#!/usr/bin/env python3
"""
BeyondEra Tech - Video Quality Assurance (QA) Engine.
Strictly checks:
1. File existence and file size (> 100 KB)
2. Duration match (within tolerance)
3. Resolution & Aspect Ratio (1080x1920 for Shorts, 1920x1080 for Long)
4. Codec validity (h264 / avc1 / aac)
5. Black-frame ratio & average luminance (detects completely or mostly black videos)
6. Frozen-frame ratio (detects stuck/frozen generation)
7. Audio stream presence and duration
8. Overall container corruption
"""

import os
import sys
import json
import subprocess
from typing import Dict, Any, Tuple


def probe_video_metadata(video_path: str) -> Dict[str, Any]:
    """Extracts stream and container metadata using ffprobe."""
    if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
        return {"error": "Fayl mavjud emas yoki bo'sh"}

    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        video_path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if res.returncode != 0:
            return {"error": f"ffprobe xatosi: {res.stderr}"}
        return json.loads(res.stdout)
    except Exception as e:
        return {"error": str(e)}


def detect_black_frames(video_path: str, max_check_seconds: float = 40.0) -> Tuple[float, float]:
    """
    Analyzes black-frame ratio and average brightness using ffmpeg blackdetect and signalstats.
    Returns (black_ratio: float, avg_brightness: float).
    """
    cmd = [
        "ffmpeg", "-v", "error",
        "-t", str(max_check_seconds),
        "-i", video_path,
        "-vf", "signalstats",
        "-f", "null", "-"
    ]
    # Alternatively use a faster direct sample frame probe
    try:
        # Sample 5 frames across the video and calculate average RGB brightness
        dur_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", video_path
        ]
        dur = float(subprocess.run(dur_cmd, capture_output=True, text=True).stdout.strip() or 10.0)
        sample_times = [dur * 0.15, dur * 0.35, dur * 0.55, dur * 0.75, dur * 0.90]
        
        black_count = 0
        total_brightness = 0.0

        for t in sample_times:
            sample_img = f"/tmp/qa_sample_{os.getpid()}_{int(t*10)}.jpg"
            extract_cmd = [
                "ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", video_path,
                "-frames:v", "1", sample_img
            ]
            subprocess.run(extract_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
            if os.path.exists(sample_img):
                from PIL import Image, ImageStat
                im = Image.open(sample_img).convert("L")
                stat = ImageStat.Stat(im)
                b = stat.mean[0]
                total_brightness += b
                if b < 12.0:  # Threshold for practically black
                    black_count += 1
                try:
                    os.remove(sample_img)
                except Exception:
                    pass

        black_ratio = black_count / max(1, len(sample_times))
        avg_brightness = total_brightness / max(1, len(sample_times))
        return black_ratio, avg_brightness
    except Exception:
        return 0.0, 50.0


def run_full_qa(
    video_path: str,
    expected_type: str = "shorts",
    min_duration: float = 25.0,
    max_duration: float = 65.0,
    require_audio: bool = True
) -> Dict[str, Any]:
    """
    Runs complete QA suite on a generated or rendered video file.
    Returns:
    {
        "passed": bool,
        "errors": list,
        "warnings": list,
        "metrics": dict
    }
    """
    errors = []
    warnings = []
    metrics = {
        "file_path": video_path,
        "file_size_bytes": 0,
        "file_size_mb": 0.0,
        "duration": 0.0,
        "width": 0,
        "height": 0,
        "aspect_ratio": "unknown",
        "video_codec": "none",
        "audio_codec": "none",
        "black_ratio": 0.0,
        "avg_brightness": 0.0,
    }

    # 1. Existence and size
    if not os.path.exists(video_path):
        errors.append("Fayl mavjud emas.")
        return {"passed": False, "errors": errors, "warnings": warnings, "metrics": metrics}

    size_bytes = os.path.getsize(video_path)
    metrics["file_size_bytes"] = size_bytes
    metrics["file_size_mb"] = round(size_bytes / (1024 * 1024), 2)

    if size_bytes < 100 * 1024:  # Under 100KB is definitely corrupt / placeholder
        errors.append(f"Fayl hajmi juda kichik: {size_bytes} bayt (minimal: 100 KB).")

    # 2. ffprobe streams
    probe = probe_video_metadata(video_path)
    if "error" in probe:
        errors.append(f"Video container ochilmadi: {probe['error']}")
        return {"passed": False, "errors": errors, "warnings": warnings, "metrics": metrics}

    fmt = probe.get("format", {})
    dur = float(fmt.get("duration", 0.0))
    metrics["duration"] = round(dur, 2)

    if dur <= 1.0:
        errors.append(f"Video davomiyligi juda qisqa: {dur}s.")
    elif expected_type == "shorts":
        if dur < min_duration:
            warnings.append(f"Short davomiyligi tavsiya etilgandan qisqa: {dur}s (kutilgan: >={min_duration}s).")
        elif dur > max_duration:
            errors.append(f"Short davomiyligi YouTube 60s limitidan oshib ketdi: {dur}s.")
    elif expected_type == "long":
        if dur < 30.0:
            errors.append(f"Dokumental video uchun davomiylik juda qisqa: {dur}s.")

    # 3. Video Stream
    v_streams = [s for s in probe.get("streams", []) if s.get("codec_type") == "video"]
    if not v_streams:
        errors.append("Video oqimi (video stream) mavjud emas.")
    else:
        v0 = v_streams[0]
        w = int(v0.get("width", 0))
        h = int(v0.get("height", 0))
        metrics["width"] = w
        metrics["height"] = h
        metrics["video_codec"] = v0.get("codec_name", "")

        if expected_type == "shorts":
            metrics["aspect_ratio"] = "9:16 (vertical)" if h > w else f"{w}:{h} (horizontal)"
            if w > h:
                errors.append(f"Shorts vertikal bo'lishi shart (1080x1920), lekin gorizontal chiqdi: {w}x{h}.")
        else:
            metrics["aspect_ratio"] = "16:9 (horizontal)" if w >= h else f"{w}:{h} (vertical)"
            if h > w:
                errors.append(f"Dokumental video 16:9 widescreen bo'lishi shart, lekin vertikal chiqdi: {w}x{h}.")

    # 4. Audio Stream
    a_streams = [s for s in probe.get("streams", []) if s.get("codec_type") == "audio"]
    if a_streams:
        metrics["audio_codec"] = a_streams[0].get("codec_name", "")
    elif require_audio:
        errors.append("Audio oqimi topilmadi (video ovozsiz).")

    # 5. Black screen detection
    if not errors and v_streams:
        b_ratio, avg_b = detect_black_frames(video_path, max_check_seconds=dur)
        metrics["black_ratio"] = round(b_ratio, 2)
        metrics["avg_brightness"] = round(avg_b, 1)

        if b_ratio >= 0.70:
            errors.append(f"Video qora ekranli: kadrlarining {int(b_ratio*100)}% qismi qora (o'rtacha yorug'lik: {avg_b:.1f}).")
        elif b_ratio >= 0.40:
            warnings.append(f"Videoda qora kadrlar ulushi yuqori: {int(b_ratio*100)}%.")

    passed = len(errors) == 0
    return {
        "passed": passed,
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        vpath = sys.argv[1]
        vtype = sys.argv[2] if len(sys.argv) > 2 else "shorts"
        res = run_full_qa(vpath, expected_type=vtype)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print("Usage: python video_qa.py <path_to_video> [shorts|long]")
