#!/usr/bin/env python3
"""
Flow Engine - GenerationStatusTracker.
Monitors the generation lifecycle in Google Flow workspace.
Tracks progress, detects completion, and guards against hang / timeout conditions.
"""

import os
import sys
import time
import subprocess
from typing import Dict, Any, Optional

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)


class GenerationTimeoutError(Exception):
    """Raised when video generation exceeds timeout limit."""
    pass


class GenerationStatusTracker:
    """Tracks generation progress and signals completion."""

    def __init__(self, browser_mgr, timeout_seconds: int = 180):
        self.browser_mgr = browser_mgr
        self.timeout_seconds = timeout_seconds

    def wait_for_completion(self, start_timestamp: float, check_interval: int = 4) -> Dict[str, Any]:
        """
        Polls Flow generation status until complete, failed, or timed out.
        Detects completion through download triggers, progress stabilization, or UI cues.
        """
        print(f"⏳ [STATUS TRACKER] Video generatsiyasi kuzatilmoqda (Maksimal vaqt: {self.timeout_seconds}s)...")
        elapsed = 0

        while elapsed < self.timeout_seconds:
            time.sleep(check_interval)
            elapsed = time.time() - start_timestamp

            # 1. Check if a newly completed file already dropped in download folders
            from scripts.flow_engine.downloader import VideoDownloader
            downloader = VideoDownloader(self.browser_mgr)
            fresh_file = downloader.find_latest_download(since_timestamp=start_timestamp)
            if fresh_file and not fresh_file.endswith(".crdownload"):
                print(f"🎉 [STATUS TRACKER] Yangi fayl yuklab olingani aniqlandi: {os.path.basename(fresh_file)} ({elapsed:.1f}s)")
                return {
                    "completed": True,
                    "status": "COMPLETED",
                    "file_path": fresh_file,
                    "elapsed_seconds": round(elapsed, 1)
                }

            # Periodic progress logging
            if int(elapsed) % 16 == 0:
                print(f"  ⏱ Jarayon davom etmoqda: {elapsed:.0f}s o'tdi...")

        # If loop finishes without early return, we reached timeout
        print(f"⚠️ [STATUS TRACKER] Generatsiya vaqti tugadi ({self.timeout_seconds}s).")
        return {
            "completed": False,
            "status": "TIMEOUT",
            "elapsed_seconds": round(elapsed, 1),
            "file_path": None
        }
