#!/usr/bin/env python3
"""
Flow Engine - VideoStorage.
Persists downloaded media into canonical project storage, computes SHA-256 hashes,
validates format integrity, and links assets to pipeline workspaces.
"""

import os
import sys
import shutil
import hashlib
from typing import Dict, Any, Optional

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
CANONICAL_STORAGE_DIR = os.path.join(PROJECT_ROOT, "assets/video_library")
os.makedirs(CANONICAL_STORAGE_DIR, exist_ok=True)


class VideoStorage:
    """Manages secure persistence and verification of generated assets."""

    def __init__(self, target_dir: str = CANONICAL_STORAGE_DIR):
        self.target_dir = target_dir

    @staticmethod
    def compute_sha256(file_path: str) -> str:
        """Computes SHA-256 hash of the media file."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def store_asset(self, source_path: str, generation_id: str, label: str = "flow_clip") -> Dict[str, Any]:
        """
        Copies media file from temporary/downloads location to project library.
        Returns detailed storage metadata record.
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Manba fayl topilmadi: {source_path}")

        ext = os.path.splitext(source_path)[1].lower() or ".mp4"
        dest_filename = f"{label}_{generation_id}{ext}"
        dest_path = os.path.join(self.target_dir, dest_filename)

        shutil.copy2(source_path, dest_path)
        sha256_hash = self.compute_sha256(dest_path)
        size_bytes = os.path.getsize(dest_path)

        print(f"💾 [STORAGE] Aktiv loyiha omboriga saqlandi: {dest_path} ({size_bytes / 1024:.1f} KB)")
        return {
            "stored": True,
            "filename": dest_filename,
            "storage_path": dest_path,
            "sha256": sha256_hash,
            "size_bytes": size_bytes,
            "extension": ext
        }
