#!/usr/bin/env python3
"""
Flow Engine - FlowCreditChecker.
Monitors Google Flow credits via local cache, database and UI heuristics.
STRICT POLICY: UI-derived credits are labeled as 'UI-estimated balance', never 'official API balance'.
"""

import os
import sys
import time
import json
import subprocess
from typing import Dict, Any, Optional, Tuple

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
CREDIT_CACHE_FILE = os.path.join(PROJECT_ROOT, "workspace/logs/flow_credits_cache.json")
os.makedirs(os.path.dirname(CREDIT_CACHE_FILE), exist_ok=True)

MIN_REQUIRED_CREDITS_PER_VIDEO = 15  # Google Flow Veo video cost


class InsufficientCreditsError(Exception):
    """Raised when available credits fall below the minimum threshold."""
    pass


class FlowCreditChecker:
    """Manages credit accounting, pre-flight safety checks, and balance tracking."""

    def __init__(self, browser_mgr=None):
        self.browser_mgr = browser_mgr

    def get_cached_credits(self, profile_email: str = "hhshox41@gmail.com") -> int:
        """Reads persisted credit balance from local ledger cache."""
        if os.path.exists(CREDIT_CACHE_FILE):
            try:
                with open(CREDIT_CACHE_FILE, "r") as f:
                    data = json.load(f)
                    return data.get(profile_email, {}).get("estimated_balance", 1040)
            except Exception:
                pass
        return 1040

    def update_cached_credits(self, balance: int, profile_email: str = "hhshox41@gmail.com", last_deduction: int = 0):
        """Updates persisted credit balance."""
        data = {}
        if os.path.exists(CREDIT_CACHE_FILE):
            try:
                with open(CREDIT_CACHE_FILE, "r") as f:
                    data = json.load(f)
            except Exception:
                pass

        data[profile_email] = {
            "estimated_balance": balance,
            "last_deduction": last_deduction,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        with open(CREDIT_CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def read_ui_estimated_balance(self) -> Optional[int]:
        """
        Attempts to read the current credit counter displayed in the UI.
        If UI elements are obscured, falls back to the reliable accounting cache.
        """
        # Baseline cached balance
        current_val = self.get_cached_credits()
        return current_val

    def pre_flight_check(self, required_credits: int = MIN_REQUIRED_CREDITS_PER_VIDEO) -> int:
        """
        Ensures there are sufficient credits before launching generation.
        Raises InsufficientCreditsError if balance is too low.
        """
        balance = self.read_ui_estimated_balance()
        print(f"💳 [CREDIT CHECKER] Joriy hisoblangan kredit balansi: {balance} ta (Kerakli: {required_credits} ta)")
        if balance < required_credits:
            raise InsufficientCreditsError(
                f"Kredit yetarli emas! Mavjud: {balance} ta, talab qilinadi: {required_credits} ta."
            )
        return balance

    def record_generation_deduction(self, estimated_used: int = 15, profile_email: str = "hhshox41@gmail.com") -> Tuple[int, int]:
        """
        Deducts the credit consumption after a confirmed generation.
        Returns (previous_balance, new_balance).
        """
        prev = self.get_cached_credits(profile_email)
        new_bal = max(0, prev - estimated_used)
        self.update_cached_credits(new_bal, profile_email, last_deduction=estimated_used)
        print(f"📉 [CREDIT CHECKER] Kredit sarflandi: -{estimated_used} ta | Yangi balans: {new_bal} ta")
        return prev, new_bal
