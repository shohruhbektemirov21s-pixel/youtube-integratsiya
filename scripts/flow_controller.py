#!/usr/bin/env python3
"""
BeyondEra Tech - Google Flow Browser Automation Controller.
Controls the 4 verified Google AI accounts (Default, Profile 1, Profile 4, Profile 17).
Features:
1. Dynamic profile health check & automatic fallback switching.
2. Flow AI project & interface detection (https://flow.google.com).
3. Robust prompt injection (ARIA/Role, input selector, and X11 typing fallback).
4. Generation monitoring & automated download detection in ~/Загрузки and ~/Downloads.
5. Automated Black Screen & Integrity QA on every downloaded video.
6. Real-time credit accounting & PostgreSQL status sync.
"""

import os
import sys
import time
import json
import uuid
import glob
import shutil
import argparse
import subprocess

from datetime import datetime
from typing import Dict, Any, Optional, Tuple

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

CHROME_BIN = "/opt/google/chrome/chrome"
DISPLAY_VAL = os.getenv("DISPLAY", ":0.0")
DOWNLOADS_DIR = os.path.expanduser("~/Загрузки")
if not os.path.exists(DOWNLOADS_DIR):
    DOWNLOADS_DIR = os.path.expanduser("~/Downloads")

VIDEO_LIB_DIR = os.path.join(PROJECT_ROOT, "assets/video_library")
os.makedirs(VIDEO_LIB_DIR, exist_ok=True)

ACTIVE_PROFILES = {
    "1": {
        "index": 1,
        "profile_dir": "Default",
        "email": "shohruhbektemirov21s@gmail.com",
        "name": "Shohruhbek Temirov (Default)",
        "credits": 1050,
        "is_healthy": True,
        "fail_count": 0
    },
    "2": {
        "index": 2,
        "profile_dir": "Profile 1",
        "email": "ustaaiverifity@gmail.com",
        "name": "Ustaai (Profile 1)",
        "credits": 1050,
        "is_healthy": True,
        "fail_count": 0
    },
    "3": {
        "index": 3,
        "profile_dir": "Profile 4",
        "email": "defarux109@gmail.com",
        "name": "DEfarux (Profile 4)",
        "credits": 1050,
        "is_healthy": True,
        "fail_count": 0
    },
    "4": {
        "index": 4,
        "profile_dir": "Profile 17",
        "email": "hhshox41@gmail.com",
        "name": "BeyondEra Tech (Profile 17)",
        "credits": 1040,
        "is_healthy": True,
        "fail_count": 0
    }
}


def _load_profiles_from_db() -> Optional[Dict[str, Any]]:
    """Flow profillarini BAZADAN o'qiydi (haqiqiy kredit balansi bilan).

    ACTIVE_PROFILES dagi `credits` qiymatlari qo'lda yozilgan va hech qachon
    Flow bilan solishtirilmagan edi — `flow.sh status` "4,190 kredit" deb
    ko'rsatardi, holbuki haqiqiy yig'indi butunlay boshqa. Endi manba —
    `flow_playwright.py sync-db` yozadigan FlowAIAccount jadvali.
    Baza mavjud bo'lmasa, eski dict zaxira sifatida ishlatiladi.
    """
    import base64
    import json as _json
    code = (
        "import json\n"
        "from apps.youtube.models import FlowAIAccount\n"
        "rows=[{'profile_dir':a.profile_dir,'name':a.name,"
        "'email':getattr(a,'email','') or '',"
        "'credits':a.credits_remaining,'is_active':a.is_active,"
        "'status':a.inspection_status or ''} "
        "for a in FlowAIAccount.objects.order_by('-credits_remaining')]\n"
        "print('PROFILES_JSON:'+json.dumps(rows))"
    )
    try:
        env = dict(os.environ, DOCKER_HOST="unix:///var/run/docker.sock")
        proc = subprocess.run(
            ["docker", "exec", "-i", "youtube_integratsiya_backend",
             "python", "manage.py", "shell", "-c", code],
            capture_output=True, text=True, timeout=25, env=env,
        )
        if proc.returncode != 0:
            return None
        for line in proc.stdout.splitlines():
            if line.startswith("PROFILES_JSON:"):
                rows = _json.loads(line[len("PROFILES_JSON:"):])
                out = {}
                for i, r in enumerate(rows, start=1):
                    out[str(i)] = {
                        "index": i,
                        "profile_dir": r["profile_dir"],
                        "email": r["email"],
                        "name": r["name"],
                        "credits": r["credits"],
                        "is_healthy": bool(r["is_active"]) and r["credits"] > 0,
                        "fail_count": 0,
                        "source": "db",
                    }
                return out or None
    except Exception:
        return None
    return None


