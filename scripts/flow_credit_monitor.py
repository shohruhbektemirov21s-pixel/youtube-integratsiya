#!/usr/bin/env python3
"""
Flow kreditlarini doimiy kuzatuvchi.

Nima qiladi
───────────
1. Har bir Chrome profili uchun Flow'dagi HAQIQIY kredit balansini o'qiydi
   (`flow_playwright.check_profile`).
2. Natijani `FlowAIAccount` jadvaliga yozadi.
3. Gemini'dan qisqa o'zbekcha xulosa so'raydi: qaysi akkauntni ishlatish
   kerak, qancha video qolgan, nimaga e'tibor berish kerak.
4. Telegram'ga hisobot yuboradi — lekin FAQAT kerak bo'lganda:
      • kredit ogohlantirish chegarasidan pastga tushsa,
      • sessiya yo'qolsa (profil tizimdan chiqib ketgan),
      • balans o'zgargan bo'lsa,
      • yoki `--force` berilgan bo'lsa.
   Bu "har soatda bir xil xabar" shovqinining oldini oladi.

Nega Chrome'ni yopish shart emas
────────────────────────────────
Ishchi nusxa `~/.chrome-flow` da — foydalanuvchining asosiy
`~/.config/google-chrome` katalogidan alohida. Chrome profil qulfi faqat
bitta katalog doirasida ishlaydi, shuning uchun kuzatuv fonda ishlayotganda
siz Chrome'dan bemalol foydalanaversangiz bo'ladi.
(Asosiy profildan nusxani YANGILASH uchun esa Chrome yopiq bo'lishi kerak —
u alohida, kamdan-kam bajariladigan amal: `--sync`.)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
sys.path.insert(0, DIR)
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

import flow_playwright as FP  # noqa: E402

STATE_FILE = os.path.join(PROJECT_ROOT, "workspace", "logs", "flow_credit_state.json")
DEFAULT_PROFILES = ["Default", "Profile 1", "Profile 4", "Profile 17"]
CREDITS_PER_VIDEO = int(os.getenv("FLOW_CREDITS_PER_VIDEO", "15"))
LOW_THRESHOLD = int(os.getenv("FLOW_LOW_CREDIT_THRESHOLD", "150"))

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ALLOWED_CHAT_IDS = [
    x for x in os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "").replace(" ", "").split(",") if x
]
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODELS = ["models/gemini-3-flash-preview", "models/gemini-flash-lite-latest"]


# ─────────────────────────── holat ────────────────────────────
def load_state() -> Dict[str, Any]:
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(tmp, STATE_FILE)   # atomik yozuv — yarim fayl qolmaydi


# ─────────────────────────── Gemini ───────────────────────────
def gemini_summary(rows: List[Dict[str, Any]]) -> Optional[str]:
    """Gemini'dan 2-3 jumlalik o'zbekcha xulosa oladi."""
    if not GEMINI_KEY:
        return None

    facts = "\n".join(
        f"- {r['profile_dir']} ({r.get('email') or 'email nomaʼlum'}): "
        + (f"{r['credits']} kredit" if r.get("credits") is not None
           else f"O'QILMADI ({r.get('error') or 'sabab nomaʼlum'})")
        for r in rows
    )
    prompt = (
        "Sen YouTube kontent-fabrikasining operatorisan. Quyida Google Flow "
        f"akkauntlarining kredit holati. Bitta video ≈ {CREDITS_PER_VIDEO} kredit.\n\n"
        f"{facts}\n\n"
        "O'ZBEK tilida, 2-3 qisqa jumlada ayt: qaysi akkauntni keyingi "
        "generatsiyalar uchun ishlatish kerak, umumiy zaxira necha videoga "
        "yetadi, va darhol e'tibor talab qiladigan muammo bormi. "
        "Salomlashish va ortiqcha muqaddima yozma."
    )
    for model in GEMINI_MODELS:
        try:
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent",
                params={"key": GEMINI_KEY},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=25,
            )
            if resp.status_code == 200:
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            continue
    return None


# ────────────────────────── Telegram ──────────────────────────
def send_telegram(text: str) -> bool:
    if not TELEGRAM_TOKEN or not ALLOWED_CHAT_IDS:
        return False
    ok = False
    for chat_id in ALLOWED_CHAT_IDS:
        try:
            r = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                timeout=15,
            )
            ok = ok or r.ok
        except Exception:
            pass
    return ok


def build_report(rows: List[Dict[str, Any]], summary: Optional[str],
                 alerts: List[str]) -> str:
    lines = ["⚡️ <b>Flow AI kredit holati</b>",
             f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M')}</i>", ""]

    total = 0
    for r in sorted(rows, key=lambda x: -(x.get("credits") or -1)):
        if r.get("credits") is None:
            lines.append(f"❌ <b>{r['profile_dir']}</b> — o'qilmadi")
            reason = (r.get("error") or "")[:90]
            if reason:
                lines.append(f"    <i>{reason}</i>")
            continue
        total += r["credits"]
        videos = r["credits"] // CREDITS_PER_VIDEO
        icon = "🔴" if r["credits"] < LOW_THRESHOLD else "🟢"
        email = r.get("email") or ""
        lines.append(f"{icon} <b>{r['profile_dir']}</b> — {r['credits']} kredit (~{videos} video)")
        if email:
            lines.append(f"    <code>{email}</code>")

    lines += ["", f"📊 <b>Jami:</b> {total} kredit ≈ {total // CREDITS_PER_VIDEO} video"]
    if alerts:
        lines += ["", "⚠️ <b>Diqqat:</b>"] + [f"• {a}" for a in alerts]
    if summary:
        lines += ["", f"🤖 <b>Gemini:</b> {summary}"]
    return "\n".join(lines)


# ──────────────────────────── asosiy ───────────────────────────
def run(profiles: List[str], sync: Optional[bool], force: bool,
        quiet: bool) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for prof in profiles:
        print(f"[{datetime.now():%H:%M:%S}] {prof} tekshirilmoqda...", flush=True)
        r = FP.check_profile(prof, headless=False, sync=sync)
        rows.append(r)
        print(f"    kredit={r.get('credits')} email={r.get('email')} "
              f"{'xato=' + str(r.get('error'))[:70] if r.get('error') else ''}", flush=True)
        time.sleep(3)

    db = FP.sync_to_database(rows)
    if not db.get("ok"):
        print("Bazaga yozishda xato:", db.get("error", "")[:300], flush=True)

    # O'zgarish va ogohlantirishlarni aniqlash
    state = load_state()
    prev = state.get("credits", {})
    alerts: List[str] = []
    changed = False

    for r in rows:
        key = r["profile_dir"]
        cur = r.get("credits")
        old = prev.get(key)
        if cur is None:
            alerts.append(f"{key}: balans o'qilmadi — {(r.get('error') or '')[:70]}")
            changed = True
            continue
        if cur != old:
            changed = True
        if cur < LOW_THRESHOLD:
            alerts.append(f"{key}: atigi {cur} kredit (~{cur // CREDITS_PER_VIDEO} video) qoldi")
        if old is not None and cur < old:
            alerts.append(f"{key}: {old} → {cur} ({old - cur} kredit sarflandi)") if (old - cur) >= 100 else None

    alerts = [a for a in alerts if a]
    state["credits"] = {r["profile_dir"]: r.get("credits") for r in rows}
    state["checked_at"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    should_send = force or alerts or (changed and not quiet)
    report = ""
    if should_send:
        report = build_report(rows, gemini_summary(rows), alerts)
        sent = send_telegram(report)
        print(f"Telegram: {'yuborildi' if sent else 'YUBORILMADI (token/chat_id yo`q)'}", flush=True)
    else:
        print("O'zgarish yo'q — Telegram xabari yuborilmadi.", flush=True)

    return {"rows": rows, "alerts": alerts, "sent": should_send, "report": report}


def main() -> int:
    ap = argparse.ArgumentParser(description="Flow kredit kuzatuvchisi")
    ap.add_argument("--profiles", default=",".join(DEFAULT_PROFILES))
    ap.add_argument("--sync", dest="sync", action="store_true", default=None,
                    help="Asosiy Chrome profilidan nusxani yangilash (Chrome yopiq bo'lsin)")
    ap.add_argument("--no-sync", dest="sync", action="store_false")
    ap.add_argument("--force", action="store_true", help="O'zgarish bo'lmasa ham hisobot yuborish")
    ap.add_argument("--quiet", action="store_true", help="Faqat ogohlantirishda yuborish")
    args = ap.parse_args()

    os.environ.setdefault("DISPLAY", ":0.0")
    profiles = [p.strip() for p in args.profiles.split(",") if p.strip()]
    sync = args.sync if args.sync is not None else False
    res = run(profiles, sync, args.force, args.quiet)
    return 0 if any(r.get("credits") is not None for r in res["rows"]) else 1


if __name__ == "__main__":
    sys.exit(main())
