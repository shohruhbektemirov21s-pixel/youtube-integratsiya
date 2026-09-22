#!/usr/bin/env python3
"""
Prompt Engineering Master Architecture for Gemini & Hermes.
Transforms viral YouTube intelligence and frontier technology topics into
Hollywood-grade Google Flow (Veo AI) video prompts and ultra-high-retention scripts.

Core Principles Enforced:
1. 0-3s Irresistible Hook (Pattern Interrupt, Shocking Metric, or Curiosity Gap).
2. Google Flow (Veo AI) Cinematic Camera & Physics Directives.
3. 7 Specialized Future Technology Domains.
4. Edge-TTS Audio Cadence & Dynamic Telemetry Overlays.
5. Infinite Loop Ending & High-Conversion CTA.
"""

import os
import sys
import json
import re
import random
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime


from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.youtube_trend_explorer import YouTubeTrendExplorer, FUTURE_TECH_NICHES

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

# Blueprint Prompt Engineering Templates for Veo / Google Flow
VEO_CINEMATIC_PATTERNS = {
    "macro_actuator": (
        "Extreme macro 8k photorealistic close-up of a {entity} {action}. "
        "Sub-millimeter micro-hydraulic actuators and carbon-fiber tendons flexing with real-time hydraulic fluid pulses. "
        "Anamorphic lens flare, volumetric cyan and amber rim lighting, shallow depth of field, 60fps cinematic slow motion. "
        "--no cartoon, 3d render look, blur, watermark, low quality, artifacts"
    ),
    "cleanroom_assembly": (
        "Cinematic vertical 9:16 wide-angle shot of {entity} in a high-tech cleanroom laboratory. "
        "Robotic arms and holographic quantum circuit schematics floating in mid-air. "
        "Pristine white specular reflections on polished titanium chassis, raytraced atmospheric haze, volumetric God-rays from overhead daylight panels. "
        "--no cartoon, plastic look, blurry, watermark, distortion"
    ),
    "cyberpunk_megastructure": (
        "Epic slow orbital camera movement around {entity} set against a futuristic skyline. "
        "Pulsing bioluminescent fiber-optic conduits, neon violet and deep obsidian reflections, hyper-detailed mechanical joints moving with zero latency. "
        "Cinema-grade colour grading, chromatic aberration at edges, Octane 8k photorealism. "
        "--no animation, anime, blur, low resolution, artifacts"
    ),
    "microscopic_nanotech": (
        "Microscopic electron-microscope style photorealistic 8k visualization of {entity} {action}. "
        "Glowing sapphire molecular bonds, bio-synthetic lipid membranes self-assembling with mechanical precision. "
        "Volumetric deep-blue darkfield illumination, bioluminescent particles drifting in fluid suspension, cinematic tilt-shift. "
        "--no cartoon, low poly, grain, watermark, blur"
    )
}

HIGH_RETENTION_HOOK_FORMULAS = [
    {
        "style": "THE_SHOCKING_METRIC",
        "template": "In less than 48 hours, this {entity} did what took human engineers 10 years to solve.",
        "pacing": "Rapid, punchy delivery, instant visual impact."
    },
    {
        "style": "THE_EXISTENTIAL_WARNING",
        "template": "What engineers just uncovered inside {entity} might change human biology forever.",
        "pacing": "Deep, suspenseful, hypnotic cadence."
    },
    {
        "style": "THE_FORBIDDEN_LEAK",
        "template": "Leaked laboratory footage just revealed the secret breakthrough behind {entity}.",
        "pacing": "Urgent, confidential tone."
    },
    {
        "style": "THE_IMPOSSIBLE_DEMO",
        "template": "Watch closely: What you are seeing right now was considered mathematically impossible last year.",
        "pacing": "Pattern-interrupt silence followed by explosive revelation."
    }
]


