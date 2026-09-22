#!/usr/bin/env python3
"""
Content History & Semantic Deduplication Manager.
Maintains persistent content memory and enforces zero duplicate topics, scripts, and video hashes.
"""

import os
import sys
import json
import re
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
HISTORY_FILE = os.path.join(PROJECT_ROOT, "assets/content_history.json")


def compute_sha256_text(text: str) -> str:
    """Computes SHA-256 for a given string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_sha256_file(filepath: str) -> str:
    """Computes SHA-256 for a given file on disk."""
    if not os.path.exists(filepath):
        return ""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def normalize_text(text: str) -> str:
    """Normalizes text for linguistic and token comparison."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    tokens = [w for w in text.split() if len(w) > 2]
    # Filter common stop words
    stop_words = {
        "the", "and", "that", "this", "with", "for", "from", "will", "are",
        "how", "what", "why", "into", "your", "our", "their", "just", "now",
        "part", "shorts", "video", "episode", "haqida", "bilan", "uchun"
    }
    filtered = [w for w in tokens if w not in stop_words]
    return " ".join(filtered)


def calculate_jaccard_similarity(text1: str, text2: str) -> float:
    """Calculates Jaccard token similarity between two texts."""
    tokens1 = set(normalize_text(text1).split())
    tokens2 = set(normalize_text(text2).split())
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return len(intersection) / float(len(union))


def calculate_ngram_similarity(text1: str, text2: str, n: int = 3) -> float:
    """Calculates character n-gram similarity (useful for slight phrasing changes)."""
    t1 = normalize_text(text1)
    t2 = normalize_text(text2)
    if len(t1) < n or len(t2) < n:
        return 1.0 if t1 == t2 else 0.0
    ngrams1 = set(t1[i:i+n] for i in range(len(t1) - n + 1))
    ngrams2 = set(t2[i:i+n] for i in range(len(t2) - n + 1))
    intersection = ngrams1.intersection(ngrams2)
    union = ngrams1.union(ngrams2)
    return len(intersection) / float(len(union))


import difflib

def calculate_token_containment(text1: str, text2: str) -> float:
    """Calculates how much the shorter text's key terms are contained in the longer text."""
    tokens1 = set(normalize_text(text1).split())
    tokens2 = set(normalize_text(text2).split())
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    min_len = min(len(tokens1), len(tokens2))
    return len(intersection) / float(min_len)


def calculate_semantic_similarity(text1: str, text2: str) -> float:
    """
    Combined semantic/lexical similarity score between 0.0 and 1.0.
    Detects variations like:
    '5 Future Technologies That Will Change Your Life'
    vs
    '5 Technologies That Will Transform Your Future'
    """
    t1_clean = normalize_text(text1)
    t2_clean = normalize_text(text2)
    if not t1_clean or not t2_clean:
        return 0.0
    if t1_clean == t2_clean:
        return 1.0

    # 1. Sequence similarity
    seq_sim = difflib.SequenceMatcher(None, t1_clean, t2_clean).ratio()

    # 2. Token overlap & Jaccard
    jaccard = calculate_jaccard_similarity(text1, text2)

    # 3. Containment (how many shared critical keywords)
    containment = calculate_token_containment(text1, text2)

    # 4. N-gram similarity
    ngram = calculate_ngram_similarity(text1, text2, n=3)

    # Weighted score emphasizing shared concepts
    return (containment * 0.35) + (seq_sim * 0.25) + (jaccard * 0.25) + (ngram * 0.15)



