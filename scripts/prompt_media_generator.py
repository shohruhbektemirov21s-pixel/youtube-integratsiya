#!/usr/bin/env python3
"""
Prompt Media Generator for BeyondEra Tech / YouTube Automation.
Provides standalone, robust prompt-driven Image and Video generation.
Videos generated through this module are flagged for confirmation before YouTube upload.
"""

import os
import sys
import time
import json
import uuid
import urllib.parse
import urllib.request
import subprocess
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

logger = logging.getLogger("PromptMediaGenerator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
IMAGES_DIR = os.path.join(OUTPUT_DIR, "images")
TEMP_DIR = os.path.join(PROJECT_ROOT, "temp")
WORKSPACE_DIR = os.path.join(PROJECT_ROOT, "workspace")
READY_DIR = os.path.join(WORKSPACE_DIR, "ready_to_upload")
ARCHIVE_DIR = os.path.join(WORKSPACE_DIR, "archive")

for d in [OUTPUT_DIR, IMAGES_DIR, TEMP_DIR, WORKSPACE_DIR, READY_DIR, ARCHIVE_DIR]:
    os.makedirs(d, exist_ok=True)


def generate_image_from_prompt(
    prompt: str,
    output_path: Optional[str] = None,
    width: int = 1080,
    height: int = 1920
) -> str:
    """
    Generates an ultra-high fidelity image based on the prompt.
    1. Attempts AI image diffusion via Pollinations AI.
    2. Falls back to PIL procedural cyber-tech graphics rendering if network fails.
    """
    if not output_path:
        ts = int(time.time())
        filename = f"img_{ts}_{uuid.uuid4().hex[:6]}.jpg"
        output_path = os.path.join(IMAGES_DIR, filename)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 1. Primary engine: Pollinations AI with enhanced tech prompt
    encoded_prompt = urllib.parse.quote(f"futuristic cyberpunk high-tech 8k {prompt}, photorealistic, volumetric neon lighting")
    pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&enhance=true"

    try:
        logger.info(f"Generating image from prompt: {prompt[:80]}...")
        req = urllib.request.Request(
            pollinations_url,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = resp.read()
            if len(data) > 1024:
                with open(output_path, "wb") as f:
                    f.write(data)
                logger.info(f"✅ Image successfully generated via Pollinations: {output_path}")
                return output_path
    except Exception as e:
        logger.warning(f"Pollinations generation failed or timed out: {e}. Falling back to procedural PIL engine.")

    # 2. Fallback Engine: Procedural PIL High-Tech Render
    try:
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new("RGB", (width, height), (7, 11, 20))
        draw = ImageDraw.Draw(img)

        # Background Cyber Grid
        horizon_y = int(height * 0.65)
        center_x = width // 2
        for x in range(-width, width * 2, 60):
            draw.line([(center_x, horizon_y), (x, height)], fill=(0, 240, 255, 60), width=1)
        for y in range(horizon_y, height, 40):
            draw.line([(0, y), (width, y)], fill=(0, 240, 255, 50), width=1)

        # Volumetric Central Core
        center_y = int(height * 0.40)
        for r in range(int(width * 0.8), 0, -30):
            alpha = int(70 * (1 - r / (width * 0.8)))
            draw.ellipse(
                [center_x - r, center_y - r, center_x + r, center_y + r],
                fill=(0, int(180 * (1 - r / (width * 0.8))), 255)
            )

        # HUD Border
        margin = 40
        draw.rectangle([margin, margin, width - margin, height - margin], outline=(0, 240, 255), width=3)
        draw.line([margin, margin + 80, margin + 80, margin], fill=(255, 0, 100), width=4)

        # Prompt & Title Overlay
        display_title = prompt[:50].upper()
        display_sub = "BEYONDERA TECH // AI PROMPT VISION"
        draw.text((margin + 20, margin + 40), display_sub, fill=(0, 240, 255))
        draw.text((margin + 20, margin + 80), display_title, fill=(255, 255, 255))
        draw.text((margin + 20, height - margin - 60), f"PROMPT: {prompt[:90]}...", fill=(180, 200, 220))

        img.save(output_path, "JPEG", quality=95)
        logger.info(f"✅ Image generated via procedural PIL engine: {output_path}")
        return output_path
    except Exception as exc:
        logger.error(f"Fallback PIL generation failed: {exc}")
        # Ultra fallback: FFmpeg solid canvas
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x0a192f:s={width}x{height}",
            "-vframes", "1", output_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path


async def generate_video_from_prompt_async(
    prompt: str,
    topic: Optional[str] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Asynchronously creates a full YouTube video package strictly based on the prompt.
    Does NOT upload to YouTube. Saves video to ready_to_upload staged for confirmation.
    """
    import edge_tts
    from scripts.content_history_manager import compute_sha256_file

    gen_id = f"prompt_vid_{int(time.time())}_{uuid.uuid4().hex[:4]}"
    safe_title = (topic or prompt[:60]).replace('"', '').replace("'", "")
    
    if not output_path:
        output_path = os.path.join(OUTPUT_DIR, f"{gen_id}_final.mp4")

    # 1. Script Generation from Prompt
    script_text = (
        f"Discover the breakthrough in {prompt}. "
        f"This next-generation technology is completely reshaping our world. "
        f"Scientists and engineers are achieving what once seemed impossible. "
        f"Follow BeyondEra Tech for daily breakthroughs in future science."
    )

    # 2. Voiceover Synthesis
    voice_path = os.path.join(TEMP_DIR, f"{gen_id}_voice.mp3")
    try:
        communicate = edge_tts.Communicate(script_text, "en-US-ChristopherNeural", rate="+3%", volume="+20%")
        await communicate.save(voice_path)
    except Exception as e:
        logger.warning(f"edge_tts error: {e}. Generating fallback tone.")
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=440:duration=10",
            "-c:a", "mp3", voice_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Probe voice duration
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", voice_path],
            capture_output=True, text=True, timeout=5
        )
        duration = max(5.0, float(probe.stdout.strip() or 10.0))
    except Exception:
        duration = 10.0

    # 3. ASS Subtitles
    subs_path = os.path.join(TEMP_DIR, f"{gen_id}_subs.ass")
    sub_title = safe_title.upper()[:30]
    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,Arial Black,58,&H0000FFFF,&H00000000,&H00000000,&H90000000,-1,0,0,0,100,100,1,0,1,5,3,8,30,30,160,1
Style: Sub,Arial Black,64,&H00FFFFFF,&H00000000,&H00000000,&H90000000,-1,0,0,0,100,100,1,0,1,5,3,2,40,40,280,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:05.00,Title,,0,0,0,,{{\\b1}}{sub_title}{{\\b0}}
Dialogue: 0,0:00:05.00,0:00:{int(duration):02d}.00,Sub,,0,0,0,,{{\\c&H0000FFFF\\b1}}FUTURE TECHNOLOGY REVOLUTION{{\\r}}
"""
    with open(subs_path, "w", encoding="utf-8") as sf:
        sf.write(ass_content)

    # 4. Generate Image Base for Video / Motion Video
    bg_image = os.path.join(TEMP_DIR, f"{gen_id}_bg.jpg")
    generate_image_from_prompt(prompt, bg_image, width=1080, height=1920)

    # 5. FFmpeg Render: Zooming Ken-Burns Motion + Subtitles + Audio
    escaped_subs = subs_path.replace(":", "\\:").replace("'", "\\'")
    bg_music = os.path.join(PROJECT_ROOT, "assets/audio_library/cyber_pulse.aac")
    if not os.path.exists(bg_music):
        bg_music = os.path.join(PROJECT_ROOT, "assets/music/cyberpunk_pulse.mp3")

    filter_complex = (
        f"[0:v]zoompan=z='min(zoom+0.0015,1.15)':d={int(duration*30)}:s=1080x1920:fps=30,"
        f"ass='{escaped_subs}'[v];"
    )

    if os.path.exists(bg_music):
        filter_complex += (
            f"[1:a]volume=1.3[voice];"
            f"[2:a]volume=0.12[bg];"
            f"[voice][bg]amix=inputs=2:duration=first[a]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", bg_image,
            "-i", voice_path,
            "-stream_loop", "-1", "-i", bg_music,
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(duration + 0.5),
            output_path
        ]
    else:
        filter_complex += f"[1:a]volume=1.2[a]"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", bg_image,
            "-i", voice_path,
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(duration + 0.5),
            output_path
        ]

    logger.info("Executing FFmpeg render for prompt video...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        logger.error(f"FFmpeg error: {res.stderr}")
        raise RuntimeError(f"FFmpeg render error: {res.stderr}")

    v_hash = compute_sha256_file(output_path)
    
    # Stage into ready_to_upload
    staged_path = os.path.join(READY_DIR, f"{gen_id}_{os.path.basename(output_path)}")
    try:
        import shutil
        shutil.copy2(output_path, staged_path)
    except Exception:
        staged_path = output_path

    # Create thumbnail
    thumb_path = os.path.join(OUTPUT_DIR, f"{gen_id}_thumb.jpg")
    try:
        shutil.copy2(bg_image, thumb_path)
    except Exception:
        pass

    result = {
        "generation_id": gen_id,
        "title": safe_title,
        "prompt": prompt,
        "video_path": output_path,
        "staged_path": staged_path,
        "thumbnail_path": thumb_path,
        "duration": round(duration, 1),
        "video_hash": v_hash,
        "status": "PENDING_CONFIRMATION",  # Strictly awaits confirmation!
        "created_at": datetime.now().isoformat()
    }
    logger.info(f"✅ Video generated from prompt successfully! Status: PENDING_CONFIRMATION")
    return result


def generate_video_from_prompt(
    prompt: str,
    topic: Optional[str] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """Synchronous wrapper for generate_video_from_prompt_async."""
    import asyncio
    return asyncio.run(generate_video_from_prompt_async(prompt, topic, output_path))


def confirm_and_upload_video(video_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Uploads a previously generated and confirmed video to YouTube.
    Executes deduplication, API upload, archiving, and DB sync.
    """
    from scripts.youtube_uploader import upload_to_youtube
    logger.info(f"Confirming YouTube upload for: {metadata.get('title')}")
    upload_res = upload_to_youtube(video_path, metadata)
    return upload_res


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "image":
        p = sys.argv[2] if len(sys.argv) > 2 else "Humanoid robot assembling microchips in cyber laboratory"
        img = generate_image_from_prompt(p)
        print(f"IMAGE_OUTPUT: {img}")
    elif len(sys.argv) > 1 and sys.argv[1] == "video":
        p = sys.argv[2] if len(sys.argv) > 2 else "Quantum Computing Neural AI Core"
        vid = generate_video_from_prompt(p)
        print(json.dumps(vid, indent=2))
    else:
        print("Usage: python prompt_media_generator.py image <prompt> | video <prompt>")