class PromptEngineeringMaster:
    """
    Expert Prompt Engineering Engine that trains Hermes & Gemini on
    cutting-edge future technology storytelling, viral hooks, and Google Flow Veo mastery.
    """

    def __init__(self):
        self.yt_explorer = YouTubeTrendExplorer()

    def engineer_prompt_from_trend(
        self,
        topic_or_query: str,
        niche_key: Optional[str] = None,
        is_shorts: bool = True
    ) -> Dict[str, Any]:
        """
        1. Explores YouTube for top-performing viral videos on the topic.
        2. Dissects viral hooks and CTR titles.
        3. Instructs Gemini via Master Prompt Engineering to create the ultimate Veo prompt & script.
        """
        # Step 1: Discover YouTube viral baseline
        yt_intelligence = self.yt_explorer.get_full_viral_intelligence(topic_or_query, limit=3)
        top_videos = yt_intelligence.get("top_viral_videos", [])

        benchmark_titles = [v["title"] for v in top_videos[:3]]
        benchmark_views = [v["views_formatted"] for v in top_videos[:3]]
        benchmark_hooks = [v["viral_dna"]["hook_category"] for v in top_videos[:3]]

        # Step 2: Formulate the Gemini Prompt Engineering Mandate
        format_str = "YouTube Shorts (9:16 vertical, 45 seconds, 90-110 words voiceover)" if is_shorts else "YouTube Documentary (16:9 widescreen, 8-12 minutes)"
        chosen_formula = random.choice(HIGH_RETENTION_HOOK_FORMULAS)

        system_instruction = f"""
You are the World's Foremost AI Prompt Engineer & YouTube Retention Director for BeyondEra Tech (@BeyondEraTech).
Your mission is to produce an electrifying, ultra-high retention video plan based on real-world viral YouTube intelligence.

TARGET TECHNOLOGY TOPIC: {topic_or_query}
TARGET FORMAT: {format_str}

LIVE YOUTUBE VIRAL BENCHMARKS (These videos got millions of views):
- {benchmark_titles[0] if len(benchmark_titles) > 0 else 'Tesla Optimus Breakthrough'} ({benchmark_views[0] if len(benchmark_views) > 0 else '10M+ views'}) -> Hook: {benchmark_hooks[0] if len(benchmark_hooks) > 0 else 'INNOVATION'}
- {benchmark_titles[1] if len(benchmark_titles) > 1 else 'Quantum Leap 2026'} ({benchmark_views[1] if len(benchmark_views) > 1 else '4M+ views'})
- {benchmark_titles[2] if len(benchmark_titles) > 2 else 'Brain Chip Demonstration'} ({benchmark_views[2] if len(benchmark_views) > 2 else '2M+ views'})

PROMPT ENGINEERING RULES FOR GOOGLE FLOW (VEO AI):
1. Format: Vertical 9:16 aspect ratio, cinematic 8k photorealistic.
2. Camera: Explicit motion (e.g. "slow orbital pan", "extreme macro push-in", "shallow depth of field with anamorphic bokeh").
3. Subject physics: Highlight titanium carbon-fiber joints, sub-millimeter micro-hydraulics, glowing cyan synaptic conduits, raytraced subsurface reflections.
4. Lighting: Volumetric God-rays, cyberpunk amber and electric cyan rim lighting, dark obsidian cleanroom atmosphere.
5. Strict Negatives: cartoon, 3d render look, blurry, watermark, low quality, artifacts, distorted anatomy.

HIGH-RETENTION SCRIPT RULES:
1. 0-3s Hook: Must immediately grab curiosity using {chosen_formula['style']} style.
2. 3-15s: Core mechanism: Explain the jaw-dropping scientific breakthrough clearly without fluff.
3. 15-35s: Future transformation: How this rewrites the world in 2026-2030.
4. 35-45s: Loop closing sentence that links back to the beginning + punchy BeyondEra Tech CTA!
5. Word count: Strictly 90 to 110 words for 45-second pacing.

Return strictly ONE valid JSON object with the following schema:
{{
  "viral_title": "Short, explosive title under 50 characters with emoji #Shorts",
  "hook_0_3s": "The exact spoken first sentence that stops scrolling",
  "full_voiceover_script": "Complete spoken narrative (90-110 words) ready for Edge-TTS synthesis",
  "veo_flow_master_prompt": "Complete cinema-grade single master prompt for Google Flow AI (Veo)",
  "scenes": [
    {{
      "scene_num": 1,
      "timing": "0-7s",
      "flow_prompt": "Cinematic Veo visual prompt for Act 1 Hook",
      "telemetry_hud": "SYSTEM.OVERCLOCK: 120GHz | SYNC: 99.98%",
      "spoken_line": "Spoken sentence for scene 1"
    }},
    {{
      "scene_num": 2,
      "timing": "7-15s",
      "flow_prompt": "Cinematic Veo visual prompt for Act 2 Discovery",
      "telemetry_hud": "NEURAL_DEXTERITY: SUB-MILLIMETER",
      "spoken_line": "Spoken sentence for scene 2"
    }},
    {{
      "scene_num": 3,
      "timing": "15-25s",
      "flow_prompt": "Cinematic Veo visual prompt for Act 3 Demonstration",
      "telemetry_hud": "ENERGY_OUTPUT: +240% NET GAIN",
      "spoken_line": "Spoken sentence for scene 3"
    }},
    {{
      "scene_num": 4,
      "timing": "25-35s",
      "flow_prompt": "Cinematic Veo visual prompt for Act 4 Real-world Shift",
      "telemetry_hud": "TIMELINE: 2026.Q4 MASS DEPLOYMENT",
      "spoken_line": "Spoken sentence for scene 4"
    }},
    {{
      "scene_num": 5,
      "timing": "35-45s",
      "flow_prompt": "Cinematic Veo visual prompt for Act 5 Loop & Finale",
      "telemetry_hud": "STATUS: AUTONOMOUS SUPREMACY",
      "spoken_line": "Spoken sentence for scene 5"
    }}
  ],
  "audio_direction": {{
    "voice_model": "en-US-AndrewNeural",
    "voice_rate": "+2%",
    "voice_volume": "+25%",
    "music_theme": "cyberpunk_pulse_bass_drop",
    "subtitle_color": "&H00FFFF"
  }},
  "tags": ["#Shorts", "#FutureTech", "#AI", "#Robotics", "#BeyondEraTech"],
  "uzbek_summary": "Hermes Telegram boti uchun o'zbekcha qisqa professional tushuntirish: video nima haqida va nima uchun tomoshabinni ushlab qoladi"
}}
"""

        generated_plan = self._call_gemini_json(system_instruction)

        # Ensure fallback safety if API returned None
        if not generated_plan or "full_voiceover_script" not in generated_plan:
            generated_plan = self._generate_fallback_plan(topic_or_query, is_shorts)

        return {
            "topic": topic_or_query,
            "youtube_intelligence": yt_intelligence,
            "prompt_plan": generated_plan
        }

    def _call_gemini_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Invokes Gemini models with JSON mode and fallback chain."""
        models = [
            "models/gemini-3.6-flash",
            "models/gemini-3.6-flash",
            "models/gemini-3.6-flash-lite"
        ]
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GEMINI_KEY}"
            try:
                resp = requests.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "response_mime_type": "application/json",
                            "temperature": 0.7
                        }
                    },
                    timeout=30
                )
                if resp.status_code == 200:
                    cand = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                    s = cand.find("{")
                    e = cand.rfind("}")
                    if s != -1 and e != -1:
                        return json.loads(cand[s:e+1])
            except Exception as exc:
                print(f"⚠️ Gemini model {model} notice: {exc}")
        return None

    def _generate_fallback_plan(self, topic: str, is_shorts: bool) -> Dict[str, Any]:
        """Provides top-tier pre-engineered baseline if API is unreachable."""
        return {
            "viral_title": f"The Terrifying Truth Behind {topic[:25]}! 🤖 #Shorts",
            "hook_0_3s": f"What engineers just solved in {topic} will shock you.",
            "full_voiceover_script": (
                f"What engineers just solved in {topic} will shock you. "
                "In a secret test, autonomous neural networks achieved sub-millimeter precision, "
                "bypassing human dexterity for the first time in history. "
                "With zero latency and infinite endurance, this breakthrough rewrites industrial supremacy. "
                "The era of human manual limits is officially over. "
                "Subscribe to BeyondEra Tech for tomorrow's truth!"
            ),
            "veo_flow_master_prompt": (
                f"Cinematic vertical 9:16 photorealistic 8k video of {topic}. "
                "Polished titanium actuators and glowing cyan neural conduits pulsing with energy. "
                "Volumetric rim lighting, anamorphic lens flare, shallow depth of field, 60fps slow motion. "
                "--no cartoon, 3d render, watermark, blur, artifacts"
            ),
            "scenes": [
                {
                    "scene_num": 1,
                    "timing": "0-7s",
                    "flow_prompt": f"Macro photorealistic shot of {topic} activating in dark cleanroom with glowing cyan LEDs.",
                    "telemetry_hud": "SYSTEM.CALIBRATION: 99.98%",
                    "spoken_line": f"What engineers just solved in {topic} will shock you."
                },
                {
                    "scene_num": 2,
                    "timing": "7-15s",
                    "flow_prompt": f"Extreme close-up of micro-hydraulic actuators flexing with precision.",
                    "telemetry_hud": "LATENCY: 0.12ms",
                    "spoken_line": "In a secret test, autonomous neural networks achieved sub-millimeter precision."
                },
                {
                    "scene_num": 3,
                    "timing": "15-25s",
                    "flow_prompt": f"Slow orbital camera moving around {topic} operating at blinding speed.",
                    "telemetry_hud": "DEXTERITY: ZERO-SHOT",
                    "spoken_line": "bypassing human dexterity for the first time in history."
                },
                {
                    "scene_num": 4,
                    "timing": "25-35s",
                    "flow_prompt": f"Wide angle perspective of automated gigafactory illuminated by neon orange and cyan lights.",
                    "telemetry_hud": "PRODUCTION: AUTONOMOUS",
                    "spoken_line": "With zero latency and infinite endurance, this breakthrough rewrites industrial supremacy."
                },
                {
                    "scene_num": 5,
                    "timing": "35-45s",
                    "flow_prompt": f"Dramatic cinematic conclusion of {topic} eyes glowing into camera, seamless loop.",
                    "telemetry_hud": "HORIZON: BEYOND_ERA",
                    "spoken_line": "The era of human manual limits is officially over. Subscribe to BeyondEra Tech for tomorrow's truth!"
                }
            ],
            "audio_direction": {
                "voice_model": "en-US-AndrewNeural",
                "voice_rate": "+2%",
                "voice_volume": "+25%",
                "music_theme": "cyberpunk_pulse_bass_drop",
                "subtitle_color": "&H00FFFF"
            },
            "tags": ["#Shorts", "#FutureTech", "#Robotics", "#AI", "#BeyondEraTech"],
            "uzbek_summary": f"Video {topic} bo'yicha eng so'nggi shov-shuvli yutuqni ko'rsatadi. 0-3s hook tomoshabinni ushlaydi, neon subtitrlar va baland inglizcha ovoz 100% retention beradi."
        }


if __name__ == "__main__":
    master = PromptEngineeringMaster()
    print("Testing Prompt Engineering Master with live YouTube trend integration...")
    plan = master.engineer_prompt_from_trend("humanoid robot dexterous manipulation", is_shorts=True)
    print("\n" + "=" * 65)
    print("🎬 MASTER PROMPT PLAN GENERATED")
    print("=" * 65)
    p = plan["prompt_plan"]
    print(f"📌 TITLE: {p.get('viral_title')}")
    print(f"🔥 HOOK (0-3s): {p.get('hook_0_3s')}")
    print(f"🎙️ SCRIPT ({len(p.get('full_voiceover_script','').split())} words):")
    print(f"   {p.get('full_voiceover_script')}")
    print(f"\n🎥 VEO MASTER PROMPT:")
    print(f"   {p.get('veo_flow_master_prompt')}")
    print(f"\n🇺🇿 UZBEK DOSSIER:\n   {p.get('uzbek_summary')}")