class ContentHistoryManager:
    def __init__(self, history_file: str = HISTORY_FILE):
        self.history_file = history_file
        self._ensure_file()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        if not os.path.exists(self.history_file):
            initial_data = {
                "version": "2.0.0",
                "description": "BeyondEra Tech Permanent Content Memory & Duplicate Registry",
                "created_at": datetime.now().isoformat(),
                "records": []
            }
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=2, ensure_ascii=False)

    def load_records(self) -> List[Dict[str, Any]]:
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("records", [])
        except Exception as e:
            print(f"⚠️ Content history load error: {e}")
            return []

    def save_records(self, records: List[Dict[str, Any]]):
        data = {
            "version": "2.0.0",
            "updated_at": datetime.now().isoformat(),
            "total_records": len(records),
            "records": records
        }
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def is_video_hash_duplicate(self, video_hash: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Checks if a video SHA-256 hash already exists in history."""
        if not video_hash:
            return False, None
        for r in self.load_records():
            if r.get("video_hash") == video_hash:
                return True, r
        return False, None

    def is_generation_id_duplicate(self, generation_id: str) -> bool:
        """Checks if a generation ID already exists in history."""
        if not generation_id:
            return False
        for r in self.load_records():
            if r.get("generation_id") == generation_id:
                return True
        return False

    def is_topic_duplicate(self, topic: str, threshold: float = 0.55) -> Tuple[bool, Optional[Dict[str, Any]], float]:
        """
        Detects if topic is identical or semantically similar to any prior topic.
        Returns (is_duplicate, matched_record, similarity_score).
        """
        records = self.load_records()
        for r in records:
            prev_topic = r.get("topic", "")
            prev_title = r.get("title", "")
            sim_topic = calculate_semantic_similarity(topic, prev_topic)
            sim_title = calculate_semantic_similarity(topic, prev_title)
            max_sim = max(sim_topic, sim_title)
            if max_sim >= threshold:
                return True, r, max_sim
        return False, None, 0.0

    def is_script_duplicate(self, script: str, threshold: float = 0.65) -> Tuple[bool, Optional[Dict[str, Any]], float]:
        """Detects if script is identical or heavily duplicated."""
        script_hash = compute_sha256_text(script)
        records = self.load_records()
        for r in records:
            if r.get("script_hash") == script_hash:
                return True, r, 1.0
            prev_script = r.get("script", "")
            if prev_script:
                sim = calculate_semantic_similarity(script, prev_script)
                if sim >= threshold:
                    return True, r, sim
        return False, None, 0.0

    def record_generation(
        self,
        generation_id: str,
        topic: str,
        title: str,
        script: str,
        prompt: str,
        flow_generation_id: str,
        output_path: str,
        video_hash: str,
        thumbnail_path: Optional[str] = None,
        status: str = "READY_TO_UPLOAD",
        youtube_video_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Records a new video generation into persistent content memory."""
        records = self.load_records()

        # Check if record with this generation_id already exists to update
        for r in records:
            if r.get("generation_id") == generation_id:
                r.update({
                    "topic": topic,
                    "title": title,
                    "topic_hash": compute_sha256_text(topic),
                    "script_hash": compute_sha256_text(script),
                    "prompt_hash": compute_sha256_text(prompt),
                    "flow_generation_id": flow_generation_id,
                    "output_path": output_path,
                    "video_hash": video_hash,
                    "thumbnail_path": thumbnail_path or r.get("thumbnail_path"),
                    "status": status,
                    "youtube_video_id": youtube_video_id or r.get("youtube_video_id"),
                    "updated_at": datetime.now().isoformat()
                })
                if metadata:
                    r.setdefault("metadata", {}).update(metadata)
                self.save_records(records)
                return r

        new_record = {
            "generation_id": generation_id,
            "topic": topic,
            "title": title,
            "topic_hash": compute_sha256_text(topic),
            "script_hash": compute_sha256_text(script),
            "prompt_hash": compute_sha256_text(prompt),
            "flow_generation_id": flow_generation_id,
            "output_path": output_path,
            "video_hash": video_hash,
            "thumbnail_path": thumbnail_path,
            "status": status,
            "created_at": datetime.now().isoformat(),
            "uploaded_at": datetime.now().isoformat() if status == "PUBLISHED" else None,
            "youtube_video_id": youtube_video_id,
            "metadata": metadata or {}
        }
        records.append(new_record)
        self.save_records(records)
        return new_record

    def update_status(
        self,
        generation_id: str,
        status: str,
        youtube_video_id: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Updates the status and YouTube video ID for an existing generation record."""
        records = self.load_records()
        updated = False
        for r in records:
            if r.get("generation_id") == generation_id:
                r["status"] = status
                r["updated_at"] = datetime.now().isoformat()
                if youtube_video_id:
                    r["youtube_video_id"] = youtube_video_id
                    r["uploaded_at"] = datetime.now().isoformat()
                if error_message:
                    r["error_message"] = error_message
                updated = True
                break
        if updated:
            self.save_records(records)
        return updated
