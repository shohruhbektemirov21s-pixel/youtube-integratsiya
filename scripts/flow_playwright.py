#!/usr/bin/env python3
"""
Google Flow uchun HAQIQIY Playwright driveri.

Nima uchun kerak edi
────────────────────
Eski `flow_controller.py` Flow'ni `xdotool` bilan boshqarardi: ekranning
qat'iy (1680, 952) nuqtasiga ko'r-ko'rona bosib, matn yozardi. Bu:
  • ekran o'lchami va oyna joylashuviga bog'liq edi,
  • har safar bitta HARDCODED eski loyihani ochardi (yangi sessiya emas),
  • kredit balansini UI'dan umuman o'qimasdi (qo'lda yozilgan dict qaytarardi),
  • muvaffaqiyatni tekshirishning yagona yo'li "yuklamalar papkasida yangi
    fayl paydo bo'ldimi" edi.

Bu modul Flow'ning haqiqiy DOM selektorlari bilan ishlaydi.

Chrome cheklovlari (muhim)
──────────────────────────
1. Chrome 136+ DEFAULT user-data-dir uchun CDP'ni bloklaydi
   ("DevTools remote debugging requires a non-default data directory"),
   shuning uchun profil boshqa katalogga ko'chiriladi (rsync bilan).
2. Playwright sukut bo'yicha `--use-mock-keychain` va `--password-store=basic`
   qo'shadi — bu Chrome'ning cookie shifrlash kalitiga kirishini buzadi va
   sessiya yo'qoladi. Ular `ignore_default_args` orqali olib tashlanadi va
   `--password-store=gnome` beriladi (gnome-keyring ishlab turishi shart).
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from playwright.sync_api import sync_playwright, Page

REAL_CHROME_DIR = os.path.expanduser("~/.config/google-chrome")
WORK_CHROME_DIR = os.path.expanduser("~/.chrome-flow")
FLOW_HOME = "https://flow.google.com"
DEFAULT_DISPLAY = os.getenv("DISPLAY", ":0.0")

# Flow UI selektorlari.
#
# DIQQAT: Flow interfeysi har akkauntning TILIGA moslashadi — bir profilda
# ruscha ("Сведения об аккаунте"), boshqasida o'zbekcha ("Nomsiz seans").
# Shuning uchun asosiy tayanch — Material Symbols ikonka nomlari
# (`edit_square`) va tarif nishoni ("PRO"): ular tilga bog'liq emas.
# aria-label variantlari faqat zaxira sifatida sinaladi.
SEL_ACCOUNT_BADGE_CANDIDATES = [
    # Eng barqarori: CSS klass — tilga ham, elementning turiga ham bog'liq emas.
    # (Nishon BUTTON emas, DIV: <div class="header-user-button has-tier">PRO</div>,
    #  shuning uchun `button:has-text("PRO")` hech qachon mos kelmagan.)
    ".header-user-button",
    '[aria-label="Account details"]',
    '[aria-label="Сведения об аккаунте"]',
    '[aria-label*="\u0430\u043a\u043a\u0430\u0443\u043d\u0442" i]',
    '[aria-label*="hisob" i]',
]
SEL_NEW_SESSION_CANDIDATES = [
    # Material Symbols ligaturasi — tilga bog'liq emas
    'button:has-text("edit_square")',
    '[aria-label="Start new session"]',
    '[aria-label="\u041d\u0430\u0447\u0430\u0442\u044c \u043d\u043e\u0432\u044b\u0439 \u0441\u0435\u0430\u043d\u0441"]',
    '[aria-label*="new session" i]',
    '[aria-label*="yangi seans" i]',
]
SEL_ACCOUNT_BADGE = SEL_ACCOUNT_BADGE_CANDIDATES[0]
SEL_NEW_SESSION = SEL_NEW_SESSION_CANDIDATES[0]
SEL_HOME = '[aria-label="Главная"]'

PROMPT_PLACEHOLDERS = [
    "Что вы хотите создать?",
    "What do you want to create?",
    "Nima yaratilishi kerak?",
    "Nima yaratmoqchisiz?",
]

# "1 035 бонусов Google Flow" / "1,035 credits" / "1 035 Google Flow bonusi"
CREDIT_RE = re.compile(
    r"(\d[\d\s\u00a0.,]*)\s*(?:\u0431\u043e\u043d\u0443\u0441\w*|credit\w*|\u043a\u0440\u0435\u0434\u0438\u0442\w*|bonus\w*)",
    re.IGNORECASE,
)


class FlowError(RuntimeError):
    pass


# Kredit so'zi tilga qarab o'zgaradi VA raqamdan uzoqda turishi mumkin:
#   ruscha   : "1 035 \u0431\u043e\u043d\u0443\u0441\u043e\u0432 Google Flow"  -> raqam darhol oldida
#   o'zbekcha : "960 Google Flow krediti"     -> orada 2 ta so'z
#   inglizcha : "740 Google Flow credits"     -> orada 2 ta so'z
# Shuning uchun avval kalit so'zni topamiz, keyin eng yaqin raqamni olamiz.
CREDIT_WORD_RE = re.compile(
    r"(?:\u0431\u043e\u043d\u0443\u0441\w*|\u043a\u0440\u0435\u0434\u0438\u0442\w*|credit\w*|kredit\w*|bonus\w*)",
    re.IGNORECASE,
)
NUMBER_RE = re.compile(r"\d[\d\s\u00a0.,]*\d|\d")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def parse_credits(texts: List[str]) -> Optional[int]:
    for t in texts:
        wm = CREDIT_WORD_RE.search(t)
        if not wm:
            continue
        before = t[: wm.start()]
        nums = NUMBER_RE.findall(before)
        if nums:
            digits = re.sub(r"[^\d]", "", nums[-1])
        else:
            after = NUMBER_RE.findall(t[wm.end():])
            digits = re.sub(r"[^\d]", "", after[0]) if after else ""
        if digits:
            return int(digits)
    return None


def parse_email(texts: List[str]) -> Optional[str]:
    # Avval FAQAT emaildan iborat matn (qo'shni matn yopishmasin)
    for t in texts:
        t = t.strip()
        if EMAIL_RE.fullmatch(t):
            return t
    for t in texts:
        m = EMAIL_RE.search(t)
        if m:
            return m.group(0)
    return None


def _chrome_is_running() -> bool:
    try:
        return subprocess.run(
            ["pgrep", "-f", "[/]opt/google/chrome/chrome"],
            capture_output=True, timeout=5,
        ).returncode == 0
    except Exception:
        return False


def sync_profile(profile_dir: str) -> str:
    """Haqiqiy profilni ishchi katalogga ko'chiradi (CDP cheklovi uchun)."""
    os.makedirs(WORK_CHROME_DIR, exist_ok=True)
    shutil.copy2(os.path.join(REAL_CHROME_DIR, "Local State"),
                 os.path.join(WORK_CHROME_DIR, "Local State"))

    src = os.path.join(REAL_CHROME_DIR, profile_dir)
    dst = os.path.join(WORK_CHROME_DIR, profile_dir)
    if not os.path.isdir(src):
        raise FlowError(f"Chrome profili topilmadi: {src}")

    if shutil.which("rsync"):
        subprocess.run(
            ["rsync", "-a", "--delete",
             "--exclude=Cache", "--exclude=Code Cache", "--exclude=GPUCache",
             "--exclude=Service Worker", "--exclude=Singleton*",
             src + "/", dst + "/"],
            check=False, timeout=600,
        )
    elif not os.path.isdir(dst):
        shutil.copytree(src, dst, dirs_exist_ok=True)

    for lock in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        for base in (WORK_CHROME_DIR, dst):
            try:
                os.remove(os.path.join(base, lock))
            except OSError:
                pass
    return dst


