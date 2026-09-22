import os
import subprocess
import requests

def build_video():
    os.makedirs("output", exist_ok=True)
    video_in = "/home/kali/Загрузки/Quantum_AI_neural_processor_flows_20260920204809.mp4"
    voice_in = "/tmp/quantum_ai_voice.mp3"
    bg_music = "assets/audio_library/cyber_pulse.aac"
    output_video = "output/Quantum_AI_Short_Fresh.mp4"
    subtitles_file = "/tmp/quantum_subtitles.ass"

    # 1. Create stylish ASS subtitles
    ass_content = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: NeonTitle,Noto Sans,64,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,6,3,2,60,60,420,1
Style: NeonAccent,Noto Sans,68,&H00FFFF00,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,6,3,2,60,60,420,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.10,0:00:02.80,NeonTitle,,0,0,0,,{\\b1}THE FUTURE OF COMPUTING{\\b0}
Dialogue: 0,0:00:02.80,0:00:05.80,NeonAccent,,0,0,0,,{\\b1}QUANTUM AI NEURAL CORE{\\b0}
Dialogue: 0,0:00:05.80,0:00:09.20,NeonTitle,,0,0,0,,{\\b1}BILLIONS OF QUANTUM OPERATIONS{\\b0}
Dialogue: 0,0:00:09.20,0:00:12.60,NeonAccent,,0,0,0,,{\\b1}DAWN OF TRUE CONSCIOUSNESS{\\b0}
"""
    with open(subtitles_file, "w") as f:
        f.write(ass_content)

    print("[1/3] ASS Subtitles generated.")

    # 2. FFmpeg command:
    # - Loop video or stream_loop
    # - Scale to 1080x1920
    # - Burn subtitles
    # - Duck background music under clear compressed voiceover
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "1", "-i", video_in,
        "-i", voice_in,
        "-stream_loop", "-1", "-i", bg_music,
        "-filter_complex",
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,ass=" + subtitles_file + "[v];"
        "[1:a]volume=1.4,acompressor=threshold=0.1:ratio=4:attack=5:release=50[voice];"
        "[2:a]volume=0.14[bg];"
        "[voice][bg]amix=inputs=2:duration=first:dropout_transition=2[a]",
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", "13.0",
        output_video
    ]

    print("[2/3] Rendering final Shorts video with FFmpeg...")
    subprocess.run(cmd, check=True)
    print(f"[3/3] Render complete: {output_video}")

if __name__ == "__main__":
    build_video()
