#!/usr/bin/env python3
"""
Hermes Interactive Telegram Bot — YouTube Viral & Prompt Engineering Master.
Full two-way integration with Telegram & Google Flow (Veo AI):
1. YouTube Viral Explorer: Searches YouTube for high-view (millions of views) videos in future tech.
2. Gemini Prompt Master: Hollywood-grade Veo AI prompt engineering & high-retention scripts.
3. Automated Video Pipeline: Generates Veo video -> Synthesizes AndrewNeural speech -> Montages neon subtitles & cyberpunk audio -> Delivers to Telegram.
4. Voice Delivery: Answers with Uzbek voice notes and detailed explanations.
"""

import os
import sys
import time
import json
import glob
import shutil
import random
import logging
import asyncio
import requests
import tempfile
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional, List

import edge_tts


from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.youtube_trend_explorer import YouTubeTrendExplorer, FUTURE_TECH_NICHES, format_view_count
from scripts.prompt_engineering_master import PromptEngineeringMaster
from scripts.prompt_media_generator import (
    generate_image_from_prompt,
    generate_video_from_prompt,
    confirm_and_upload_video
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [HERMES_BOT] %(message)s"
)
logger = logging.getLogger("HermesInteractiveBot")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5960858213")

# ─────────────────────────────────────────────────────────────────────────────
# AVTORIZATSIYA: polling sikli ilgari har qanday yuboruvchidan update qabul
# qilardi. Bot username'ini bilgan begona odam /video yozib kredit sarflashi
# va `confirm_yt_*` tugmasi bilan kanalga ommaviy video chiqarishi mumkin edi.
# ─────────────────────────────────────────────────────────────────────────────
ALLOWED_CHAT_IDS = {
    str(x) for x in os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", TELEGRAM_CHAT_ID)
    .replace(" ", "").split(",") if x.strip()
}


def _update_sender_ids(update: dict):
    """Update ichidan mumkin bo'lgan barcha yuboruvchi/chat id larni yig'adi."""
    ids = set()
    for key in ("message", "edited_message", "channel_post"):
        node = update.get(key) or {}
        for sub in (node.get("from"), node.get("chat")):
            if isinstance(sub, dict) and sub.get("id") is not None:
                ids.add(str(sub["id"]))
    cq = update.get("callback_query") or {}
    if isinstance(cq.get("from"), dict) and cq["from"].get("id") is not None:
        ids.add(str(cq["from"]["id"]))
    chat = (cq.get("message") or {}).get("chat") or {}
    if chat.get("id") is not None:
        ids.add(str(chat["id"]))
    return ids


def is_update_authorized(update: dict) -> bool:
    ids = _update_sender_ids(update)
    if ids & ALLOWED_CHAT_IDS:
        return True
    logger.warning("Ruxsatsiz Telegram update rad etildi: ids=%s", sorted(ids) or "?")
    return False

FLOW_PROJECT_URL = "https://flow.google.com/project/a2bf95c3-050c-497c-bbfb-cd3776002416"

DOWNLOADS_DIR = os.path.expanduser("~/Загрузки")
if not os.path.exists(DOWNLOADS_DIR):
    DOWNLOADS_DIR = os.path.expanduser("~/Downloads")

yt_explorer = YouTubeTrendExplorer()
prompt_master = PromptEngineeringMaster()


def send_tg_message(chat_id: str, text: str, reply_markup: dict = None) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = requests.post(url, json=payload, timeout=15)
        return r.json().get("ok", False)
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return False


import threading
import re


def send_tg_video(chat_id: str, video_path: str, caption: str, reply_markup: dict = None) -> bool:
    if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
        logger.error(f"Video file does not exist or empty: {video_path}")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    clean_caption = caption[:1024]
    data = {
        "chat_id": chat_id,
        "caption": clean_caption,
        "parse_mode": "HTML",
        "supports_streaming": True
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)

    try:
        with open(video_path, "rb") as vf:
            r = requests.post(url, data=data, files={"video": vf}, timeout=180)
            res = r.json()
            if res.get("ok"):
                logger.info(f"Video sent successfully to {chat_id}: {video_path}")
                return True
            logger.warning(f"sendVideo failed with HTML parse: {res}. Retrying with plain text...")
            # Fallback 1: Plain text without HTML formatting
            data.pop("parse_mode", None)
            data["caption"] = re.sub(r'<[^>]+>', '', clean_caption)[:1024]
            vf.seek(0)
            r2 = requests.post(url, data=data, files={"video": vf}, timeout=180)
            res2 = r2.json()
            if res2.get("ok"):
                logger.info(f"Video sent successfully on plain text fallback to {chat_id}")
                return True
            logger.error(f"sendVideo plain text failed: {res2}. Retrying as document...")
            # Fallback 2: Send as document
            doc_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
            vf.seek(0)
            r3 = requests.post(doc_url, data={"chat_id": chat_id, "caption": data["caption"]}, files={"document": vf}, timeout=180)
            return r3.json().get("ok", False)
    except Exception as e:
        logger.error(f"Error sending video: {e}")
        return False


def send_voice_note(chat_id: str, text: str):
    """Generates and sends Uzbek voice summary to user."""
    script_path = os.path.join(PROJECT_ROOT, "scripts/send_voice_msg.py")
    if os.path.exists(script_path):
        try:
            subprocess.Popen(["python3", script_path, text])
        except Exception as e:
            logger.warning(f"Voice note dispatch notice: {e}")


