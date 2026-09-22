import os
import sys
import uuid
import json
import shutil
import logging
import subprocess
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("video_render_engine")

PROJECT_ROOT = "/home/kali/Рабочий стол/Youtube akkaunt integratsiyasi"
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# Append project root to sys.path so we can import modules
sys.path.append(PROJECT_ROOT)

from scripts.audio_subtitles_engine import (
    synthesize_voiceover,
    generate_styled_ass_subtitles,
    resolve_ambient_music
)
from scripts.video_qa import run_full_qa


class VideoRenderingError(Exception):
    """Custom exception for video rendering failures."""
    pass


def select_video_clips(scene_prompts: List[str], work_dir: str) -> List[str]:
    """
    Selects video clips based on scene prompts. Uses semantic keyword matching.
    """
    assets_dir = os.path.join(PROJECT_ROOT, "assets", "video_library")
    downloads_dir = os.path.expanduser("~/Загрузки")
    
    # Try to copy fresh downloads first (optional logic, could expand)
    try:
        if os.path.exists(downloads_dir):
            for f in os.listdir(downloads_dir):
                if f.startswith("flow_clip_") and f.endswith(".mp4"):
                    src = os.path.join(downloads_dir, f)
                    dst = os.path.join(assets_dir, f)
                    if not os.path.exists(dst):
                        shutil.copy2(src, dst)
                        logger.info(f"Copied fresh clip {f} from Downloads.")
    except Exception as e:
        logger.warning(f"Failed to copy fresh clips from Downloads: {e}")

    # Discover available clips
    available_clips = []
    if os.path.exists(assets_dir):
        available_clips = [os.path.join(assets_dir, f) for f in os.listdir(assets_dir) if f.startswith("flow_clip_") and f.endswith(".mp4")]
    
    # Ensure we have at least a dummy clip or fail if totally empty
    if not available_clips:
        logger.warning(f"No clips found in {assets_dir}. Will use dummy logic or fail.")
        return []

    available_clips.sort()
    
    clip_map = {
        'quantum': 'flow_clip_2.mp4',
        'photon': 'flow_clip_2.mp4',
        'laser': 'flow_clip_2.mp4',
        'neural': 'flow_clip_3.mp4',
        'brain': 'flow_clip_3.mp4',
        'synapse': 'flow_clip_3.mp4',
        'matrix': 'flow_clip_4.mp4',
        'data': 'flow_clip_4.mp4',
        'algorithm': 'flow_clip_4.mp4',
        'space': 'flow_clip_5.mp4',
        'orbit': 'flow_clip_5.mp4',
        'cosmic': 'flow_clip_5.mp4'
    }

    selected_clips = []
    default_clip = available_clips[0]
    
    for prompt in scene_prompts:
        prompt_lower = prompt.lower()
        matched = False
        for kw, filename in clip_map.items():
            if kw in prompt_lower:
                clip_path = os.path.join(assets_dir, filename)
                if clip_path in available_clips:
                    selected_clips.append(clip_path)
                    matched = True
                    break
        
        if not matched:
            selected_clips.append(default_clip)
            
    # If no prompts, just pick some clips
    if not selected_clips:
        selected_clips = available_clips[:min(len(available_clips), 5)]

    logger.info(f"Selected {len(selected_clips)} clips for scenes.")
    return selected_clips


def normalize_clips(clips: List[str], work_dir: str, target_duration: float) -> List[str]:
    """
    Normalizes clips to exactly 1080x1920 30fps.
    Splits the target duration evenly among the clips.
    """
    if not clips:
        raise VideoRenderingError("No clips provided for normalization.")

    normalized = []
    duration_per_clip = target_duration / len(clips)
    
    for i, clip in enumerate(clips):
        out_path = os.path.join(work_dir, f"norm_clip_{i:03d}.mp4")
        
        cmd = [
            "ffmpeg", "-y", "-i", clip,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
            "-t", str(duration_per_clip),
            "-an",  # Remove audio from background clips
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            out_path
        ]
        
        logger.info(f"Normalizing clip {i} -> {out_path} for {duration_per_clip:.2f}s")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        normalized.append(out_path)
        
    return normalized