def work_copy_exists(profile_dir: str) -> bool:
    return os.path.isdir(os.path.join(WORK_CHROME_DIR, profile_dir))


@contextmanager
def flow_browser(profile_dir: str, headless: bool = False, sync: Optional[bool] = None):
    """Flow uchun tayyor brauzer konteksti.

    MUHIM: ishchi nusxa (`~/.chrome-flow`) foydalanuvchining asosiy Chrome
    katalogidan (`~/.config/google-chrome`) ALOHIDA. Chrome profil qulfi
    faqat bitta katalog doirasida ishlaydi, shuning uchun bu yerda brauzer
    ochish foydalanuvchining ochiq Chrome'iga xalaqit bermaydi va aksincha.

    Chrome yopiq bo'lishi FAQAT `sync=True` (asosiy profildan nusxa olish)
    uchun kerak: ishlab turgan Chrome'ning SQLite fayllarini ko'chirish
    buzilgan nusxa berishi mumkin.
    """
    if sync is None:
        sync = not work_copy_exists(profile_dir)

    if sync:
        deadline = time.time() + 25
        while _chrome_is_running() and time.time() < deadline:
            time.sleep(1.5)
        if _chrome_is_running():
            raise FlowError(
                "Profilni yangilash uchun Chrome yopiq bo'lishi kerak "
                "(ishchi nusxa hali yaratilmagan). Chrome'ni yoping va qayta urining."
            )
        sync_profile(profile_dir)

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=WORK_CHROME_DIR,
            channel="chrome",
            headless=headless,
            args=[
                f"--profile-directory={profile_dir}",
                "--password-store=gnome",          # haqiqiy keyring — cookie'lar ochiladi
                "--disable-blink-features=AutomationControlled",
                "--no-first-run", "--no-default-browser-check",
                "--hide-crash-restore-bubble", "--disable-session-crashed-bubble",
            ],
            ignore_default_args=[
                "--enable-automation",
                "--use-mock-keychain",             # busiz cookie shifri ochilmaydi
                "--password-store=basic",
                "--disable-extensions",
            ],
            viewport={"width": 1600, "height": 950},
            accept_downloads=True,
        )
        try:
            yield ctx
        finally:
            try:
                ctx.close()
            except Exception:
                pass


