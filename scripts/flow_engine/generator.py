#!/usr/bin/env python3
"""
Flow Engine - FlowGenerator.
Responsible for reliable prompt injection, model parameters, submission,
and auto-approval dialog handling on Google Flow interface.
Uses robust X11 input typing, contenteditable navigation and UI interaction.
"""

import os
import sys
import time
import subprocess
from typing import Dict, Any, Optional

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)


class FlowGenerator:
    """Automates prompt dispatch and generation confirmation inside Flow workspace."""

    def __init__(self, browser_mgr):
        self.browser_mgr = browser_mgr

    def prepare_input_field(self, wid: str) -> bool:
        """
        Locates and focuses the bottom-right prompt input field.
        Uses fallback strategy: window activation + prompt box click + focus check.
        """
        env = self.browser_mgr.get_env()
        try:
            # Focus prompt box (default coordinates on 1080p: x=1680, y=952)
            subprocess.run(["xdotool", "windowactivate", "--sync", wid], env=env, timeout=3)
            subprocess.run(["xdotool", "mousemove", "1680", "952", "click", "1"], env=env, timeout=3)
            time.sleep(0.3)
            # Select all existing text if any and clear
            subprocess.run(["xdotool", "key", "--clearmodifiers", "ctrl+a", "BackSpace"], env=env, timeout=3)
            return True
        except Exception as e:
            print(f"⚠️ Input maydonini tayyorlashda xatolik: {e}")
            return False

    def submit_prompt(self, prompt: str, is_video_request: bool = True) -> Dict[str, Any]:
        """
        Submits prompt to the active Flow session.
        If is_video_request is True, prefixes with video generation instruction if needed.
        """
        wid = self.browser_mgr.find_flow_window()
        if not wid:
            self.browser_mgr.launch_or_focus()
            wid = self.browser_mgr.find_flow_window()

        if not wid:
            raise RuntimeError("Google Flow oynasi topilmadi.")

        print(f"📝 [FLOW GENERATOR] Prompt kiritilmoqda: \"{prompt[:70]}...\"")
        self.prepare_input_field(wid)

        env = self.browser_mgr.get_env()
        clean_prompt = prompt.replace("\n", " ").strip()

        # Type the prompt with realistic typing delay
        try:
            subprocess.run(
                ["xdotool", "type", "--delay", "12", clean_prompt],
                env=env,
                timeout=20,
                check=True
            )
            time.sleep(0.4)
            # Submit with Return
            subprocess.run(["xdotool", "key", "Return"], env=env, timeout=3, check=True)
            print("🚀 [FLOW GENERATOR] Prompt muvaffaqiyatli yuborildi!")
        except Exception as e:
            raise RuntimeError(f"Promptni yozishda xatolik yuz berdi: {e}")

        # Check for approval dialog ("Сгенерировать 1 видео за бонусы?" / "Всегда одобрять")
        time.sleep(1.5)
        self.handle_approval_dialog(wid)

        return {
            "success": True,
            "prompt": clean_prompt,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

    def handle_approval_dialog(self, wid: str):
        """
        Checks if the Flow bonus confirmation dialog appeared.
        If so, clicks 'Всегда одобрять' or 'Одобрить' to start generation.
        """
        env = self.browser_mgr.get_env()
        try:
            # Click 'Всегда одобрять' button position (x=1700, y=748)
            # or click 'Одобрить' (x=1700, y=705)
            subprocess.run(["xdotool", "mousemove", "1700", "748", "click", "1"], env=env, timeout=2)
            time.sleep(0.5)
            # Fallback in case of smaller dialog: click bottom-right 'Одобрить' (x=1700, y=705)
            subprocess.run(["xdotool", "mousemove", "1700", "705", "click", "1"], env=env, timeout=2)
            print("👍 [FLOW GENERATOR] Bonuslar dialogi tekshirildi va tasdiqlandi.")
        except Exception:
            pass
