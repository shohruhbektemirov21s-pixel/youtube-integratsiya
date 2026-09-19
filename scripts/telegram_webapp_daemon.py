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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("telegram_webapp_daemon")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "your_telegram_bot_token_here")
CLOUDFLARED_BIN = os.path.expanduser("~/.local/bin/cloudflared")
KNOWN_CHAT_IDS = [5960858213]  # Add known user chat IDs here

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
    """Updates the default and user-specific menu buttons."""
    # Global default
    set_telegram_menu_button(app_url)
    # User-specific
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
                time.sleep(2)  # Give Cloudflare a moment to propagate
                update_all_telegram_buttons(discovered_url)

        process.wait()
    except KeyboardInterrupt:
        logger.info("Stopping tunnel daemon...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    run_tunnel()
