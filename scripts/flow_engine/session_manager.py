#!/usr/bin/env python3
"""
Flow Engine - GoogleSessionManager.
Validates authentication status, enforces safety checkpoints, and handles security gates.
STRICT POLICY: Never bypass CAPTCHA / 2FA. Alert immediately and gracefully halt.
"""

import os
import sys
import time
import subprocess
from typing import Dict, Any, Optional, Tuple

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)


class GoogleCheckpointError(Exception):
    """Raised when a Google Security Checkpoint, CAPTCHA, or re-auth is detected."""
    pass


class GoogleSessionManager:
    """Monitors and verifies authentication integrity for the target Google account."""

    def __init__(self, browser_mgr):
        self.browser_mgr = browser_mgr

    def check_session_state(self) -> Dict[str, Any]:
        """
        Inspects the active window state and window title to determine auth status.
        Returns detailed status: authenticated, checkpoint_required, login_required, or not_found.
        """
        wid = self.browser_mgr.find_flow_window()
        if not wid:
            return {
                "authenticated": False,
                "status": "WINDOW_NOT_FOUND",
                "message": "Google Flow oynasi topilmadi."
            }

        cmd = ["xdotool", "getwindowname", wid]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, env=self.browser_mgr.get_env(), timeout=3)
            title = res.stdout.strip()
        except Exception as e:
            return {"authenticated": False, "status": "ERROR", "message": str(e)}

        t_lower = title.lower()

        # Security Checkpoint / CAPTCHA Detection
        if any(w in t_lower for w in ["captcha", "challenge", "verify it's you", "подтвердите личность"]):
            return {
                "authenticated": False,
                "status": "SECURITY_CHECKPOINT",
                "message": "Google Security Checkpoint yoki CAPTCHA aniqlandi. Xavfsizlik qoidalariga ko'ra jarayon to'xtatildi.",
                "window_title": title
            }

        # Login Required
        if any(w in t_lower for w in ["войти", "sign in", "choose an account", "выберите аккаунт"]):
            return {
                "authenticated": False,
                "status": "LOGIN_REQUIRED",
                "message": "Foydalanuvchi tizimga kirmagan (Login Required).",
                "window_title": title
            }

        # Page 404 / Project not found
        if "404" in t_lower or "не найден" in t_lower or "topilmadi" in t_lower:
            return {
                "authenticated": True,
                "status": "PROJECT_NOT_FOUND_FOR_PROFILE",
                "message": "Loyiha ushbu profil uchun topilmadi (profilni tekshirish lozim).",
                "window_title": title
            }

        # Valid Flow workspace
        if any(w in t_lower for w in ["flow", "гугл флоу", "сент. 20", "robot assembling"]):
            return {
                "authenticated": True,
                "status": "AUTHENTICATED",
                "message": "Google Flow akkaunti to'liq tasdiqlangan va faol.",
                "window_title": title
            }

        return {
            "authenticated": True,
            "status": "UNKNOWN_PAGE",
            "message": f"Noma'lum oyna holati: '{title}'",
            "window_title": title
        }

    def verify_or_halt(self):
        """Halts execution and raises exception if session is compromised or gated."""
        state = self.check_session_state()
        if state["status"] == "SECURITY_CHECKPOINT":
            raise GoogleCheckpointError(state["message"])
        if not state["authenticated"]:
            raise PermissionError(f"Autentifikatsiya xatoligi: {state['message']}")
        return state
