#!/usr/bin/env python3
"""
Utility to generate and send Telegram Voice Messages in native Uzbek.
Uses Edge-TTS (uz-UZ-MadinaNeural / uz-UZ-SardorNeural) + FFmpeg + Telegram sendVoice.
"""

import sys
import os
import asyncio
import argparse
import subprocess
import requests
import tempfile
import edge_tts

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DEFAULT_CHAT_ID = "5960858213"


async def generate_and_send_voice(text: str, chat_id: str = DEFAULT_CHAT_ID, voice: str = "uz-UZ-MadinaNeural", caption: str = None) -> bool:
    """Generate Uzbek speech from text and send as Telegram Voice note."""
    if not text or not text.strip():
        return False

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_mp3:
        mp3_path = f_mp3.name
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f_ogg:
        ogg_path = f_ogg.name

    try:
        # 1. Synthesize speech using Edge-TTS in Uzbek
        comm = edge_tts.Communicate(text.strip(), voice)
        await comm.save(mp3_path)

        # 2. Transcode to Ogg Opus for Telegram voice note
        subprocess.run(
            ["ffmpeg", "-y", "-i", mp3_path, "-c:a", "libopus", "-b:a", "32k", ogg_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )

        # 3. Send via Telegram Bot API sendVoice
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendVoice"
        with open(ogg_path, "rb") as voice_file:
            data = {"chat_id": chat_id}
            if caption:
                data["caption"] = caption
            resp = requests.post(url, data=data, files={"voice": voice_file}, timeout=25)
            
        success = resp.status_code == 200 and resp.json().get("ok", False)
        if success:
            print(f"✅ Ovozli xabar muvaffaqiyatli yuborildi: '{text[:50]}...'")
        else:
            print(f"❌ Telegram xatoligi: {resp.status_code} - {resp.text}")
        return success

    except Exception as e:
        print(f"❌ Ovoz yaratish/yuborishda xatolik: {e}")
        return False
    finally:
        for p in (mp3_path, ogg_path):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send Uzbek voice message to Telegram")
    parser.add_argument("text", help="Text to speak in Uzbek")
    parser.add_argument("--chat-id", default=DEFAULT_CHAT_ID, help="Telegram chat ID")
    parser.add_argument("--voice", choices=["uz-UZ-MadinaNeural", "uz-UZ-SardorNeural"], default="uz-UZ-MadinaNeural")
    parser.add_argument("--caption", default="", help="Optional caption")

    args = parser.parse_args()
    asyncio.run(generate_and_send_voice(args.text, args.chat_id, args.voice, args.caption or None))
