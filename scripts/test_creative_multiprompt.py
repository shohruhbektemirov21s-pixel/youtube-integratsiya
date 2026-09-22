#!/usr/bin/env python3
"""
Test script to verify Multi-Prompt Creative Hybrid Video Generation.
Validates:
1. Multi-prompt scene decomposition (Kelajak texnologiyalari: Quantum, Robot, Neural, Fusion, Space).
2. Creative hybrid blending: Alternating dynamic Flow video clips & animated futuristic tech imagery.
3. Audio synthesis & styled subtitles.
4. Video QA validation (0 black screens, strict aspect ratio, valid duration).
"""

import os
import sys
import json
import time

PROJECT_ROOT = "/home/kali/Рабочий стол/Youtube akkaunt integratsiyasi"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.flow_controller import acquire_multi_prompt_assets
from scripts.ffmpeg_render_engine import assemble_final_video
from scripts.video_qa import run_full_qa

def test_multi_prompt_pipeline():
    print("=" * 70)
    print("🚀 TEST: KELAJAK TEXNOLOGIYALARI - MULTI-PROMPT KREATIV VIDEO SINOVI")
    print("=" * 70)

    # Simulated multi-prompt content plan representing frontier future tech
    test_content_plan = {
        "generation_id": f"test_multiprompt_{int(time.time())}",
        "topic": "Next-Gen Quantum Humanoids & Neural Singularity",
        "video_type": "shorts",
        "title": "How Quantum Humanoids Will Evolve By 2030 🤖 #Shorts",
        "script": "By 2030, humanoid robotics and quantum optical processors will merge into a single entity. With sub-millimeter dexterity, synthetic synapses execute trillions of decisions in real-time. Magnetic fusion supplies continuous clean energy, opening humanity's expansion across orbital space.",
        "voiceover_text": "By 2030, humanoid robotics and quantum optical processors will merge into a single entity. With sub-millimeter dexterity, synthetic synapses execute trillions of decisions in real-time. Magnetic fusion supplies continuous clean energy, opening humanity's expansion across orbital space.",
        "creative_direction": {
            "primary_hex": "0x00f0ff",
            "accent_hex": "0xff0055",
            "voice_name": "en-US-ChristopherNeural",
            "voice_rate": "+3%",
            "music_profile": "ambient_flow_synth",
            "subtitle_color": "&H00FFFF"
        },
        "scenes": [
            {
                "title": "Act 1 The Inflection",
                "prompt": "Cinematic vertical 9:16 shot of quantum optical processor with laser beams in cryogenic chamber",
                "voiceover": "By 2030, humanoid robotics and quantum optical processors will merge into a single entity.",
                "telemetry": "QUANTUM.LATTICE: 99.99%"
            },
            {
                "title": "Act 2 Mechanical Precision",
                "prompt": "Vertical 9:16 macro shot of robotic titanium hand assembling micro-actuators with electrical sparks",
                "voiceover": "With sub-millimeter dexterity, synthetic synapses execute trillions of decisions in real-time.",
                "telemetry": "ACTUATOR.PRECISION: 0.02mm"
            },
            {
                "title": "Act 3 Synaptic Network",
                "prompt": "Vertical 9:16 glowing synaptic neural network visualization with hyper-fast data pulses",
                "voiceover": "Synthetic synapses execute trillions of decisions in real-time.",
                "telemetry": "NEURAL.SYNAPSE: 10.4 TB/s"
            },
            {
                "title": "Act 4 Clean Fusion Core",
                "prompt": "Toroidal tokamak magnetic field fusion reactor generating clean infinite plasma power",
                "voiceover": "Magnetic fusion supplies continuous clean energy.",
                "telemetry": "TOKAMAK.PLASMA: 100M C"
            },
            {
                "title": "Act 5 Orbital Horizon",
                "prompt": "Deep space orbital station with solar arrays and autonomous maintenance bots",
                "voiceover": "Opening humanity's expansion across orbital space.",
                "telemetry": "ORBIT.RELAY: LOCKED"
            }
        ],
        "scene_prompts": [
            "Cinematic vertical 9:16 shot of quantum optical processor with laser beams in cryogenic chamber",
            "Vertical 9:16 macro shot of robotic titanium hand assembling micro-actuators with electrical sparks",
            "Vertical 9:16 glowing synaptic neural network visualization with hyper-fast data pulses",
            "Toroidal tokamak magnetic field fusion reactor generating clean infinite plasma power",
            "Deep space orbital station with solar arrays and autonomous maintenance bots"
        ]
    }

    # Step 1: Multi-prompt asset acquisition
    print("\n[1/3] Multi-prompt orqali Flow video va vizual aktivlarni boshqarish...")
    assets = acquire_multi_prompt_assets(
        scene_prompts=test_content_plan["scene_prompts"],
        profile_choice="4",
        aspect_ratio="9:16",
        generation_id=test_content_plan["generation_id"]
    )
    print(f"✅ Multi-prompt aktivlar soni: {assets['prompts_count']} ta sahna")

    # Step 2: Assemble creative video combining video clips & animated tech images
    print("\n[2/3] Kreativ gibrid montaj (Video kliplar + Ken Burns ilmiy rasmlari)...")
    out_dir = os.path.join(PROJECT_ROOT, f"workspace/working/{test_content_plan['generation_id']}")
    os.makedirs(out_dir, exist_ok=True)
    out_video = os.path.join(out_dir, "test_creative_hybrid.mp4")

    res = assemble_final_video(
        content_plan=test_content_plan,
        raw_video_path=assets.get("primary_video"),
        all_clips=assets.get("all_clips"),
        output_path=out_video
    )

    print(f"\n[3/3] Video QA tahlili...")
    qa = res["qa"]
    print(f"  Status: {'PASSED ✅' if qa['passed'] else 'FAILED ❌'}")
    print(f"  Video yo'li: {res['output_path']}")
    print(f"  Fayl hajmi: {os.path.getsize(res['output_path']) / (1024*1024):.2f} MB")
    print(f"  Davomiyligi: {qa['metrics']['duration']}s")
    print(f"  Ruxsat: {qa['metrics']['width']}x{qa['metrics']['height']}")
    print(f"  Qora kadrlar nisbati (Black ratio): {qa['metrics'].get('black_ratio', 0.0)}")
    print(f"  O'rtacha yorug'lik (Avg brightness): {qa['metrics'].get('avg_brightness', 0.0)}")

    if qa['passed']:
        print("\n🎉 BARCHA SINOVLAR MUVAFFAQIYATLI O'TDI! Video tayyor!")
    else:
        print(f"\n⚠️ QA Xatoliklari: {qa['errors']}")

if __name__ == "__main__":
    test_multi_prompt_pipeline()