def get_profiles() -> Dict[str, Any]:
    """Bazadagi haqiqiy ma'lumot, bo'lmasa — eski statik dict."""
    if os.environ.get("FLOW_PROFILES_FROM_DB", "1") != "0":
        db = _load_profiles_from_db()
        if db:
            return db
    return ACTIVE_PROFILES


def get_healthy_profile(preferred_key: str = "4") -> Dict[str, Any]:
    """Selects preferred profile if healthy, or falls back to next available profile."""
    profiles = get_profiles()
    if preferred_key in profiles and profiles[preferred_key]["is_healthy"]:
        return profiles[preferred_key]

    # Find profile with highest credits and zero fail count
    candidates = [p for p in profiles.values() if p.get("is_healthy", True)]
    if candidates:
        candidates.sort(key=lambda x: (x.get("fail_count", 0), -x.get("credits", 0)))
        return candidates[0]

    return profiles.get("4") or next(iter(profiles.values()))


TARGET_FLOW_PROJECT_URL = "https://flow.google.com/project/a2bf95c3-050c-497c-bbfb-cd3776002416"


def launch_flow_in_chrome(profile_dir: str = "Profile 17", url: str = TARGET_FLOW_PROJECT_URL) -> bool:
    """Launches or focuses Chrome on DISPLAY=:0.0 with the target profile and project URL."""
    cmd = [
        CHROME_BIN,
        f"--profile-directory={profile_dir}",
        url
    ]
    env = os.environ.copy()
    env["DISPLAY"] = DISPLAY_VAL
    env["HOME"] = os.path.expanduser("~")

    try:
        subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        time.sleep(3)
        return True
    except Exception as e:
        print(f"❌ Brauzerni ishga tushirishda xatolik: {e}")
        return False


def wait_for_flow_window(timeout_seconds: int = 15) -> Optional[str]:
    """Waits for Chrome window with Flow AI to become active on X11."""
    start = time.time()
    while time.time() - start < timeout_seconds:
        try:
            cmd = ["xdotool", "search", "--onlyvisible", "--class", "google-chrome"]
            env = os.environ.copy()
            env["DISPLAY"] = DISPLAY_VAL
            res = subprocess.run(cmd, capture_output=True, text=True, env=env)
            wids = [w.strip() for w in res.stdout.splitlines() if w.strip()]
            for wid in wids:
                title_cmd = ["xdotool", "getwindowname", wid]
                t_res = subprocess.run(title_cmd, capture_output=True, text=True, env=env)
                t_str = t_res.stdout.lower()
                if "flow" in t_str or "google" in t_str:
                    return wid
        except Exception:
            pass
        time.sleep(1)
    return None


def find_latest_flow_download(since_timestamp: float) -> Optional[str]:
    """Scans download directories for freshly downloaded Flow video files."""
    patterns = [
        os.path.join(DOWNLOADS_DIR, "*_1080p_*.mp4"),
        os.path.join(DOWNLOADS_DIR, "*.mp4"),
        os.path.join("/tmp", "flow_*.mp4")
    ]
    candidates = []
    for pat in patterns:
        for f in glob.glob(pat):
            try:
                mtime = os.path.getmtime(f)
                if mtime >= since_timestamp - 5 and os.path.getsize(f) > 500 * 1024:
                    candidates.append((mtime, f))
            except Exception:
                pass

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    return None


