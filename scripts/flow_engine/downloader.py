#!/usr/bin/env python3
"""
Flow Engine - VideoDownloader.
Triggers Flow video download / export actions and scans download folders for completed files.
Handles temporary .crdownload locks and verifies download integrity.
"""

import os
import sys
import glob
import time
import subprocess
from typing import Optional, List

DOWNLOAD_DIRS = [
    os.path.expanduser("~/Загрузки"),
    os.path.expanduser("~/Downloads"),
    "/tmp"
]


class VideoDownloader:
    """Manages browser download triggering and filesystem scanning."""

    def __init__(self, browser_mgr=None):
        self.browser_mgr = browser_mgr

    def trigger_ui_download(self) -> bool:
        """
        Sends click to Download button on Flow UI and confirms export.
        Download button: x=1640, y=152.
        1K/2K resolution option: x=1700, y=200.
        """
        if not self.browser_mgr:
            return False
        env = self.browser_mgr.get_env()
        wid = self.browser_mgr.find_flow_window()
        if not wid:
            return False

        try:
            # Click download tray icon (editor header)
            subprocess.run(["xdotool", "windowactivate", "--sync", wid], env=env, timeout=3)
            # Flow editor header download icon is at x=1555, y=150
            subprocess.run(["xdotool", "mousemove", "1555", "150", "click", "1"], env=env, timeout=3)
            time.sleep(1.2)
            # Click '1080p' (x=1600, y=300) or '720p' (x=1600, y=250)
            subprocess.run(["xdotool", "mousemove", "1600", "250", "click", "1"], env=env, timeout=3)
            print("📥 [DOWNLOADER] UI orqali video yuklab olish buyrug'i berildi.")
            return True
        except Exception as e:
            print(f"⚠️ Yuklab olish tugmasini bosishda xatolik: {e}")
            return False

    def find_latest_download(self, since_timestamp: float, wait_timeout: int = 15) -> Optional[str]:
        """
        Scans download directories for files created after since_timestamp.
        Waits until file is completely written (no .crdownload in progress).
        """
        start_wait = time.time()
        while time.time() - start_wait < wait_timeout:
            for d in DOWNLOAD_DIRS:
                if not os.path.exists(d):
                    continue
                # Search mp4, mov, webm, jpeg, png
                patterns = [os.path.join(d, "*.mp4"), os.path.join(d, "*.jpeg"), os.path.join(d, "*.png")]
                for p in patterns:
                    for f in glob.glob(p):
                        try:
                            mtime = os.path.getmtime(f)
                            if mtime >= since_timestamp - 3:
                                # Ensure no companion .crdownload
                                crdownload = f + ".crdownload"
                                if not os.path.exists(crdownload) and os.path.getsize(f) > 50 * 1024:
                                    return f
                        except Exception:
                            pass
            time.sleep(1)
        return None
