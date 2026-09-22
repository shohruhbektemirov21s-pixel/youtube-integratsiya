#!/usr/bin/env python3
"""
Flow Engine - Video Audio & Subtitle Enrichment Component.
Transforms silent Veo/Flow video clips into ready-to-publish YouTube/Shorts videos:
1. Intelligent Voiceover Script Generation based on prompt & topic.
2. Neural Text-To-Speech (Edge-TTS) in Uzbek or English.
3. Ambient Sci-Fi Music layer with dynamic volume ducking.
4. Mobile-safe High-Retention ASS Subtitles.
5. FFmpeg master muxing.
"""

import os
import sys
import subprocess
import tempfile
from typing import Dict, Any, Optional, Tuple

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.audio_subtitles_engine import (
    synthesize_voiceover,
    generate_styled_ass_subtitles,
    mix_voice_and_ambient,
    resolve_ambient_music
)


def create_dynamic_script(prompt: str, topic: Optional[str] = None, lang: str = "uz") -> str:
    """Creates a concise, impactful 10-second script for the video."""
    p_lower = prompt.lower()
    
    if lang == "uz":
        if "robot" in p_lower or "processor" in p_lower or "quantum" in p_lower:
            return "Kvant texnologiyalari davri boshlandi. Gumanoid robotlar yuqori aniqlikdagi mikrosxemalarni yigʻmoqda. Kelajak allaqachon shu yerda."
        elif "cyber" in p_lower or "city" in p_lower:
            return "Kelajak megapolislari sunʼiy intellekt va avtomatika boshqaruvida rivojlanmoqda. Texnologik inqilob yangi bosqichda."
        elif "space" in p_lower or "mars" in p_lower:
            return "Insoniyat yangi koinot missiyalariga tayyorlanmoqda. Avtonom stansiyalar fazo sirlarini kashf etmoqda."
        else:
            clean_topic = topic or "Kelajak texnologiyalari"
            return f"{clean_topic}. Sunʼiy intellekt va eng ilgʻor muhandislik yutuqlari hayotimizni oʻzgartirmoqda."
    else:
        if "robot" in p_lower or "processor" in p_lower or "quantum" in p_lower:
            return "Humanoid robotics assemble next-generation quantum processors with microscopic precision. The future is here."
        elif "cyber" in p_lower or "city" in p_lower:
            return "Autonomous megacities powered by advanced artificial intelligence are shaping tomorrow. The revolution begins now."
        elif "space" in p_lower or "mars" in p_lower:
            return "Autonomous deep-space probes prepare the frontier for human colonization. Beyond the known horizons."
        else:
            clean_topic = topic or "Frontier Technology"
            return f"Frontier breakthrough in {clean_topic}. Autonomous intelligence powering the next technological era."


def enrich_video_with_audio(
    input_video_path: str,
    output_video_path: str,
    prompt: str,
    topic: Optional[str] = None,
    language: str = "uz",
    music_name: Optional[str] = "ambient_flow_synth.aac",
    music_volume: float = 0.18,
    custom_script: Optional[str] = None
) -> Dict[str, Any]:
    """
    Takes a raw/silent Flow video and adds:
    - AI voiceover (Edge-TTS)
    - Ambient Sci-Fi soundtrack
    - Animated neon subtitles
    Returns metadata dict.
    """
    if not os.path.exists(input_video_path):
        raise FileNotFoundError(f"Input video not found: {input_video_path}")

    # Determine probe duration of input video
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", input_video_path
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True)
    try:
        video_duration = float(res.stdout.strip())
    except Exception:
        video_duration = 10.0

    # 1. Prepare Voiceover Script
    script_text = custom_script or create_dynamic_script(prompt, topic=topic, lang=language)
    voice_name = "uz-UZ-MadinaNeural" if language == "uz" else "en-US-ChristopherNeural"

    print(f"🎙️ [Audio Enricher] Ovozlilashtirish ({language.upper()} - {voice_name}): \"{script_text}\"")

    # 2. Synthesize Voiceover
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f_voice:
        tmp_voice = f_voice.name

    voice_path, voice_dur = synthesize_voiceover(
        text=script_text,
        voice=voice_name,
        rate="+4%",
        output_path=tmp_voice
    )

    # 3. Resolve Ambient Music & Mix
    with tempfile.NamedTemporaryFile(suffix=".aac", delete=False) as f_mix:
        tmp_mixed_audio = f_mix.name

    music_path = resolve_ambient_music(music_name)
    mix_voice_and_ambient(
        voice_path=voice_path,
        ambient_path=music_path,
        total_duration=video_duration,
        output_audio=tmp_mixed_audio,
        music_volume=music_volume
    )

    # 4. Generate Styled ASS Subtitles
    with tempfile.NamedTemporaryFile(suffix=".ass", delete=False) as f_ass:
        tmp_ass = f_ass.name

    primary_color = "&H00E5FF" if language == "uz" else "&H00FFFF" # Cyan for UZ, Yellow for EN
    generate_styled_ass_subtitles(
        script_text=script_text,
        total_duration=video_duration,
        output_ass=tmp_ass,
        is_shorts=True,
        custom_primary=primary_color
    )

    # 5. FFmpeg Final Video Assemble
    os.makedirs(os.path.dirname(os.path.abspath(output_video_path)), exist_ok=True)
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", input_video_path,
        "-i", tmp_mixed_audio,
        "-vf", f"ass={tmp_ass}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-t", str(video_duration),
        output_video_path
    ]

    print(f"🎬 [Audio Enricher] FFmpeg orqali to'liq audio + video render qilinmoqda...")
    subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Cleanup temp files
    for p in [tmp_voice, tmp_mixed_audio, tmp_ass]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

    return {
        "status": "success",
        "output_path": output_video_path,
        "duration": video_duration,
        "script": script_text,
        "language": language,
        "voice": voice_name,
        "has_audio": True,
        "has_subtitles": True
    }