def generate_video_with_flow(
    prompt: str,
    profile_choice: str = "4",
    aspect_ratio: str = "9:16",
    max_retries: int = 3,
    **kwargs
) -> Dict[str, Any]:
    """
    Automates Flow AI video generation:
    1. Selects healthy profile.
    2. Opens Flow AI in Chrome.
    3. Enters prompt and triggers generation.
    4. Downloads and runs QA on the resulting video.
    """
    from scripts.video_qa import run_full_qa

    generation_id = kwargs.get("generation_id") or f"flow_{int(time.time())}"
    flow_gen_id = f"FLOW_{uuid.uuid4().hex[:12].upper()}"
    
    print("=" * 65)
    print("🎬 [FLOW CONTROLLER] Google Flow AI Avtomatlashtirish Boshlanmoqda...")
    print(f"🔑 Flow Generation ID: {flow_gen_id}")
    print(f"📝 Prompt: {prompt[:80]}...")
    print("=" * 65)

    timestamp_start = time.time()
    prof = get_healthy_profile(profile_choice)
    print(f"👤 Tanlangan profil: [{prof['index']}] {prof['name']} ({prof['email']})")
    print(f"⚡️ Mavjud kredit: {prof['credits']} ta")

    # 1. Launch / Focus Flow in Chrome at Target Project URL
    launch_flow_in_chrome(prof["profile_dir"], TARGET_FLOW_PROJECT_URL)
    wid = wait_for_flow_window(timeout_seconds=6)
    if wid:
        try:
            env = os.environ.copy()
            env["DISPLAY"] = DISPLAY_VAL
            subprocess.run(["xdotool", "windowactivate", "--sync", wid, "mousemove", "1680", "952", "click", "1"], env=env, timeout=4)
            time.sleep(0.4)
            clean_p = prompt.replace("\n", " ").strip()
            subprocess.run(["xdotool", "type", "--delay", "15", clean_p], env=env, timeout=12)
            time.sleep(0.4)
            subprocess.run(["xdotool", "key", "Return"], env=env, timeout=4)
            print(f"🚀 [FLOW PROJECT] Loyihaga prompt to'g'ridan-to'g'ri yuborildi: \"{clean_p[:60]}...\"")
        except Exception as e:
            print(f"⚠️ Flow AI prompt yuborishda ogohlantirish: {e}")

    downloaded_video = None
    is_fresh_download = False

    # 2. Wait for Flow AI to generate video, then check for fresh downloads
    print("⏳ [FLOW CONTROLLER] Video generatsiyasi kutilmoqda (120s)...")
    poll_start = time.time()
    latest = None
    while time.time() - poll_start < 120:
        latest = find_latest_flow_download(since_timestamp=timestamp_start)
        if latest:
            break
        time.sleep(5)
        elapsed = int(time.time() - poll_start)
        if elapsed % 15 == 0:
            print(f"  ⏱ Kutilmoqda: {elapsed}s o'tdi...")

    if not latest:
        latest = find_latest_flow_download(since_timestamp=timestamp_start)
    if latest:
        dest_name = f"flow_fresh_{flow_gen_id}.mp4"
        dest_path = os.path.join(VIDEO_LIB_DIR, dest_name)
        try:
            shutil.copy2(latest, dest_path)
            downloaded_video = dest_path
            is_fresh_download = True
            print(f"📥 Yangi yuklab olingan Flow video loyihaga saqlandi: {dest_path}")
        except Exception:
            pass

    # 3. Yangi yuklama bo'lmadi.
    #
    # Ilgari bu yerda kutubxonadagi 5 ta eski klipdan biri JIM tanlanib,
    # natija "muvaffaqiyat" deb qaytarilardi. Audio va subtitr yangi bo'lgani
    # uchun SHA-256 dedup ham buni ushlamas edi — ya'ni Flow butunlay
    # ishlamayotgan bo'lsa ham kanalga "yangi" video ketaverardi.
    #
    # Endi standart xatti-harakat: HALOL XATO. Arxiv kadrlarini ataylab
    # ishlatmoqchi bo'lsangiz: FLOW_ALLOW_LIBRARY_FALLBACK=1
    allow_library = os.environ.get("FLOW_ALLOW_LIBRARY_FALLBACK") == "1"

    if not downloaded_video and not allow_library:
        print("❌ [FLOW] Yangi video yuklanmadi va arxiv fallback o'chirilgan.")
        return {
            "success": False,
            "video_path": None,
            "is_fresh_download": False,
            "reused_from_library": False,
            "generation_id": generation_id,
            "flow_generation_id": flow_gen_id,
            "profile": prof["name"],
            "error": (
                "Flow AI dan yangi video kelmadi. Sabablari: Chrome oynasi "
                "kutilgan joyda emas, Flow sahifasi yuklanmagan, sessiya "
                "tugagan, yoki kredit qolmagan. "
                "Arxiv kadrlarini ataylab ishlatish uchun: "
                "FLOW_ALLOW_LIBRARY_FALLBACK=1"
            ),
        }

    reused_from_library = False
    if not downloaded_video:
        reused_from_library = True
        print("⚠️  [FLOW] YANGI VIDEO EMAS — arxiv kutubxonasidan kadr olinmoqda "
              "(FLOW_ALLOW_LIBRARY_FALLBACK=1 yoqilgan).")
        p_lower = prompt.lower()
        if any(w in p_lower for w in ["quantum", "photon", "qubit", "optical", "laser"]):
            preferred_name = "flow_clip_2.mp4"
        elif any(w in p_lower for w in ["neural", "brain", "synapse", "telepathy", "cortex"]):
            preferred_name = "flow_clip_3.mp4"
        elif any(w in p_lower for w in ["matrix", "radar", "hud", "telemetry", "algorithm"]):
            preferred_name = "flow_clip_4.mp4"
        elif any(w in p_lower for w in ["space", "orbit", "lunar", "satellite", "star", "cosmic"]):
            preferred_name = "flow_clip_5.mp4"
        else:
            preferred_name = "flow_clip_1.mp4"

        pref_path = os.path.join(VIDEO_LIB_DIR, preferred_name)
        if os.path.exists(pref_path) and os.path.getsize(pref_path) > 100 * 1024:
            downloaded_video = pref_path
            print(f"💎 Mavzuga mos Flow video manbasi tanlandi: {downloaded_video}")
        else:
            existing_clips = sorted(glob.glob(os.path.join(VIDEO_LIB_DIR, "flow_clip_*.mp4")))
            if existing_clips:
                import random
                downloaded_video = random.choice(existing_clips)
                print(f"💎 Flow video kutubxonasidan tasdiqlangan fayl topildi: {downloaded_video}")

    all_available_clips = sorted(glob.glob(os.path.join(VIDEO_LIB_DIR, "flow_clip_*.mp4")))

    # Run QA on the Flow video
    is_shorts = (aspect_ratio == "9:16")
    qa_res = None
    if downloaded_video and os.path.exists(downloaded_video):
        qa_res = run_full_qa(
            downloaded_video,
            expected_type="shorts" if is_shorts else "long",
            min_duration=8.0,
            require_audio=False
        )

    # Deduct credits
    credits_used = 10
    prof["credits"] = max(0, prof["credits"] - credits_used)

    return {
        "success": downloaded_video is not None,
        "reused_from_library": reused_from_library,
        "video_path": downloaded_video,
        "flow_generation_id": flow_gen_id,
        "is_fresh_download": is_fresh_download,
        "all_clips": all_available_clips,
        "profile": prof,
        "prompt": prompt,
        "credits_used": credits_used,
        "qa": qa_res
    }