def _open_flow(ctx) -> Page:
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto(FLOW_HOME, timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(7000)
    if "/about" in page.url or "accounts.google.com" in page.url:
        raise FlowError(f"Flow sessiyasi yo'q (URL: {page.url}) — profil tizimga kirmagan.")
    return page


def ensure_in_project(page: Page) -> bool:
    """Loyiha ICHIGA kiradi.

    Kredit ko'rsatkichi ("N бонусов Google Flow") faqat loyiha ichidagi
    akkaunt panelida chiqadi — loyihalar ro'yxati sahifasida u yo'q.
    """
    if "/project/" in page.url:
        return True

    # Mavjud loyiha kartasini ochish
    for sel in ['a[href*="/project/"]', '[role="link"][href*="/project/"]']:
        try:
            link = page.locator(sel).first
            if link.is_visible(timeout=4000):
                link.click(timeout=8000)
                page.wait_for_timeout(7000)
                if "/project/" in page.url:
                    return True
        except Exception:
            continue

    # Loyiha yo'q bo'lsa — yangi sessiya ochamiz
    for sel in SEL_NEW_SESSION_CANDIDATES:
        try:
            page.click(sel, timeout=5000)
            page.wait_for_timeout(6000)
            break
        except Exception:
            continue
    return "/project/" in page.url


def open_account_panel(page: Page) -> List[str]:
    """Akkaunt panelini ochadi va undagi qisqa matnlarni qaytaradi (diagnostika)."""
    for attempt, sel in enumerate(SEL_ACCOUNT_BADGE_CANDIDATES):
        try:
            page.click(sel, timeout=8000)
            page.wait_for_timeout(2500 + attempt * 1000)
            break
        except Exception:
            continue
    return page.evaluate(
        """() => {const s=new Set();
           document.querySelectorAll('div,span,p,li,button,a').forEach(e=>{
             if(e.children.length>2)return;
             const t=(e.innerText||'').trim();
             if(t && t.length<=80) s.add(t);});
           return [...s];}"""
    )


def read_credits(page: Page, timeout_ms: int = 12000) -> Optional[int]:
    """Kredit balansini akkaunt panelidan o'qiydi.

    Nega bu shunchalik ehtiyotkor
    ─────────────────────────────
    Birinchi versiya sahifadagi BARCHA qisqa matnlarni skanerlab, "credit"
    so'zi uchragan birinchi raqamni olardi. Flow'da model narxi yorliqlari
    ham bor ("Veo — 15 credits"), shuning uchun bitta profil uchun 15, 740
    va None kabi bir-biriga zid natijalar chiqardi. Bazaga taxminiy raqam
    yozish — tizim yolg'on gapirishining aynan o'sha turi.

    Shuning uchun endi:
      • panel ochilishi majburiy (`.header-user-button` — CSS klass tilga
        va element turiga bog'liq emas; nishon BUTTON emas, DIV),
      • raqam panel ochilgandan KEYINGI matndan olinadi,
      • "Google Flow" so'zi bor qator afzal ko'riladi (narx yorlig'ida u yo'q),
      • topilmasa — None qaytariladi, taxmin qilinmaydi.
    """
    for sel in SEL_ACCOUNT_BADGE_CANDIDATES:
        try:
            page.click(sel, timeout=6000)
        except Exception:
            continue

        page.wait_for_timeout(min(timeout_ms, 5000))
        body = page.evaluate("() => document.body.innerText || ''")
        lines = [ln.strip() for ln in body.splitlines() if ln.strip()]

        hits = [ln for ln in lines if CREDIT_WORD_RE.search(ln) and any(c.isdigit() for c in ln)]
        if not hits:
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
            except Exception:
                pass
            continue

        # "740 Google Flow credits" — balans; "Veo — 15 credits" — narx yorlig'i
        preferred = [ln for ln in hits if "flow" in ln.lower()] or hits
        value = parse_credits(preferred)
        # Panelni albatta yopamiz — ochiq qolsa keyingi bosishlarni
        # (masalan "Yangi sessiya" tugmasini) to'sib qo'yadi.
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
        except Exception:
            pass
        if value is not None:
            return value
    return None


def check_profile(profile_dir: str, headless: bool = False,
                  sync: Optional[bool] = None) -> Dict[str, Any]:
    """Bitta profil uchun: login holati, email va haqiqiy kredit balansi."""
    out: Dict[str, Any] = {
        "profile_dir": profile_dir, "logged_in": False,
        "email": None, "credits": None, "plan": None, "error": None,
    }
    try:
        with flow_browser(profile_dir, headless=headless, sync=sync) as ctx:
            page = _open_flow(ctx)
            out["logged_in"] = True
            if re.search(r"\bPRO\b", page.evaluate("() => document.body.innerText || ''")):
                out["plan"] = "PRO"

            ensure_in_project(page)
            out["credits"] = read_credits(page)
            if out["credits"] is None:
                page.wait_for_timeout(4000)
                out["credits"] = read_credits(page)

            texts = page.evaluate(
                """() => {const s=new Set();
                   document.querySelectorAll('div,span,p,li,button,a').forEach(e=>{
                     if(e.children.length>2)return;
                     const t=(e.innerText||'').trim();
                     if(t && t.length<=80) s.add(t);});
                   return [...s];}"""
            )
            out["email"] = parse_email(texts)
            if out["credits"] is None:
                # Diagnostika: nima ko'rinayotganini saqlaymiz
                out["debug_texts"] = [t for t in texts if any(c.isdigit() for c in t)][:12]
    except Exception as exc:
        out["error"] = str(exc)[:300]
    return out


def start_new_session(page: Page) -> bool:
    """YANGI sessiya (chat) ochadi — eski loyihaga yozishning o'rniga."""
    for sel in SEL_NEW_SESSION_CANDIDATES:
        try:
            page.click(sel, timeout=8000)
            page.wait_for_timeout(3500)
            return True
        except Exception:
            continue
    return False


def submit_prompt(page: Page, prompt: str) -> bool:
    """Promptni haqiqiy input maydoniga yozadi (koordinata bo'yicha bosish emas)."""
    for ph in PROMPT_PLACEHOLDERS:
        try:
            box = page.get_by_placeholder(ph).first
            if box.is_visible(timeout=3000):
                box.click()
                box.fill(prompt)
                page.wait_for_timeout(500)
                box.press("Enter")
                return True
        except Exception:
            continue
    # Zaxira: sahifadagi birinchi textarea / contenteditable
    for sel in ["textarea", "[contenteditable='true']"]:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=3000):
                el.click()
                el.fill(prompt)
                el.press("Enter")
                return True
        except Exception:
            continue
    return False