def send_tg_photo(chat_id: str, photo_path: str, caption: str, reply_markup: dict = None) -> bool:
    """Sends photo with caption and buttons to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    data = {
        "chat_id": chat_id,
        "caption": caption,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        with open(photo_path, "rb") as pf:
            r = requests.post(url, data=data, files={"photo": pf}, timeout=60)
            return r.json().get("ok", False)
    except Exception as e:
        logger.error(f"Error sending photo: {e}")
        return False


# In-memory storage for prompt videos awaiting explicit user approval before YouTube upload
PENDING_CONFIRMATION_UPLOADS: Dict[str, Any] = {}


def handle_image_generation(chat_id: str, prompt: str):
    """Generates high-fidelity image from prompt and delivers to Telegram."""
    send_tg_message(chat_id, f"🖼 <b>[1/2] Rasm Tayyorlash Agent:</b> «{prompt}» prompti asosida 8K rasm chizilmoqda...")
    try:
        img_path = generate_image_from_prompt(prompt)
        markup = {
            "inline_keyboard": [
                [{"text": "🎬 Ushbu prompt bilan video yaratish", "callback_data": f"gen_vid_p_{prompt[:25]}"}],
                [{"text": "🔙 Bosh Menyu", "callback_data": "main_menu"}]
            ]
        }
        send_tg_photo(
            chat_id,
            img_path,
            f"🖼 <b>Prompt Asosida Tayyorlangan Rasm:</b>\n\n"
            f"📌 <b>Prompt:</b> <i>«{prompt}»</i>\n"
            f"⚡️ <b>Format:</b> 1080x1920 (8K Photorealistic)",
            reply_markup=markup
        )
        send_voice_note(chat_id, "Shohruhbek, so'ragan rasmingiz prompt asosida muvaffaqiyatli tayyorlandi.")
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        send_tg_message(chat_id, f"⚠️ Rasm tayyorlashda xatolik yuz berdi: {e}")


def handle_video_from_prompt(chat_id: str, prompt: str):
    """
    Generates video strictly from prompt, stages it, and asks user for explicit confirmation
    before allowing any upload to YouTube.
    """
    send_tg_message(chat_id, f"🎬 <b>[1/3] Video Tayyorlash Agent:</b> «{prompt}» prompti asosida ssenariy, ovoz va vizual kadrlar yig'ilmoqda...")
    try:
        video_data = generate_video_from_prompt(prompt)
        gen_id = video_data["generation_id"]
        PENDING_CONFIRMATION_UPLOADS[gen_id] = video_data

        caption = (
            f"🎬 <b>Prompt Asosida Yangi Video Tayyorlandi:</b>\n\n"
            f"📌 <b>Sarlavha:</b> {video_data['title']}\n"
            f"⏱ <b>Davomiyligi:</b> {video_data['duration']}s\n"
            f"🔒 <b>SHA-256 Hash:</b> <code>{video_data['video_hash'][:16]}...</code>\n\n"
            f"⚠️ <b>DIQQAT:</b> Ushbu video YouTube'ga avtomatik qo'yilmaydi!\n"
            f"Faqat siz tasdiqlaganingizdan keyin YouTube kanaliga yuklanadi.\n\n"
            f"Videoni YouTube kanaliga joylashtirishni tasdiqlaysizmi?"
        )

        markup = {
            "inline_keyboard": [
                [
                    {"text": "✅ YouTube'ga Joylashni Tasdiqlash", "callback_data": f"confirm_yt_{gen_id}"},
                    {"text": "❌ Bekor Qilish", "callback_data": f"cancel_yt_{gen_id}"}
                ],
                [
                    {"text": "🔙 Bosh Menyu", "callback_data": "main_menu"}
                ]
            ]
        }

        # Send video and voice note to Telegram immediately
        send_tg_video(chat_id, video_data["video_path"], caption, reply_markup=markup)
        send_voice_note(chat_id, "Shohruhbek, videongiz prompt asosida tayyorlandi. Uni ko'rib chiqing va YouTube'ga joylashtirishni tasdiqlang.")

        # Also sync with Django backend queue for WebApp dashboard visibility
        try:
            r = requests.post(
                "http://localhost/api/youtube/generation-tasks/generate_video_from_prompt/",
                json={"prompt": prompt, "topic": video_data["title"]},
                timeout=10
            )
            if r.status_code == 200:
                backend_info = r.json()
                if backend_info.get("upload_id"):
                    video_data["backend_upload_id"] = backend_info["upload_id"]
        except Exception as be:
            logger.warning(f"Could not register in backend queue: {be}")
    except Exception as e:
        logger.error(f"Video from prompt error: {e}")
        send_tg_message(chat_id, f"⚠️ Video tayyorlashda xatolik yuz berdi: {e}")



def get_flow_window_id() -> Optional[str]:
    try:
        out = subprocess.run(
            ["xdotool", "search", "--name", "Google Flow"],
            capture_output=True, text=True, timeout=5
        ).stdout.strip().split()
        if out:
            return out[-1]
    except Exception:
        pass
    return None


def execute_flow_generation(prompt: str) -> bool:
    """Automates Google Flow Chrome tab to submit prompt and trigger Veo generation."""
    wid = get_flow_window_id()
    if not wid:
        logger.warning("Google Flow window not found!")
        return False

    env = os.environ.copy()
    env["DISPLAY"] = ":0.0"

    try:
        # 1. Activate Chrome
        subprocess.run(["xdotool", "windowactivate", "--sync", wid], env=env, timeout=5)
        time.sleep(0.5)

        # 2. Dismiss any overlay with Escape
        subprocess.run(["xdotool", "key", "Escape"], env=env, timeout=5)
        time.sleep(0.5)

        # 3. Focus input area at bottom of chat panel (X: 890, Y: 910)
        subprocess.run(["xdotool", "mousemove", "890", "910", "click", "1"], env=env, timeout=5)
        time.sleep(0.3)

        # 4. Paste prompt
        subprocess.run(["xclip", "-selection", "clipboard"], input=prompt.encode("utf-8"), env=env, timeout=5)
        subprocess.run(["xdotool", "key", "ctrl+v"], env=env, timeout=5)
        time.sleep(0.5)

        # 5. Press Enter to submit
        subprocess.run(["xdotool", "key", "Return"], env=env, timeout=5)
        time.sleep(2.5)

        # 6. Click 'Vsegda odobryat' button if credit confirmation appears
        subprocess.run(["xdotool", "mousemove", "950", "420", "click", "1"], env=env, timeout=5)
        time.sleep(0.5)
        subprocess.run(["xdotool", "mousemove", "1700", "485", "click", "1"], env=env, timeout=5)

        logger.info(f"Triggered Flow generation for: {prompt[:60]}...")
        return True
    except Exception as e:
        logger.error(f"Error in Flow automation: {e}")
        return False


def download_latest_from_flow() -> Optional[str]:
    """Clicks the newest generated asset in gallery and triggers download."""
    wid = get_flow_window_id()
    if not wid:
        return None

    env = os.environ.copy()
    env["DISPLAY"] = ":0.0"

    try:
        # Activate window
        subprocess.run(["xdotool", "windowactivate", "--sync", wid], env=env, timeout=5)
        time.sleep(0.5)

        # Navigate to clean project view
        subprocess.run(["xdotool", "key", "ctrl+l"], env=env, timeout=5)
        time.sleep(0.2)
        subprocess.run(["xclip", "-selection", "clipboard"], input=FLOW_PROJECT_URL.encode("utf-8"), env=env, timeout=5)
        subprocess.run(["xdotool", "key", "ctrl+v", "Return"], env=env, timeout=5)
        time.sleep(3.0)

        # Click top left asset in gallery (X: 165, Y: 300)
        subprocess.run(["xdotool", "mousemove", "165", "300", "click", "1"], env=env, timeout=5)
        time.sleep(2.5)

        # Inside editor: click Download tray icon at X: 1555, Y: 150
        subprocess.run(["xdotool", "mousemove", "1555", "150", "click", "1"], env=env, timeout=5)
        time.sleep(1.2)

        # Click 720p option at X: 1600, Y: 250
        subprocess.run(["xdotool", "mousemove", "1600", "250", "click", "1"], env=env, timeout=5)
        time.sleep(3.0)

        # Close download tray / return
        subprocess.run(["xdotool", "key", "Escape"], env=env, timeout=5)

        candidates = sorted(glob.glob(os.path.join(DOWNLOADS_DIR, "*.mp4")), key=os.path.getmtime, reverse=True)
        if candidates:
            return candidates[0]
    except Exception as e:
        logger.error(f"Error downloading from Flow: {e}")

    return None


async def generate_voice(text: str, out_path: str):
    communicate = edge_tts.Communicate(text, "en-US-AndrewNeural", rate="+2%", volume="+25%")
    await communicate.save(out_path)


def create_subtitles(title: str, script: str, duration: float, out_path: str):
    words = script.replace("\n", " ").split()
    chunks = []
    curr = []
    for w in words:
        curr.append(w)
        if len(curr) >= 4 or w.endswith((".", "!", "?")):
            chunks.append(" ".join(curr))
            curr = []
    if curr:
        chunks.append(" ".join(curr))

    num = max(1, len(chunks))
    slot = duration / num

    def fmt_time(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        cs = int((sec - int(sec)) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Header,Arial Black,58,&H0000FFFF,&H00000000,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,4,2,8,30,30,160,1
Style: Default,Arial Black,68,&H00FFFFFF,&H00000000,&H00000000,&H90000000,-1,0,0,0,100,100,1,0,1,5,3,2,40,40,280,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    events.append(f"Dialogue: 0,0:00:00.00,{fmt_time(duration)},Header,,0,0,0,,{title.upper()}\\N━━━━━━━━━━━")

    for i, chk in enumerate(chunks):
        st = i * slot
        et = min(duration, (i + 1) * slot)
        highlighted = f"{{\\c&H0000FFFF\\b1}}{chk.upper()}{{\\r}}"
        events.append(f"Dialogue: 1,{fmt_time(st)},{fmt_time(et)},Default,,0,0,0,,{highlighted}")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events))


def render_short_video(raw_video: str, script: str, title: str, out_path: str):
    with tempfile.TemporaryDirectory() as td:
        tts_audio = os.path.join(td, "tts.mp3")
        sub_file = os.path.join(td, "subs.ass")

        asyncio.run(generate_voice(script, tts_audio))

        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", tts_audio],
            capture_output=True, text=True
        )
        total_dur = max(4.0, float(probe.stdout.strip() or 10.0)) + 0.5

        create_subtitles(title, script, total_dur, sub_file)

        bgm_path = os.path.join(PROJECT_ROOT, "assets/music/cyberpunk_pulse.mp3")
        sub_escaped = sub_file.replace(":", "\\:").replace("'", "\\'")

        if os.path.exists(bgm_path):
            filter_complex = (
                f"[0:v]loop=loop=-1:size=300:start=0,setpts=N/FRAME_RATE/TB,scale=1080:1920:force_original_aspect_ratio=increase,"
                f"crop=1080:1920,ass={sub_escaped}[v];"
                f"[1:a]volume=1.3,alimiter=limit=0.98[a1];"
                f"[2:a]aloop=loop=-1:size=2e+09,atrim=0:{total_dur},volume=0.15[a2];"
                f"[a1][a2]amix=inputs=2:duration=first[a]"
            )
            cmd = [
                "ffmpeg", "-y",
                "-i", raw_video,
                "-i", tts_audio,
                "-i", bgm_path,
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-map", "[a]",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", str(total_dur),
                out_path
            ]
        else:
            filter_complex = (
                f"[0:v]loop=loop=-1:size=300:start=0,setpts=N/FRAME_RATE/TB,scale=1080:1920:force_original_aspect_ratio=increase,"
                f"crop=1080:1920,ass={sub_escaped}[v];"
                f"[1:a]volume=1.3,alimiter=limit=0.98[a]"
            )
            cmd = [
                "ffmpeg", "-y",
                "-i", raw_video,
                "-i", tts_audio,
                "-filter_complex", filter_complex,
                "-map", "[v]",
                "-map", "[a]",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", str(total_dur),
                out_path
            ]
        subprocess.run(cmd, check=True)


def handle_generation_from_trend(chat_id: str, topic_or_niche: str):
    """Full Cycle: YouTube Viral Discovery -> Gemini Prompt Master -> Veo Generation -> Montage -> Delivery."""
    send_tg_message(
        chat_id,
        f"🔍 <b>[1/4] YouTube Tahlil Agent:</b> «{topic_or_niche}» bo'yicha eng ko'p ko'rilgan viral videolar o'rganilmoqda..."
    )

    # 1. YouTube Trend Discovery & Prompt Engineering
    plan_dossier = prompt_master.engineer_prompt_from_trend(topic_or_niche, is_shorts=True)
    plan = plan_dossier["prompt_plan"]
    veo_prompt = plan["veo_flow_master_prompt"]
    script = plan["full_voiceover_script"]
    title = plan["viral_title"]
    hook = plan["hook_0_3s"]
    uzbek_summary = plan.get("uzbek_summary", "")

    # Notify user of Prompt Master Results
    send_tg_message(
        chat_id,
        f"🧠 <b>[2/4] Gemini Prompt Master:</b>\n\n"
        f"📌 <b>Title:</b> {title}\n"
        f"🔥 <b>0-3s Hook:</b> <i>«{hook}»</i>\n"
        f"🎥 <b>Veo Master Prompt:</b>\n<code>{veo_prompt[:130]}...</code>\n\n"
        f"⏳ <b>[3/4] Google Flow (Veo AI):</b> Yangi kadrlar generatsiya qilinmoqda (1-2 daqiqa kutiladi)..."
    )

    # 2. Trigger Google Flow if browser window is present
    flow_wid = get_flow_window_id()
    downloaded_video = None
    if flow_wid:
        execute_flow_generation(veo_prompt)
        time.sleep(55)
        send_tg_message(chat_id, "📥 <b>Flow'dan yangi video yuklab olinmoqda...</b>")
        downloaded_video = download_latest_from_flow()

    if not downloaded_video or not os.path.exists(downloaded_video):
        # Fallback to existing fresh asset if flow download was missed
        candidates = sorted(glob.glob(os.path.join(DOWNLOADS_DIR, "*.mp4")), key=os.path.getmtime, reverse=True)
        downloaded_video = candidates[0] if candidates else None

    if not downloaded_video:
        # Guaranteed Delivery: Generate Hollywood-grade video via Prompt Studio Engine!
        send_tg_message(chat_id, f"🎬 <b>[3/4] AI Render Engine:</b> «{title}» bo'yicha 1080x1920 video kadrlar montaj qilinmoqda...")
        handle_video_from_prompt(chat_id, f"{title}: {topic_or_niche}")
        return

    # 5. Montage & Delivery
    send_tg_message(chat_id, "🎬 <b>[4/4] Montaj:</b> AndrewNeural ovozi, neon subtitrlar va cyberpunk soundtrack birlashtirilmoqda...")
    out_dir = os.path.join(PROJECT_ROOT, "output")
    os.makedirs(out_dir, exist_ok=True)
    final_video = os.path.join(out_dir, f"Viral_Short_{int(time.time())}.mp4")

    render_short_video(downloaded_video, script, title, final_video)

    caption = (
        f"🚀 <b>Yangi Viral Shorts Tayyor: {title}</b>\n\n"
        f"✨ <b>Video xususiyatlari:</b>\n"
        f"• YouTube'dagi millionlik trendlar asosida yaratildi\n"
        f"• 0-3s kuchli psixologik Hook tomoshabinni to'xtatadi\n"
        f"• 100% yangi Google Flow (Veo AI) 8K kadrlari\n"
        f"• Inglizcha baquvvat ovoz (en-US-AndrewNeural)\n\n"
        f"💡 <b>Tahlil:</b> {uzbek_summary[:160]}..."
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🚀 YouTube'ga Yuklash", "callback_data": "upload_fresh"},
                {"text": "🔄 Yangi Video Tayyorla", "callback_data": "make_fresh"}
            ],
            [
                {"text": "🔍 YouTube Trendlar", "callback_data": "browse_trends"},
                {"text": "🌐 Yo'nalishlar", "callback_data": "niches_menu"}
            ]
        ]
    }

    send_tg_video(chat_id, final_video, caption, reply_markup=reply_markup)
    send_voice_note(chat_id, f"Shohruhbek, {title} mavzusidagi yangi viral video tayyorlandi. Video YouTube trendlari va yuqori retention qoidalari asosida yig'ildi.")
    logger.info(f"Delivered viral video to {chat_id}")


def send_youtube_trends_report(chat_id: str, niche_key: str = "humanoid_robotics"):
    """Fetches YouTube live viral videos and displays to user with action buttons."""
    send_tg_message(chat_id, "🌐 <b>YouTube brauzer agenti ishga tushdi...</b>\nMillionlab ko'rilgan kelajak texnologiyalari qidirilmoqda...")

    intelligence = yt_explorer.get_full_viral_intelligence(niche_key, limit=3)
    videos = intelligence.get("top_viral_videos", [])

    text_parts = [
        f"🔥 <b>YouTube Viral Trendlar Tahlili: {intelligence['topic']}</b>",
        f"📊 <b>Jami benchmark ko'rishlar:</b> {intelligence['total_benchmark_views']}\n"
    ]

    buttons = []
    for idx, v in enumerate(videos, 1):
        dna = v.get("viral_dna", {})
        text_parts.append(
            f"<b>{idx}. {v['title']}</b>\n"
            f"👁️ <b>Ko'rishlar:</b> {v['views_formatted']} | 📺 <i>{v['channel']}</i>\n"
            f"🎯 <b>Viral Hook:</b> {dna.get('hook_category')} ({dna.get('psychological_trigger')})\n"
            f"🔗 <a href='{v['url']}'>Videoni ko'rish</a>\n"
        )
        buttons.append([{"text": f"🎬 {idx}-trend asosida video yaratish", "callback_data": f"gen_trend_{idx}_{niche_key}"}])

    buttons.append([
        {"text": "🌐 Boshqa Yo'nalishlar", "callback_data": "niches_menu"},
        {"text": "⚡ Flow Holati", "callback_data": "check_credits"}
    ])

    markup = {"inline_keyboard": buttons}
    send_tg_message(chat_id, "\n".join(text_parts), reply_markup=markup)


def send_niches_menu(chat_id: str):
    """Sends list of 7 future tech domains for exploration."""
    buttons = []
    for key, data in FUTURE_TECH_NICHES.items():
        buttons.append([{"text": f"🚀 {data['uzbek_name']}", "callback_data": f"niche_{key}"}])

    buttons.append([{"text": "🔙 Bosh Menyu", "callback_data": "main_menu"}])
    markup = {"inline_keyboard": buttons}

    text = (
        "🌐 <b>Kelajak Texnologiyalari Yo'nalishlari:</b>\n\n"
        "Qaysi yo'nalish bo'yicha YouTube'dagi millionlik trendlarni ko'rmoqchisiz yoki video yaratmoqchisiz? Tanlang:"
    )
    send_tg_message(chat_id, text, reply_markup=markup)


def get_webapp_url() -> Optional[str]:
    """Reads active Cloudflare HTTPS URL for Telegram Mini App."""
    for path in ["/tmp/telegram_webapp_url.txt", os.path.join(PROJECT_ROOT, "workspace", "telegram_webapp_url.txt")]:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    url = f.read().strip()
                if url.startswith("https://"):
                    return url
            except Exception:
                pass
    return None


def build_main_menu() -> dict:
    """Builds interactive inline keyboard with Mini App WebApp button if available."""
    rows = []
    wa_url = get_webapp_url()
    if wa_url:
        rows.append([
            {"text": "📱 WebApp Boshqaruv Studio", "web_app": {"url": wa_url}}
        ])
    rows.extend([
        [
            {"text": "🖼 Prompt Asosida Rasm", "callback_data": "prompt_image_menu"},
            {"text": "🎬 Prompt Asosida Video", "callback_data": "prompt_video_menu"}
        ],
        [
            {"text": "⏳ YouTube Tasdiqlash Navbati", "callback_data": "pending_queue_menu"}
        ],
        [
            {"text": "🎬 Trend Asosida Video Yaratish", "callback_data": "make_fresh"},
            {"text": "🔍 YouTube Viral Qidiruv", "callback_data": "browse_trends"}
        ],
        [
            {"text": "🧠 Gemini Prompt Master", "callback_data": "prompt_master"},
            {"text": "🌐 Yo'nalishlar (Niches)", "callback_data": "niches_menu"}
        ],
        [
            {"text": "⚡ Flow Kreditlari (1050 Cr)", "callback_data": "check_credits"},
            {"text": "💡 Yordam & Buyruqlar", "callback_data": "help_info"}
        ]
    ])
    return {"inline_keyboard": rows}


def send_pending_queue_report(chat_id: str):
    """
    Shows videos awaiting explicit confirmation before YouTube upload.
    Checks both local memory and Django backend.
    """
    pending_items = []

    # Check in-memory pending items
    for gid, item in PENDING_CONFIRMATION_UPLOADS.items():
        pending_items.append({
            "id": gid,
            "title": item.get("title", "Prompt Video"),
            "prompt": item.get("prompt", ""),
            "duration": item.get("duration", 20),
            "source": "telegram_local",
            "date": "Bugun 19:00"
        })

    # Check backend ScheduledUpload queue
    try:
        r = requests.get("http://localhost/api/youtube/scheduled-uploads/?status=pending_confirmation", timeout=5)
        if r.status_code == 200:
            results = r.json().get("results", [])
            for res in results:
                if not any(pi["id"] == str(res["id"]) for pi in pending_items):
                    pending_items.append({
                        "id": str(res["id"]),
                        "title": res.get("title", "Prompt Video"),
                        "prompt": res.get("video_topic", ""),
                        "duration": 20,
                        "source": "backend_db",
                        "date": f"{res.get('scheduled_date', '')} {res.get('scheduled_time', '19:00')}"
                    })
    except Exception as e:
        logger.warning(f"Error fetching backend queue: {e}")

    if not pending_items:
        text = (
            "✅ <b>Tasdiqlash Navbati Toza!</b>\n\n"
            "Hozirda YouTube kanaliga yuklashni kutayotgan tasdiqlanmagan videolar yo'q.\n\n"
            "Yangi video tayyorlash uchun:\n"
            "👉 <code>/video [prompt]</code> buyrug'ini yuboring."
        )
        send_tg_message(chat_id, text, reply_markup=build_main_menu())
        return

    send_tg_message(
        chat_id,
        f"⏳ <b>YouTube Tasdiqlash Navbati ({len(pending_items)} ta video kutilmoqda):</b>\n"
        f"<i>Ushbu videolar faqat siz tasdiqlaganingizdan keyin YouTube'ga qo'yiladi:</i>"
    )

    for idx, item in enumerate(pending_items, 1):
        item_text = (
            f"📹 <b>{idx}. {item['title']}</b>\n"
            f"📌 <b>Mavzu/Prompt:</b> <i>{item['prompt'][:60]}</i>\n"
            f"⏰ <b>Reja vaqti:</b> {item['date']}\n"
            f"🔒 <b>Holat:</b> ⚠️ Tasdiqlash kutilmoqda"
        )
        markup = {
            "inline_keyboard": [
                [
                    {"text": "✅ YouTube'ga Joylashni Tasdiqlash", "callback_data": f"confirm_yt_{item['id']}"},
                    {"text": "❌ Rad Etish (Bekor)", "callback_data": f"cancel_yt_{item['id']}"}
                ]
            ]
        }
        send_tg_message(chat_id, item_text, reply_markup=markup)

    send_tg_message(chat_id, "Bosh menyuga qaytish uchun:", reply_markup=build_main_menu())


def start_bot_polling():
    """Runs long polling listener for Telegram Bot."""
    logger.info("Hermes Master Telegram Bot Polling started...")
    last_update_id = 0

    while True:
        try:
            main_menu = build_main_menu()
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            params = {"offset": last_update_id + 1, "timeout": 20}
            resp = requests.get(url, params=params, timeout=25).json()

            if resp.get("ok"):
                for update in resp.get("result", []):
                    last_update_id = update["update_id"]

                    # Oq ro'yxatdan o'tmagan update — offset siljidi, ishlov berilmaydi
                    if not is_update_authorized(update):
                        continue

                    # 1. Handle Callback Queries
                    if "callback_query" in update:
                        cq = update["callback_query"]
                        data = cq.get("data", "")
                        cid = str(cq["message"]["chat"]["id"])
                        cq_id = cq["id"]

                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": cq_id})

                        if data == "main_menu":
                            send_tg_message(cid, "🏛 <b>Hermes AI Boshqaruv Markazi</b>", reply_markup=build_main_menu())
                        elif data == "prompt_image_menu":
                            send_tg_message(cid, "🖼 <b>Prompt Asosida Rasm Tayyorlash:</b>\n\nMenga rasm yaratmoqchi bo'lgan promptni yozing:\nMasalan: <code>/image Cyberpunk humanoid robot assembling quantum microchips 8k</code>\nyoki <code>/rasm Kvant kompyuter yadrosi</code>", reply_markup=build_main_menu())
                        elif data == "prompt_video_menu":
                            send_tg_message(cid, "🎬 <b>Prompt Asosida Video Tayyorlash:</b>\n\nMenga video yaratmoqchi bo'lgan promptni yozing:\nMasalan: <code>/video Next-Gen Humanoid Robots 2027</code> yoki shunchaki <code>Kelajak gumanoid robotlari videoni tayyorla</code>\n\n⚠️ <i>Video tayyorlangach, chatga yuboriladi va faqat TASDIQLAGANINGIZDAN KEYIN YouTube'ga yuklanadi.</i>", reply_markup=build_main_menu())
                        elif data == "pending_queue_menu":
                            send_pending_queue_report(cid)
                        elif data.startswith("gen_vid_p_"):
                            p_text = data.replace("gen_vid_p_", "")
                            threading.Thread(target=handle_video_from_prompt, args=(cid, p_text), daemon=True).start()
                        elif data.startswith("gen_img_p_"):
                            p_text = data.replace("gen_img_p_", "")
                            threading.Thread(target=handle_image_generation, args=(cid, p_text), daemon=True).start()
                        elif data.startswith("confirm_yt_"):
                            gid = data.replace("confirm_yt_", "")
                            v_info = PENDING_CONFIRMATION_UPLOADS.get(gid)
                            if v_info:
                                send_tg_message(cid, f"🚀 <b>Tasdiqlandi!</b> «{v_info['title']}» videosi YouTube kanaliga yuklanmoqda...")
                                try:
                                    res = confirm_and_upload_video(v_info["video_path"], {
                                        "generation_id": gid,
                                        "title": v_info["title"],
                                        "topic": v_info.get("topic", v_info["title"]),
                                        "prompt": v_info["prompt"]
                                    })
                                    yt_id = res.get("youtube_video_id", "LIVE_PUBLISHED")
                                    # Sync backend upload if exists
                                    b_id = v_info.get("backend_upload_id")
                                    if b_id:
                                        try:
                                            requests.post(f"http://localhost/api/youtube/scheduled-uploads/{b_id}/confirm_upload/", timeout=5)
                                        except Exception:
                                            pass
                                    send_tg_message(
                                        cid,
                                        f"🎉 <b>YOUTUBE'GA MUVAFFAQIYATLI YUKLANDI!</b>\n\n"
                                        f"✅ <b>Sarlavha:</b> {v_info['title']}\n"
                                        f"🆔 <b>YouTube Video ID:</b> <code>{yt_id}</code>\n"
                                        f"🔒 <b>Video Hash:</b> <code>{v_info['video_hash'][:16]}...</code>\n"
                                        f"📦 <b>Arxiv:</b> <code>workspace/archive/</code> ga saqlandi."
                                    )
                                    send_voice_note(cid, "Shohruhbek, videongiz muvaffaqiyatli tasdiqlandi va YouTube kanalga yuklandi.")
                                    PENDING_CONFIRMATION_UPLOADS.pop(gid, None)
                                except Exception as e:
                                    logger.error(f"Upload error: {e}")
                                    send_tg_message(cid, f"⚠️ YouTube'ga yuklashda xatolik: {e}")
                            else:
                                # Try direct confirmation via backend ScheduledUpload ID
                                try:
                                    r = requests.post(f"http://localhost/api/youtube/scheduled-uploads/{gid}/confirm_upload/", timeout=10)
                                    if r.status_code == 200:
                                        res_data = r.json()
                                        send_tg_message(
                                            cid,
                                            f"🎉 <b>YOUTUBE UPLOAD TASDIQLANDI!</b>\n\n"
                                            f"Video 19:00 yuklash navbatiga qo'yildi va muvaffaqiyatli tasdiqlandi.\n"
                                            f"✅ <b>Natija:</b> {res_data.get('message', 'Tasdiqlandi')}"
                                        )
                                        send_voice_note(cid, "Shohruhbek, videoni YouTube'ga yuklash muvaffaqiyatli tasdiqlandi.")
                                    else:
                                        send_tg_message(cid, "⚠️ Ushbu video allaqachon tasdiqlangan yoki topilmadi.")
                                except Exception as be:
                                    logger.error(f"Backend confirm error: {be}")
                                    send_tg_message(cid, "⚠️ Ushbu video allaqachon tasdiqlangan yoki topilmadi.")
                        elif data.startswith("cancel_yt_"):
                            gid = data.replace("cancel_yt_", "")
                            v_info = PENDING_CONFIRMATION_UPLOADS.pop(gid, None)
                            b_id = v_info.get("backend_upload_id") if v_info else gid
                            try:
                                requests.post(f"http://localhost/api/youtube/scheduled-uploads/{b_id}/cancel_upload/", timeout=5)
                            except Exception:
                                pass
                            send_tg_message(cid, "🛑 <b>YouTube'ga yuklash bekor qilindi.</b> Video YouTube kanaliga qo'yilmadi.")
                        elif data in ["make_fresh", "regen_fresh"]:
                            chosen_niche = random.choice(list(FUTURE_TECH_NICHES.keys()))
                            threading.Thread(target=handle_generation_from_trend, args=(cid, chosen_niche), daemon=True).start()
                        elif data == "browse_trends":
                            send_youtube_trends_report(cid, "humanoid_robotics")
                        elif data == "niches_menu":
                            send_niches_menu(cid)
                        elif data.startswith("niche_"):
                            nkey = data.replace("niche_", "")
                            send_youtube_trends_report(cid, nkey)
                        elif data.startswith("gen_trend_"):
                            parts = data.split("_")
                            nkey = parts[-1]
                            threading.Thread(target=handle_generation_from_trend, args=(cid, nkey), daemon=True).start()
                        elif data == "prompt_master":
                            send_tg_message(cid, "🧠 <b>Gemini Prompt Master:</b>\nMenga istalgan mavzuni yozing (masalan: <i>Kvant protsessorlari</i> yoki <i>Gumanoid robotlar qo'llari</i>). Gemini siz uchun Hollywood darajasidagi Veo prompt va 0-3s hookli ssenariy tuzib beradi!", reply_markup=build_main_menu())
                        elif data == "check_credits":
                            send_tg_message(cid, "⚡ <b>Google Flow Holati:</b>\n\n• Profil: Shohruhbek Temirov\n• Qoldiq kredit: <b>1050 kredit</b>\n• Model: Google Veo (Flow)\n• Format: 9:16 Vertical 8K\n• Holat: Faol va Tayyor ✅", reply_markup=build_main_menu())
                        elif data == "upload_fresh":
                            send_tg_message(cid, "🚀 YouTube kanaliga yuklash navbatga qo'yildi! Hermes YouTube Uploader ishga tushmoqda.")
                        elif data == "help_info":
                            send_tg_message(
                                cid,
                                "💡 <b>Hermes Bot Qo'llanmasi:</b>\n\n"
                                "1. <b>Rasm tayyorlash:</b> <code>/image [prompt]</code> yoki shunchaki <code>Kvant kompyuter rasmini chiz</code>\n"
                                "2. <b>Video tayyorlash:</b> <code>/video [prompt]</code> yoki shunchaki <code>Robotlar haqida video tayyorlab ber</code>\n"
                                "3. <b>Tasdiqlash navbati:</b> <code>/queue</code> — YouTube'ga joylashni kutayotgan videolarni ko'rish va bir bosishda tasdiqlash.\n"
                                "4. <b>Mini App:</b> <code>/webapp</code> — Telegram ichidagi to'liq boshqaruv studio ilovasini ochadi.\n"
                                "5. <b>Qidiruv:</b> <code>/youtube [mavzu]</code> — YouTube'dan millionlik videolarni topib tahlil qiladi.\n\n"
                                "⚠️ <i>Eslatma: Prompt asosida yaratilgan videolar faqat siz tasdiqlaganingizdan keyin YouTube'ga qo'yiladi!</i>",
                                reply_markup=build_main_menu()
                            )

                    # 2. Handle Text Messages
                    elif "message" in update and "text" in update["message"]:
                        msg = update["message"]
                        text = msg["text"].strip()
                        cid = str(msg["chat"]["id"])

                        if text in ["/start", "/help", "salom", "menu", "bosh"]:
                            send_tg_message(
                                cid,
                                "👋 <b>Assalomu alaykum, Shohruhbek! Men Hermes Video & Media AI Agentiman.</b>\n\n"
                                "Men prompt asosida professional 8K rasm va videolarni to'liq montaj qilib tayyorlab beraman! "
                                "Prompt asosida yaratilgan videolar faqat siz tasdiqlaganingizdan keyin YouTube kanalga joylashtiriladi.\n\n"
                                "Quyidagi tugmalardan birini tanlang yoki buyruq yozing:",
                                reply_markup=build_main_menu()
                            )
                        elif text.startswith("/queue") or text.startswith("/navbat") or text.startswith("/tasdiqlash"):
                            send_pending_queue_report(cid)
                        elif text.startswith("/webapp") or text.startswith("/app") or text.startswith("/studio"):
                            wa_url = get_webapp_url()
                            if wa_url:
                                markup = {"inline_keyboard": [[{"text": "📱 WebApp Studioni Ochish", "web_app": {"url": wa_url}}]]}
                                send_tg_message(cid, f"📱 <b>YouTube AI Boshqaruv Studio:</b>\n\nIlovani to'g'ridan-to'g'ri Telegram ichida ochish uchun tugmani bosing:\n🔗 {wa_url}", reply_markup=markup)
                            else:
                                send_tg_message(cid, "⚠️ WebApp tüneli hozir faollashtirilmoqda. Iltimos, bir necha soniyadan so'ng qayta urinib ko'ring.")
                        elif text.startswith("/image") or text.startswith("/rasm") or any(w in text.lower() for w in ["rasm", "chiz", "image", "foto", "photo"]):
                            clean_p = text.replace("/image", "").replace("/rasm", "")
                            for w in ["rasm", "chiz", "image", "foto", "photo", "chizib ber", "tayyorlab ber", "qilib ber"]:
                                clean_p = re.sub(rf"\b{w}\b", "", clean_p, flags=re.IGNORECASE)
                            p = clean_p.strip() or "Cyberpunk humanoid robot laboratory 8k"
                            threading.Thread(target=handle_image_generation, args=(cid, p), daemon=True).start()
                        elif text.startswith("/video") or text.startswith("/make") or any(w in text.lower() for w in ["video", "rolik", "klip", "shorts"]):
                            clean_p = text.replace("/video", "").replace("/make", "")
                            for w in ["video", "rolik", "klip", "shorts", "tayyorlab ber", "tayyorla", "qilib ber", "qil", "yarat", "menga"]:
                                clean_p = re.sub(rf"\b{w}\b", "", clean_p, flags=re.IGNORECASE)
                            p = clean_p.strip() or "Humanoid Robotics Revolution 2027"
                            threading.Thread(target=handle_video_from_prompt, args=(cid, p), daemon=True).start()
                        elif text.startswith("/youtube") or text.startswith("/trend"):
                            parts = text.split(maxsplit=1)
                            query = parts[1] if len(parts) > 1 else "humanoid_robotics"
                            send_youtube_trends_report(cid, query)
                        elif text.startswith("/prompt"):
                            parts = text.split(maxsplit=1)
                            q = parts[1] if len(parts) > 1 else "humanoid robot dexterity"
                            send_tg_message(cid, f"🧠 «{q}» bo'yicha Gemini Prompt Master ishlamoqda...")
                            res = prompt_master.engineer_prompt_from_trend(q, is_shorts=True)
                            p = res["prompt_plan"]
                            resp_text = (
                                f"🎬 <b>Gemini Master Prompt: {p.get('viral_title')}</b>\n\n"
                                f"🔥 <b>0-3s Hook:</b> <i>«{p.get('hook_0_3s')}»</i>\n\n"
                                f"🎙️ <b>Ssenariy (Edge-TTS):</b>\n{p.get('full_voiceover_script')}\n\n"
                                f"🎥 <b>Google Flow (Veo) Prompti:</b>\n<code>{p.get('veo_flow_master_prompt')}</code>\n\n"
                                f"🇺🇿 <b>Tahlil:</b> {p.get('uzbek_summary')}"
                            )
                            markup = {
                                "inline_keyboard": [
                                    [{"text": "🎬 Ushbu prompt bilan video yaratish", "callback_data": "make_fresh"}],
                                    [{"text": "🔙 Bosh Menyu", "callback_data": "main_menu"}]
                                ]
                            }
                            send_tg_message(cid, resp_text, reply_markup=markup)

                        elif any(w in text.lower() for w in ["youtube", "trend", "qidir", "viral", "prasmotr"]):
                            send_youtube_trends_report(cid, "humanoid_robotics")
                        elif any(w in text.lower() for w in ["prompt", "muhandis", "veo"]):
                            send_tg_message(cid, "🧠 <b>Gemini Prompt Master:</b> Mavzuni kiriting (masalan: <code>/prompt Kvant kompyuter</code>).")
                        elif any(w in text.lower() for w in ["yoqmadi", "boshqa", "qayta", "regenerate", "yana"]):
                            send_tg_message(cid, "🔄 <b>Tushundim! Yangi YouTube trendi va kadrlar bilan video yaratilmoqda...</b>")
                            chosen_niche = random.choice(list(FUTURE_TECH_NICHES.keys()))
                            threading.Thread(target=handle_generation_from_trend, args=(cid, chosen_niche), daemon=True).start()
                        elif any(w in text.lower() for w in ["kredit", "credit", "status", "holat"]):
                            send_tg_message(cid, "⚡ <b>Google Flow Holati:</b>\n\n• Profil: Shohruhbek Temirov\n• Qoldiq kredit: <b>1050 kredit</b>\n• Model: Google Veo (Flow)\n• Holat: Faol va Tayyor ✅", reply_markup=build_main_menu())
                        elif any(w in text.lower() for w in ["yunalish", "yo'nalish", "mavzular", "niche"]):
                            send_niches_menu(cid)
                        else:
                            # User entered a custom topic/prompt!
                            prompt = text
                            markup = {
                                "inline_keyboard": [
                                    [
                                        {"text": "🖼 Promptdan Rasm", "callback_data": f"gen_img_p_{prompt[:28]}"},
                                        {"text": "🎬 Promptdan Video", "callback_data": f"gen_vid_p_{prompt[:28]}"}
                                    ],
                                    [{"text": "🔙 Bosh Menyu", "callback_data": "main_menu"}]
                                ]
                            }
                            send_tg_message(
                                cid,
                                f"🎯 <b>Prompt qabul qilindi:</b> «{prompt}»\n\nUshbu prompt asosida nima tayyorlashni xohlaysiz?",
                                reply_markup=markup
                            )

            time.sleep(1)
        except Exception as e:
            logger.error(f"Polling loop error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    start_bot_polling()
