#!/usr/bin/env python3
"""
Telegram WebApp & Cloudflare Tunnel Supervisor
Automatically starts a Cloudflare tunnel for the YouTube AI Automation frontend,
obtains the public HTTPS URL, and sets the Telegram Bot's Chat Menu Button
so users can launch the full dashboard as a Telegram Mini App directly.
"""

import os
import re
import sys
import time
import json
import logging
import subprocess
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("telegram_webapp_daemon")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CLOUDFLARED_BIN = os.path.expanduser("~/.local/bin/cloudflared")
KNOWN_CHAT_IDS = [
    int(x) for x in os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", "").replace(" ", "").split(",")
    if x.strip().lstrip("-").isdigit()
] or [5960858213]
URL_CACHE_FILES = [
    "/tmp/telegram_webapp_url.txt",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspace", "telegram_webapp_url.txt")
]


def set_telegram_menu_button(app_url: str, chat_id: int = None) -> bool:
    """Sets the Telegram bot chat menu button to open the Web App."""
    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setChatMenuButton"
    payload = {
        "menu_button": {
            "type": "web_app",
            "text": "📱 Boshqaruv Paneli",
            "web_app": {
                "url": app_url
            }
        }
    }
    if chat_id:
        payload["chat_id"] = chat_id

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                logger.info(f"Successfully set Telegram menu button for chat_id={chat_id or 'default'}: {app_url}")
                return True
            else:
                logger.warning(f"Telegram API warning for chat_id={chat_id}: {data}")
    except Exception as e:
        logger.error(f"Failed to set Telegram menu button: {e}")
    return False

def update_all_telegram_buttons(app_url: str):
    """Menyu tugmasini FAQAT ruxsat etilgan chat'lar uchun o'rnatadi.

    Ilgari bu yerda chat_id'siz set_telegram_menu_button(app_url) ham chaqirilardi —
    u botning GLOBAL default tugmasini o'rnatib, botga /start yozgan har qanday
    begona odamga "Boshqaruv Paneli" tugmasini ko'rsatardi.
    """
    for cid in KNOWN_CHAT_IDS:
        set_telegram_menu_button(app_url, chat_id=cid)

def run_tunnel():
    """Runs cloudflared tunnel and supervises the connection."""
    cmd = [CLOUDFLARED_BIN, "tunnel", "--url", "http://localhost:80"]
    logger.info(f"Starting cloudflared tunnel: {' '.join(cmd)}")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
    discovered_url = None

    try:
        for line in process.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()

            match = url_pattern.search(line)
            if match and not discovered_url:
                discovered_url = match.group(0)
                logger.info(f"Discovered Cloudflare Tunnel URL: {discovered_url}")
                for cache_file in URL_CACHE_FILES:
                    try:
                        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                        with open(cache_file, "w") as f:
                            f.write(discovered_url)
                        logger.info(f"Saved tunnel URL to {cache_file}")
                    except Exception as fe:
                        logger.warning(f"Could not save to {cache_file}: {fe}")
                time.sleep(2)  # Give Cloudflare a moment to propagate
                update_all_telegram_buttons(discovered_url)

        process.wait()
    except KeyboardInterrupt:
        logger.info("Stopping tunnel daemon...")
        process.terminate()
        process.wait()

def main():
    """Tunnel uzilsa qayta ko'taradi (eksponensial backoff bilan)."""
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN o'rnatilmagan — chiqilmoqda.")
        sys.exit(1)

    backoff = 5
    while True:
        started = time.time()
        try:
            run_tunnel()
        except Exception as exc:
            logger.error(f"Tunnel xatosi: {exc}")
        uptime = time.time() - started
        backoff = 5 if uptime > 120 else min(backoff * 2, 300)
        logger.warning(f"Tunnel to'xtadi ({uptime:.0f}s ishladi). {backoff}s dan keyin qayta uriniladi...")
        time.sleep(backoff)


if __name__ == "__main__":
    main()
