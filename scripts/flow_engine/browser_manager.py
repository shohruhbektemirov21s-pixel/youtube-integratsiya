#!/usr/bin/env python3
"""
Flow Engine - FlowBrowserManager.
Controls the Chrome browser instance, profiles, window activation, and crash recovery.
"""

import os
import sys
import time
import subprocess
from typing import Optional, Dict, Any, List

CHROME_BIN = "/opt/google/chrome/chrome"
if not os.path.exists(CHROME_BIN):
    CHROME_BIN = "/usr/bin/google-chrome"

DEFAULT_DISPLAY = os.getenv("DISPLAY", ":0.0")
TARGET_FLOW_PROJECT_URL = "https://flow.google.com/project/a2bf95c3-050c-497c-bbfb-cd3776002416"
DEFAULT_PROFILE = "Profile 17"  # BeyondEra Tech (hhshox41@gmail.com PRO)


class FlowBrowserManager:
    """Manages Chrome lifecycle, profile isolation, window discovery and activation."""

    def __init__(
        self,
        profile_dir: str = DEFAULT_PROFILE,
        project_url: str = TARGET_FLOW_PROJECT_URL,
        display: str = DEFAULT_DISPLAY
    ):
        self.profile_dir = profile_dir
        self.project_url = project_url
        self.display = display
        self.active_wid: Optional[str] = None

    def get_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        env["DISPLAY"] = self.display
        env["HOME"] = os.path.expanduser("~")
        return env

    def find_flow_window(self) -> Optional[str]:
        """Finds active Chrome window hosting Google Flow."""
        try:
            cmd = ["xdotool", "search", "--class", "google-chrome"]
            res = subprocess.run(cmd, capture_output=True, text=True, env=self.get_env(), timeout=5)
            wids = [w.strip() for w in res.stdout.splitlines() if w.strip()]
            for wid in wids:
                t_cmd = ["xdotool", "getwindowname", wid]
                t_res = subprocess.run(t_cmd, capture_output=True, text=True, env=self.get_env(), timeout=2)
                title = t_res.stdout.lower()
                if "flow" in title or "гугл флоу" in title or "google" in title:
                    self.active_wid = wid
                    return wid
        except Exception:
            pass
        return None

    def activate_window(self, wid: Optional[str] = None) -> bool:
        """Brings the Flow window to foreground and focuses it."""
        target_wid = wid or self.active_wid or self.find_flow_window()
        if not target_wid:
            return False
        try:
            subprocess.run(["xdotool", "windowmap", target_wid], env=self.get_env(), timeout=3)
            subprocess.run(["xdotool", "windowactivate", "--sync", target_wid], env=self.get_env(), timeout=3)
            time.sleep(0.5)
            self.active_wid = target_wid
            return True
        except Exception:
            return False

    def launch_or_focus(self) -> str:
        """Ensures the Chrome window with Flow project is open and active."""
        existing = self.find_flow_window()
        if existing:
            self.activate_window(existing)
            return existing

        # Launch fresh instance
        cmd = [
            CHROME_BIN,
            f"--profile-directory={self.profile_dir}",
            "--new-window",
            self.project_url
        ]
        try:
            subprocess.Popen(
                cmd,
                env=self.get_env(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            time.sleep(4)
        except Exception as e:
            raise RuntimeError(f"Chrome brauzerini ishga tushirib bo'lmadi: {e}")

        # Wait up to 15 seconds for window to register
        start = time.time()
        while time.time() - start < 15:
            wid = self.find_flow_window()
            if wid:
                self.activate_window(wid)
                return wid
            time.sleep(1)

        raise TimeoutError("Flow loyihasi oynasi belgilangan vaqtda ochilmadi.")

    def navigate_to_url(self, url: str) -> bool:
        """Navigates the currently focused Flow tab to target URL."""
        if not self.activate_window():
            self.launch_or_focus()

        try:
            subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+l"], env=self.get_env(), timeout=3)
            time.sleep(0.3)
            subprocess.run(["xdotool", "type", "--delay", "20", url], env=self.get_env(), timeout=8)
            time.sleep(0.3)
            subprocess.run(["xdotool", "key", "Return"], env=self.get_env(), timeout=3)
            time.sleep(3)
            return True
        except Exception:
            return False

    def is_alive(self) -> bool:
        """Checks if the tracked window is still present in X11."""
        if not self.active_wid:
            return bool(self.find_flow_window())
        try:
            cmd = ["xdotool", "getwindowname", self.active_wid]
            res = subprocess.run(cmd, capture_output=True, text=True, env=self.get_env(), timeout=2)
            return res.returncode == 0 and bool(res.stdout.strip())
        except Exception:
            return False