def concatenate_clips(normalized_clips: List[str], work_dir: str) -> str:
    """
    Concatenates normalized clips using the concat demuxer.
    """
    list_path = os.path.join(work_dir, "concat_list.txt")
    with open(list_path, 'w') as f:
        for clip in normalized_clips:
            # Concat demuxer needs paths relative to list or absolute, escaping might be needed.
            # Using absolute paths.
            f.write(f"file '{clip}'\n")
            
    out_path = os.path.join(work_dir, "concatenated_video.mp4")
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        out_path
    ]
    
    logger.info("Concatenating clips...")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_path


def synthesize_voice(script_text: str, voice_name: str, rate: str, work_dir: str) -> str:
    """
    Synthesizes the voiceover.
    """
    out_path = os.path.join(work_dir, "raw_voice.mp3")
    logger.info("Synthesizing voiceover...")
    result = synthesize_voiceover(
        text=script_text,
        voice_id=voice_name,
        speed=rate,
        output_path=out_path
    )
    if not result:
        raise VideoRenderingError("Voice synthesis failed.")
    return out_path


def get_audio_duration(file_path: str) -> float:
    """Gets the duration of an audio/video file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", file_path
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())


def boost_voice(raw_voice: str, work_dir: str) -> str:
    """
    Applies highpass filter, dynamic audio normalization and volume boost to voiceover.
    """
    out_path = os.path.join(work_dir, "boosted_voice.wav")
    cmd = [
        "ffmpeg", "-y", "-i", raw_voice,
        "-af", "highpass=f=75,dynaudnorm=f=150:g=15:m=10:p=0.95,volume=1.35",
        out_path
    ]
    logger.info("Boosting voiceover clarity...")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_path


def generate_subtitles(script: str, duration: float, work_dir: str, subtitle_color: str) -> str:
    """
    Generates an ASS subtitle file.
    """
    out_path = os.path.join(work_dir, "subs.ass")
    logger.info("Generating styled ASS subtitles...")
    result = generate_styled_ass_subtitles(
        script=script,
        duration=duration,
        output_path=out_path,
        style_type="modern",
        color=subtitle_color
    )
    if not result:
        logger.warning("Subtitle generation returned false, but checking if file exists.")
        
    if not os.path.exists(out_path):
        # Create a dummy blank subtitle file just so it doesn't crash
        with open(out_path, 'w') as f:
            f.write("[Script Info]\nScriptType=v4.00+\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    return out_path


def mix_audio(voice: str, music_profile: str, duration: float, work_dir: str) -> str:
    """
    Mixes voiceover with ambient music using amix. Voice at 1.0, ambient at 0.12.
    """
    # First, get the actual ambient music path
    ambient_path = resolve_ambient_music(music_profile)
    if not ambient_path or not os.path.exists(ambient_path):
        logger.warning(f"Ambient music profile '{music_profile}' not found or resolve failed. Using voice only.")
        return voice
        
    out_path = os.path.join(work_dir, "mixed_audio.wav")
    
    # Loop ambient music if it's shorter than the duration, and mix it
    # Complex filter: 
    # [1:a]volume=0.12[amb];[0:a]volume=1.0[v];[v][amb]amix=inputs=2:duration=first:dropout_transition=2
    cmd = [
        "ffmpeg", "-y",
        "-i", voice,
        "-stream_loop", "-1", "-i", ambient_path,
        "-filter_complex", "[1:a]volume=0.12[amb];[0:a]volume=1.0[v];[v][amb]amix=inputs=2:duration=first:dropout_transition=2",
        "-c:a", "pcm_s16le",
        out_path
    ]
    
    logger.info("Mixing audio tracks...")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_path


def final_render(video: str, audio: str, subtitles: str, output_path: str, duration: float) -> None:
    """
    Final FFmpeg render combining video, audio, and burning subtitles.
    """
    logger.info(f"Starting final render to {output_path} (Duration: {duration:.2f}s)")
    
    # Escape path for the subtitles filter
    # FFmpeg requires escaping for paths in filters
    escaped_subs = subtitles.replace('\\', '\\\\').replace(':', '\\:').replace("'", "\\'")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video,
        "-i", audio,
        "-vf", f"ass='{escaped_subs}'",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "256k",
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        "-shortest",
        output_path
    ]
    
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    logger.info("Final render completed successfully.")


def render_shorts_video(content_plan: Dict) -> Dict:
    """
    Main entry point for rendering a YouTube Short based on a content plan.
    Returns: {'success': bool, 'video_path': str, 'duration': float, 'qa': dict}
    """
    logger.info("Starting video render pipeline...")
    
    # Extract metadata from content plan
    script_text = content_plan.get('script', "Default script if missing.")
    voice_name = content_plan.get('voice_profile', 'default_voice')
    rate = content_plan.get('speech_rate', '+0%')
    scene_prompts = content_plan.get('scenes', [])
    music_profile = content_plan.get('music_profile', 'ambient_default')
    subtitle_color = content_plan.get('subtitle_color', '&H00FFFFFF')
    
    uid = str(uuid.uuid4())[:8]
    work_dir = os.path.join(PROJECT_ROOT, "workspace", f"render_{uid}")
    os.makedirs(work_dir, exist_ok=True)
    
    output_dir = os.path.join(PROJECT_ROOT, "workspace", "ready_to_upload")
    os.makedirs(output_dir, exist_ok=True)
    
    final_output_path = os.path.join(output_dir, f"short_{uid}.mp4")
    
    try:
        # Step d, e: Synthesize and boost voice
        raw_voice_path = synthesize_voice(script_text, voice_name, rate, work_dir)
        boosted_voice_path = boost_voice(raw_voice_path, work_dir)
        
        # Determine exact duration based on voiceover
        voice_duration = get_audio_duration(boosted_voice_path)
        # Add 1.5s padding
        target_duration = voice_duration + 1.5
        logger.info(f"Voice duration: {voice_duration:.2f}s, Target video duration: {target_duration:.2f}s")
        
        # Step a, b, c: Video visuals
        if not scene_prompts:
            scene_prompts = ["default"] * max(1, int(target_duration / 5)) # Dummy prompts if missing
            
        selected_clips = select_video_clips(scene_prompts, work_dir)
        
        if not selected_clips:
            raise VideoRenderingError("Failed to select any video clips.")
            
        normalized_clips = normalize_clips(selected_clips, work_dir, target_duration)
        concatenated_video = concatenate_clips(normalized_clips, work_dir)
        
        # Step f: Subtitles
        subs_path = generate_subtitles(script_text, target_duration, work_dir, subtitle_color)
        
        # Step g: Mix audio
        mixed_audio_path = mix_audio(boosted_voice_path, music_profile, target_duration, work_dir)
        
        # Step h: Final render
        final_render(concatenated_video, mixed_audio_path, subs_path, final_output_path, target_duration)
        
        # Step i: QA
        qa_result = {}
        try:
            qa_result = run_full_qa(final_output_path)
            logger.info(f"QA Results: {json.dumps(qa_result)}")
        except Exception as qa_err:
            logger.warning(f"QA check failed: {qa_err}")
            qa_result = {"error": str(qa_err)}
            
        # Cleanup work dir
        try:
            shutil.rmtree(work_dir)
        except Exception as cleanup_err:
            logger.warning(f"Failed to cleanup work dir: {cleanup_err}")
            
        return {
            'success': True,
            'video_path': final_output_path,
            'duration': target_duration,
            'qa': qa_result
        }
        
    except Exception as e:
        logger.error(f"Render pipeline failed: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'video_path': None,
            'duration': 0.0,
            'qa': {}
        }


if __name__ == "__main__":
    # Test stub
    dummy_plan = {
        "script": "Welcome to the future of AI. In this short, we explore the boundaries of neural networks and space travel.",
        "scenes": ["neural network in the brain", "space travel cosmic orbit"],
        "voice_profile": "nova",
        "speech_rate": "+5%",
        "music_profile": "tech_minimal",
        "subtitle_color": "&H0000FFFF"
    }
    
    print("Testing video render engine with dummy plan...")
    res = render_shorts_video(dummy_plan)
    print("Result:", json.dumps(res, indent=2))
