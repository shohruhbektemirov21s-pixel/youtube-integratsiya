#!/usr/bin/env python3
"""
Flow Engine - GenerationQueue & Lock Manager.
Guarantees strict concurrency control using atomic file locks.
Prevents accidental credit drain caused by overlapping parallel tasks.
"""

import os
import sys
import time
import fcntl
from typing import Optional
from contextlib import contextmanager

LOCK_FILE_PATH = "/tmp/flow_generation_task.lock"


class QueueBusyError(Exception):
    """Raised when another generation task is already holding the exclusive lock."""
    pass


class GenerationQueue:
    """Provides atomic execution locks and serial job queueing."""

    def __init__(self, lock_path: str = LOCK_FILE_PATH):
        self.lock_path = lock_path
        self._lock_file = None

    @contextmanager
    def acquire_lock(self, timeout_seconds: int = 120, non_blocking: bool = False):
        """
        Context manager to acquire an exclusive non-reentrant lock.
        Blocks until timeout or raises QueueBusyError.
        """
        start_time = time.time()
        self._lock_file = open(self.lock_path, "w")
        acquired = False

        print("🔒 [QUEUE] Exclusive generation lock olish jarayoni...")
        while not acquired:
            try:
                flags = fcntl.LOCK_EX
                if non_blocking:
                    flags |= fcntl.LOCK_NB
                fcntl.flock(self._lock_file, flags)
                acquired = True
                self._lock_file.write(f"PID: {os.getpid()} | Time: {time.time()}\n")
                self._lock_file.flush()
                print("✅ [QUEUE] Lock muvaffaqiyatli olindi. Hech qanday parallel generatsiya kreditlarni sarflamaydi.")
            except (IOError, BlockingIOError):
                if non_blocking:
                    raise QueueBusyError("Boshqa video generatsiya hozir faol ishlamoqda. Lock band.")
                if time.time() - start_time > timeout_seconds:
                    raise TimeoutError(f"Generation lock'ni {timeout_seconds}s ichida olib bo'lmadi.")
                time.sleep(2)

        try:
            yield
        finally:
            try:
                fcntl.flock(self._lock_file, fcntl.LOCK_UN)
                self._lock_file.close()
                print("🔓 [QUEUE] Generation lock bo'shatildi.")
            except Exception:
                pass