def sync_to_database(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Haqiqiy kredit balanslarini `FlowAIAccount` jadvaliga yozadi.

    Ilgari bazadagi kreditlar faqat "har generatsiyada -10" hisobidan kelib
    chiqardi va Flow'dagi haqiqiy balans bilan hech qachon solishtirilmasdi.
    """
    import base64
    import json as _json

    payload = base64.b64encode(_json.dumps(results).encode()).decode()
    code = f'''
import base64, json
from django.utils import timezone
from apps.youtube.models import FlowAIAccount

rows = json.loads(base64.b64decode("{payload}").decode())
report = []
for r in rows:
    if not r.get("logged_in") or r.get("credits") is None:
        report.append({{"profile": r["profile_dir"], "action": "skipped",
                        "reason": r.get("error") or "kredit o'qilmadi"}})
        continue

    acc = FlowAIAccount.objects.filter(profile_dir=r["profile_dir"]).first()
    if acc is None:
        acc = FlowAIAccount(
            name=(r.get("email") or r["profile_dir"]),
            profile_dir=r["profile_dir"],
            initial_credits=r["credits"],
        )
        action = "created"
    else:
        action = "updated"

    old = acc.credits_remaining
    acc.credits_remaining = r["credits"]
    if r.get("email") and hasattr(acc, "email"):
        acc.email = r["email"]
    if acc.initial_credits < r["credits"]:
        acc.initial_credits = r["credits"]
    acc.has_flow_credits = r["credits"] > 0
    acc.is_active = r["credits"] > 0
    acc.inspection_status = "verified"
    acc.last_inspected_at = timezone.now()
    acc.save()
    report.append({{"profile": r["profile_dir"], "action": action,
                    "old": old, "new": r["credits"], "email": r.get("email")}})

print("SYNC_RESULT:" + json.dumps(report))
'''
    proc = subprocess.run(
        ["docker", "exec", "-i", "youtube_integratsiya_backend",
         "python", "manage.py", "shell", "-c", code],
        capture_output=True, text=True, timeout=120,
        env={**os.environ, "DOCKER_HOST": "unix:///var/run/docker.sock"},
    )
    if proc.returncode != 0:
        return {"ok": False, "error": (proc.stderr or "")[-800:]}
    for line in proc.stdout.splitlines():
        if line.startswith("SYNC_RESULT:"):
            import json as _j
            return {"ok": True, "report": _j.loads(line[len("SYNC_RESULT:"):])}
    return {"ok": False, "error": "SYNC_RESULT topilmadi", "stdout": proc.stdout[-500:]}


# ─────────────────────────────────────────────────────────────────────────
# Video generatsiyasi — jonli sinov orqali tasdiqlangan oqim (2026-09-23):
#   1. Yangi sessiya ochiladi ("Начать новый сеанс" — eski loyihaga
#      yozish o'rniga, ilgari xdotool shu sababdan doim eski Sep-20
#      loyihasini ochardi).
#   2. Prompt input maydoniga yoziladi va Enter bosiladi.
#   3. Flow tasdiqlash so'raydi: "Сгенерировать 1 видео за бонусы (N)?" —
#      "Всегда одобрять" tugmasi bosiladi (keyingi safarlar uchun ham
#      saqlanadi, shuning uchun bu qadam keyingi chaqiruvlarda tez o'tadi).
#   4. Generatsiya progress foizi bilan ko'rinadi (0% -> 12% -> 22% ...),
#      lekin "high demand" bo'lsa "navbatda kutish" holatiga tushishi va
#      NOANIQ vaqt (bir necha daqiqadan ortiq) davom etishi mumkin —
#      shuning uchun POLL_TIMEOUT katta va konfiguratsiya qilinadigan.
#   5. Tayyor bo'lgach video karta menyusidan ("Дополнительные параметры"
#      -> "Скачать" -> "Исходный размер") yuklab olinadi. 1080p/4K ni
#      TANLAMANG — ular alohida "sifat oshirish" (upscale) jarayonini
#      boshlaydi va yana kutish talab qiladi; "Исходный размер" darhol
#      tayyor faylni beradi.
#   6. "Опубликовать на YouTube" tugmasi ham bor (Flow'ning o'z YouTube
#      integratsiyasi, OAuth kerak emas) — LEKIN bu ATAYLAB CHAQIRILMAYDI:
#      qaytarib bo'lmaydigan ommaviy nashr xavfi bor. Yuklab olingan fayl
#      loyihaning o'z QA/subtitr/branding pipeline'idan o'tadi, YouTube'ga
#      chiqish esa mavjud tasdiqlash oqimi (confirm_upload) orqali bo'ladi.
# ─────────────────────────────────────────────────────────────────────────

GENERATION_APPROVE_CANDIDATES = [
    "Всегда одобрять", "Always allow", "Har doim tasdiqla",
    "Одобрить", "Approve", "Tasdiqla",
]
DOWNLOAD_TRIGGER_CANDIDATES = ["Скачать", "Download", "Yuklab olish"]
DOWNLOAD_ORIGINAL_CANDIDATES = ["Исходный размер", "Original size", "Original o'lcham", "Original"]
MORE_OPTIONS_LABEL = "Дополнительные параметры"


def _click_first_visible(page: Page, texts: List[str], timeout_ms: int = 4000) -> bool:
    for t in texts:
        try:
            el = page.get_by_text(t, exact=True).first
            if el.is_visible(timeout=timeout_ms):
                el.click(timeout=timeout_ms)
                return True
        except Exception:
            continue
    return False


def approve_generation_if_asked(page: Page) -> bool:
    """Kredit sarflash tasdiqlash so'rovi chiqsa, uni bosadi."""
    page.wait_for_timeout(1500)
    return _click_first_visible(page, GENERATION_APPROVE_CANDIDATES, timeout_ms=3000)


def _latest_media_card_menu(page: Page):
    """Chatdagi ENG SO'NGGI media kartaning 'Дополнительные параметры' tugmasini qaytaradi.

    Sahifada bu aria-label bilan bir nechta tugma bor: birinchisi (index 0)
    doim sahifa header'idagi umumiy menyu, index>=1 esa chatdagi har bir
    media javobiga tegishli. Eng oxirgisi — eng yangi video.
    """
    thumbs = page.locator("main").locator("img")
    if thumbs.count() == 0:
        return None
    thumb = thumbs.last
    box = thumb.bounding_box()
    if not box:
        return None
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_timeout(500)
    locs = page.locator(f'main [aria-label="{MORE_OPTIONS_LABEL}"]')
    n = locs.count()
    if n < 2:
        return None
    return locs.nth(n - 1)


def wait_for_video_ready(page: Page, timeout_s: int = 1800, poll_s: int = 15):
    """Video tayyorligini POLL qiladi.

    Google Flow "high demand" bo'lsa videoni navbatga qo'yadi va aniq
    tugash vaqtini bermaydi ("check back in a few minutes" — amalda bir
    necha daqiqadan o'nlab daqiqagacha bo'lishi mumkin). Shuning uchun
    progress foizini kutish o'rniga, oddiygina davriy ravishda "Скачать"
    submenyusi ichida "Исходный размер" ko'rinishini tekshiramiz — bu
    fayl haqiqatan tayyor bo'lgandagina paydo bo'ladi.
    """
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        menu = _latest_media_card_menu(page)
        if menu is not None:
            try:
                menu.click(timeout=4000, force=True)
                page.wait_for_timeout(800)
                dl = page.get_by_text(DOWNLOAD_TRIGGER_CANDIDATES[0], exact=True).first
                if dl.is_visible(timeout=2000):
                    dl.hover(timeout=3000)
                    page.wait_for_timeout(800)
                    for cand in DOWNLOAD_ORIGINAL_CANDIDATES:
                        if page.get_by_text(cand, exact=True).first.is_visible(timeout=1500):
                            page.keyboard.press("Escape")
                            return True
                page.keyboard.press("Escape")
            except Exception:
                try:
                    page.keyboard.press("Escape")
                except Exception:
                    pass
        page.wait_for_timeout(poll_s * 1000)
    return False


def download_latest_video(page: Page, dest_path: str, timeout_ms: int = 30000) -> bool:
    """Eng so'nggi videoni ASL o'lchamda (upscale'siz) yuklab, dest_path ga saqlaydi."""
    menu = _latest_media_card_menu(page)
    if menu is None:
        return False
    menu.click(timeout=5000, force=True)
    page.wait_for_timeout(800)
    page.get_by_text(DOWNLOAD_TRIGGER_CANDIDATES[0], exact=True).first.hover(timeout=5000)
    page.wait_for_timeout(1000)

    for cand in DOWNLOAD_ORIGINAL_CANDIDATES:
        try:
            with page.expect_download(timeout=timeout_ms) as dl_info:
                page.get_by_text(cand, exact=True).first.click(timeout=5000)
            download = dl_info.value
            download.save_as(dest_path)
            return True
        except Exception:
            continue
    return False


def generate_video(profile_dir: str, prompt: str, dest_path: str,
                    headless: bool = False, sync: Optional[bool] = None,
                    poll_timeout_s: int = 1800) -> Dict[str, Any]:
    """To'liq zanjir: yangi sessiya -> prompt -> tasdiqlash -> kutish -> yuklash.

    Qaytaradi: {"success": bool, "video_path": str|None, "credits_before": int|None,
                "credits_after": int|None, "error": str|None}
    """
    out: Dict[str, Any] = {
        "success": False, "video_path": None,
        "credits_before": None, "credits_after": None, "error": None,
    }
    try:
        with flow_browser(profile_dir, headless=headless, sync=sync) as ctx:
            page = _open_flow(ctx)
            ensure_in_project(page)

            out["credits_before"] = read_credits(page)

            if not start_new_session(page):
                out["error"] = "Yangi sessiya ochilmadi"
                return out

            if not submit_prompt(page, prompt):
                out["error"] = "Prompt yuborilmadi (input maydoni topilmadi)"
                return out

            approve_generation_if_asked(page)

            ready = wait_for_video_ready(page, timeout_s=poll_timeout_s)
            if not ready:
                out["error"] = (
                    f"Video {poll_timeout_s}s ichida tayyor bo'lmadi "
                    "(Flow 'high demand' navbatida bo'lishi mumkin)."
                )
                return out

            if not download_latest_video(page, dest_path):
                out["error"] = "Video tayyor, lekin yuklab olinmadi"
                return out

            out["success"] = True
            out["video_path"] = dest_path
            out["credits_after"] = read_credits(page)
            return out
    except Exception as exc:
        out["error"] = str(exc)[:400]
        return out


if __name__ == "__main__":
    import argparse, json

    ap = argparse.ArgumentParser(description="Google Flow Playwright driveri")
    ap.add_argument("action", choices=["check", "check-all", "sync-db", "generate"])
    ap.add_argument("--profile", default="Profile 17")
    ap.add_argument("--profiles", default="Default,Profile 1,Profile 4,Profile 17")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--sync", dest="sync", action="store_true", default=None,
                    help="Asosiy Chrome profilidan nusxani yangilash (Chrome yopiq bo'lsin)")
    ap.add_argument("--no-sync", dest="sync", action="store_false",
                    help="Mavjud ishchi nusxa bilan ishlash (Chrome ochiq bo'lsa ham)")
    ap.add_argument("--prompt", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--poll-timeout", type=int, default=1800)
    args = ap.parse_args()

    os.environ.setdefault("DISPLAY", DEFAULT_DISPLAY)

    if args.action == "check":
        print(json.dumps(check_profile(args.profile, args.headless, args.sync),
                         indent=2, ensure_ascii=False))
    elif args.action == "generate":
        if not args.prompt or not args.out:
            print("--prompt va --out majburiy"); raise SystemExit(2)
        res = generate_video(args.profile, args.prompt, args.out,
                             headless=args.headless, sync=args.sync,
                             poll_timeout_s=args.poll_timeout)
        print(json.dumps(res, indent=2, ensure_ascii=False))
        raise SystemExit(0 if res["success"] else 1)
    else:
        results = []
        for prof in [p.strip() for p in args.profiles.split(",") if p.strip()]:
            print(f"\n{'='*60}\n  {prof} tekshirilmoqda...\n{'='*60}", flush=True)
            r = check_profile(prof, args.headless, args.sync)
            time.sleep(4)
            results.append(r)
            status = "OK" if r["logged_in"] else "KIRMAGAN"
            print(f"  {status} | email={r['email']} | kredit={r['credits']} | {r['plan'] or ''}"
                  + (f" | {r['error']}" if r["error"] else ""), flush=True)
        if args.action == "sync-db":
            print("\n=== Bazaga yozilmoqda ===", flush=True)
            out = sync_to_database(results)
            if out.get("ok"):
                for row in out["report"]:
                    if row["action"] == "skipped":
                        print(f"  - {row['profile']}: o'tkazib yuborildi ({row['reason']})")
                    else:
                        print(f"  + {row['profile']}: {row['old']} -> {row['new']} "
                              f"({row['action']}, {row.get('email')})")
            else:
                print("  XATO:", out.get("error"))
        else:
            print("\n" + json.dumps(results, indent=2, ensure_ascii=False))