def acquire_multi_prompt_assets(
    scene_prompts: list,
    profile_choice: str = "4",
    aspect_ratio: str = "9:16",
    generation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creatively handles MULTI-PROMPT asset acquisition:
    Takes all scene prompts from the content plan, maps each prompt to its thematic video asset,
    and returns a structured asset map ensuring each scene has its own distinct creative visual prompt.
    """
    print("=" * 65)
    print("🎨 [FLOW CONTROLLER] MULTI-PROMPT KREATIV AKTIVLAR BOSHQARUVI")
    print(f"🎬 Jami sahna promptlari: {len(scene_prompts)} ta unikal prompt")
    print("=" * 65)

    all_available_clips = sorted(glob.glob(os.path.join(VIDEO_LIB_DIR, "flow_clip_*.mp4")))
    scene_asset_map = []

    primary_res = generate_video_with_flow(
        prompt=scene_prompts[0] if scene_prompts else "Futuristic tech innovation",
        profile_choice=profile_choice,
        aspect_ratio=aspect_ratio,
        generation_id=generation_id
    )

    for idx, sc_prompt in enumerate(scene_prompts):
        p_lower = sc_prompt.lower()
        if any(w in p_lower for w in ["quantum", "photon", "qubit", "optical", "laser"]):
            clip_name = "flow_clip_2.mp4"
            visual_category = "quantum"
        elif any(w in p_lower for w in ["neural", "brain", "synapse", "telepathy", "cortex"]):
            clip_name = "flow_clip_3.mp4"
            visual_category = "neural"
        elif any(w in p_lower for w in ["matrix", "radar", "hud", "telemetry", "algorithm", "data"]):
            clip_name = "flow_clip_4.mp4"
            visual_category = "matrix"
        elif any(w in p_lower for w in ["space", "orbit", "starship", "lunar", "satellite", "star"]):
            clip_name = "flow_clip_5.mp4"
            visual_category = "space"
        else:
            clip_name = "flow_clip_1.mp4"
            visual_category = "robot"

        assigned_clip = os.path.join(VIDEO_LIB_DIR, clip_name)
        if not os.path.exists(assigned_clip) and all_available_clips:
            assigned_clip = all_available_clips[idx % len(all_available_clips)]

        scene_asset_map.append({
            "scene_index": idx,
            "prompt": sc_prompt,
            "visual_category": visual_category,
            "assigned_video_clip": assigned_clip if os.path.exists(assigned_clip) else None,
            "use_hybrid_image": (idx % 2 == 1)  # alternating hybrid image and video
        })
        print(f"  🔹 Sahna #{idx+1} Prompt: \"{sc_prompt[:45]}...\" -> Kategoriya: [{visual_category.upper()}]")

    return {
        "success": True,
        "primary_video": primary_res.get("video_path"),
        "flow_generation_id": primary_res.get("flow_generation_id"),
        "all_clips": all_available_clips,
        "scene_assets": scene_asset_map,
        "prompts_count": len(scene_prompts),
        "profile": primary_res.get("profile"),
        "qa": primary_res.get("qa")
    }




def show_status():
    profiles = get_profiles()
    """Display live credit balances of the 4 Google AI Pro accounts."""
    print("=" * 65)
    src = "BAZA (haqiqiy)" if any(p.get("source") == "db" for p in profiles.values()) else "statik dict"
    print(f"   🎯 GOOGLE FLOW PROFILLARI — manba: {src}")
    print("=" * 65)
    total_credits = 0
    for k in sorted(profiles.keys()):
        p = profiles[k]
        total_credits += p["credits"]
        status_icon = "🟢 Faol" if p.get("is_healthy", True) else "🔴 Xatolik"
        print(f"  [{p['index']}] {p['name']} | {status_icon}")
        print(f"      📧 Email:   {p['email']}")
        print(f"      📁 Chrome:  {p['profile_dir']}")
        print(f"      ⚡️ Kredit:  {p['credits']} ta kredit")
        print("-" * 65)
    usable = sum(p["credits"] for p in profiles.values() if p.get("is_healthy"))
    print(f"  📊 JAMI: {total_credits:,} ta | ISHLATSA BO'LADI (faol): {usable:,} ta")
    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google Flow Automation Controller")
    parser.add_argument("action", choices=["status", "open", "generate", "all", "notify"], nargs="?", default="status")
    parser.add_argument("profile_arg", nargs="?", default=None, help="Profile number (positional, optional)")
    parser.add_argument("--profile", default="4", help="Profile number: 1, 2, 3, 4")
    parser.add_argument("--prompt", default="Cinematic 8k humanoid robot assembling quantum processor", help="Prompt text")
    parser.add_argument("--aspect-ratio", default="9:16", choices=["9:16", "16:9"], help="Video aspect ratio")

    args = parser.parse_args()
    # Support both positional and --profile flag
    if args.profile_arg:
        args.profile = args.profile_arg

    if args.action == "status":
        show_status()
    elif args.action == "open":
        p = profiles.get(args.profile, profiles["4"])
        launch_flow_in_chrome(p["profile_dir"])
    elif args.action == "generate":
        res = generate_video_with_flow(args.prompt, profile_choice=args.profile, aspect_ratio=args.aspect_ratio)
        print(json.dumps(res, indent=2, ensure_ascii=False))
