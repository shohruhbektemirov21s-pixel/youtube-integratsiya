#!/usr/bin/env python3
"""
BeyondEra Tech - Autonomous Content Plan Engine.
Generates comprehensive, high-retention content plans using Gemini 3.6/3.8 Flash.
Enforces:
1. Strict Single-Niche Rules (AI, Robotics, Future Tech, AGI, Quantum, Neuralink).
2. 10-day Cadence Engine (9 days: 30-60s Shorts; 10th day: 8-12 min Documentary).
3. Full Scene Breakdown with detailed Google Flow prompts and synchronized voiceover.
4. Database persistence into VideoGenerationTask & ScheduledUpload.
"""

import os
import sys
import json
import time
import re
import datetime
import subprocess
import requests
from typing import Dict, Any, Tuple, Optional


from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
if not GEMINI_KEY:
    print("⚠️ GEMINI_API_KEY muhit o'zgaruvchisi o'rnatilmagan. Zaxira reja ishlatiladi.")
BEYOND_ERA_CHANNEL_ID = "UC525J1r4HA1qV8DVf6FKQEg"

# Allowed Niche Keywords for BeyondEra Tech
ALLOWED_NICHE_KEYWORDS = [
    "artificial intelligence", "ai", "humanoid", "robot", "robotics",
    "agi", "quantum computing", "quantum", "neuralink", "brain-computer",
    "fusion energy", "future tech", "future computing", "emerging technology",
    "autonomous", "physical ai", "cybernetics", "bipedal", "tesla optimus",
    "figure 02", "boston dynamics", "deepseek", "generative ai", "singularity",
    "supercomputer", "nanotechnology", "megaproject", "space propulsion"
]

FORBIDDEN_KEYWORDS = [
    "recipe", "cooking", "minecraft", "fortnite", "gameplay walkthrough",
    "makeup", "beauty salon", "celebrity gossip", "prank", "vlog day in life",
    "crypto trading signals", "forex broker", "weight loss diet", "casino"
]


def validate_niche(topic: str, script_or_summary: str = "") -> Tuple[bool, str]:
    """
    Strictly validates that the topic belongs to BeyondEra Tech's single niche.
    Returns (is_valid, message).
    """
    text = f"{topic} {script_or_summary}".lower()

    for forbidden in FORBIDDEN_KEYWORDS:
        if forbidden in text:
            return False, f"Mavzu taqiqlangan yo'nalishga tushdi: '{forbidden}'"

    matches = [kw for kw in ALLOWED_NICHE_KEYWORDS if kw in text]
    if not matches:
        return False, "Mavzu BeyondEra Tech asosiy niche'iga (AI, Robotics, Future Tech) mos kelmadi."

    return True, f"Niche tekshiruvidan muvaffaqiyatli o'tdi (Mos kalit so'zlar: {', '.join(matches[:3])})"


def fetch_future_tech_news(topic_hint: Optional[str] = None) -> list:
    """Fetch live tech breakthroughs from Google News RSS."""
    import urllib.request
    import urllib.parse
    import xml.etree.ElementTree as ET

    search = f"breakthrough {topic_hint}" if topic_hint else "humanoid robot physical AI quantum 2026"
    url = f"https://news.google.com/rss/search?q={urllib.parse.quote(search)}&hl=en-US&gl=US&ceid=US:en"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    headlines = []
    try:
        xml_data = urllib.request.urlopen(req, timeout=6).read()
        root = ET.fromstring(xml_data)
        for item in root.findall(".//item")[:4]:
            t = item.find("title")
            if t is not None and t.text:
                headlines.append(t.text.strip())
    except Exception:
        headlines = [
            "Next-Gen Humanoid Robots reach mass gigafactory production line milestones",
            "Quantum processors demonstrate material synthesis breakthroughs",
            "Physical AI foundation models achieve zero-shot manipulation dexterity"
        ]
    return headlines


def get_cadence_status() -> Dict[str, Any]:
    """
    Checks PostgreSQL to calculate days since last 10-day long documentary.
    Rule: 1 long-form documentary every 10 days; all other days are 30-60s Shorts.
    """
    cmd = [
        "docker", "exec", "-i", "youtube_integratsiya_backend",
        "python", "manage.py", "shell", "-c",
        f"""
import json
from django.apps import apps
from django.utils import timezone

ScheduledUpload = apps.get_model('youtube', 'ScheduledUpload')
YouTubeChannel = apps.get_model('youtube', 'YouTubeChannel')

ch = YouTubeChannel.objects.filter(channel_id='{BEYOND_ERA_CHANNEL_ID}').first() or YouTubeChannel.objects.first()

long_uploads = ScheduledUpload.objects.filter(channel=ch).order_by('-scheduled_date')
last_long = None
for u in long_uploads:
    t_str = str(u.tags) if u.tags else ''
    d_str = str(u.description) if u.description else ''
    if 'LongForm' in t_str or 'Documentary' in t_str or 'Chapters' in d_str:
        last_long = u
        break

today = timezone.now().date()
if last_long:
    diff = (today - last_long.scheduled_date).days
    data = {{
        'exists': True,
        'last_date': str(last_long.scheduled_date),
        'days_since': diff,
        'days_until': max(0, 10 - diff),
        'should_be_long': diff >= 10,
        'title': last_long.title
    }}
else:
    data = {{
        'exists': False,
        'last_date': None,
        'days_since': 999,
        'days_until': 0,
        'should_be_long': True,
        'title': None
    }}
print('CADENCE_JSON:' + json.dumps(data))
"""
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
        for line in proc.stdout.splitlines():
            if line.startswith("CADENCE_JSON:"):
                return json.loads(line.replace("CADENCE_JSON:", "").strip())
    except Exception as e:
        print(f"⚠️ Cadence holatini tekshirishda ogohlantirish: {e}")

    return {
        "exists": False,
        "last_date": None,
        "days_since": 999,
        "days_until": 0,
        "should_be_long": True,
        "title": None
    }


DIVERSE_TECH_DOMAINS = [
    {
        "domain": "Humanoid Robotics & Sub-Millimeter Dexterity",
        "hint": "Tesla Optimus Gen-3 micro-assembly and Figure 02 neural manipulation breakthrough",
        "theme": "CYBERPUNK_NEON",
        "primary_hex": "0x00f0ff",
        "accent_hex": "0xff0055",
        "voice_name": "en-US-ChristopherNeural",
        "music_profile": "cyber_pulse",
        "subtitle_color": "&H00FFFF",
        "hook_style": "SHOCKING_METRIC"
    },
    {
        "domain": "Quantum Supremacy & Optical Silicon Photonics",
        "hint": "Majorana zero-modes room temperature quantum chip decoding petaflop calculations in picoseconds",
        "theme": "QUANTUM_GOLD",
        "primary_hex": "0xffd700",
        "accent_hex": "0xffaa00",
        "voice_name": "en-US-BrianNeural",
        "music_profile": "quantum_suspense",
        "subtitle_color": "&H00D7FF",
        "hook_style": "CONTRARIAN_QUESTION"
    },
    {
        "domain": "Neuralink & Direct Cortical Telepathy",
        "hint": "Brain-computer interface decoding synthetic inner monologue with 16000 bio-electrodes",
        "theme": "ELECTRIC_VIOLET",
        "primary_hex": "0xc084fc",
        "accent_hex": "0x38bdf8",
        "voice_name": "en-US-EricNeural",
        "music_profile": "ambient_flow_synth",
        "subtitle_color": "&H00E5FF",
        "hook_style": "MIND_BENDING_DEMO"
    },
    {
        "domain": "AGI Superintelligence & Self-Recursive Coding",
        "hint": "Autonomous AI reasoning engine autonomously discovering new physics algorithms overnight",
        "theme": "MATRIX_EMERALD",
        "primary_hex": "0x10b981",
        "accent_hex": "0x06b6d4",
        "voice_name": "en-US-GuyNeural",
        "music_profile": "cyber_pulse",
        "subtitle_color": "&H00FF66",
        "hook_style": "LEAKED_BREAKTHROUGH"
    },
    {
        "domain": "Autonomous Space Robotics & Orbital Megastructures",
        "hint": "AI-guided humanoid rovers constructing self-sustaining orbital solar lattices on the Moon",
        "theme": "COSMIC_DEEP",
        "primary_hex": "0x38bdf8",
        "accent_hex": "0x818cf8",
        "voice_name": "en-GB-RyanNeural",
        "music_profile": "epic_uplifting",
        "subtitle_color": "&H00FFFFFF",
        "hook_style": "URGENT_TIMELINE"
    },
    {
        "domain": "Micro-Fusion & Infinite Clean Power for AI Megaclusters",
        "hint": "Compact magnetic confinement fusion reactor generating net energy to power 100000 GPU AI cluster",
        "theme": "CRIMSON_PLASMA",
        "primary_hex": "0xff4444",
        "accent_hex": "0xff9900",
        "voice_name": "en-US-ChristopherNeural",
        "music_profile": "quantum_suspense",
        "subtitle_color": "&H0055FF",
        "hook_style": "SHOCKING_METRIC"
    }
]

PLAN_30_DAYS_FILE = os.path.join(PROJECT_ROOT, "assets/content_plan_30_days.json")
STATE_30_DAYS_FILE = os.path.join(PROJECT_ROOT, "assets/30_day_state.json")


def get_30_day_plan_entry(day_number: int) -> Optional[Dict[str, Any]]:
    """Loads specific day entry (1 to 30) from assets/content_plan_30_days.json."""
    if not os.path.exists(PLAN_30_DAYS_FILE):
        return None
    try:
        with open(PLAN_30_DAYS_FILE, "r", encoding="utf-8") as f:
            days = json.load(f)
        for d in days:
            if d.get("day") == day_number:
                return d
    except Exception as e:
        print(f"⚠️ 30-kunlik rejani o'qishda ogohlantirish: {e}")
    return None


import uuid
from scripts.content_history_manager import (
    ContentHistoryManager, compute_sha256_text
)

try:
    from scripts.youtube_channel_intelligence import YouTubeChannelIntelligence
    _intel_available = True
except ImportError:
    _intel_available = False

def get_current_30_day_progress() -> int:
    """Returns the current active day (1 to 30) from the state tracker."""
    if os.path.exists(STATE_30_DAYS_FILE):
        try:
            with open(STATE_30_DAYS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                last_completed = data.get("last_completed_day", 0)
                next_day = (last_completed % 30) + 1
                return next_day
        except Exception:
            pass
    return 1


def advance_30_day_progress(completed_day: int):
    """Saves the completed day number into assets/30_day_state.json."""
    state = {
        "last_completed_day": completed_day,
        "updated_at": str(datetime.datetime.now()),
        "next_day": (completed_day % 30) + 1
    }
    with open(STATE_30_DAYS_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    print(f"📌 [30-KUNLIK REJA] {completed_day}-kun muvaffaqiyatli yakunlandi! Keyingi reja: {state['next_day']}-kun.")


history_manager = ContentHistoryManager()


def get_next_pending_plan_entry() -> Optional[Dict[str, Any]]:
    """
    Finds the next un-executed ('pending') topic from the 30-day master plan.
    Enforces that completed topics are NEVER picked again.
    Checks semantic duplication with prior published content.
    If a pending topic is semantically duplicate with history, marks it as 'skipped_duplicate' and checks next.
    """
    if not os.path.exists(PLAN_30_DAYS_FILE):
        return None
    try:
        with open(PLAN_30_DAYS_FILE, "r", encoding="utf-8") as f:
            days = json.load(f)

        dirty = False
        selected_entry = None
        for d in days:
            if d.get("status") == "pending":
                t_title = d.get("title", "")
                t_topic = d.get("topic", t_title)
                
                # Check semantic duplicate against content history
                is_dup, dup_rec, sim_score = history_manager.is_topic_duplicate(t_topic, threshold=0.55)
                if is_dup:
                    print(f"⚠️ [CONTENT PLAN] Day {d.get('day')} ('{t_topic}') skipped due to semantic similarity ({sim_score:.2f}) with '{dup_rec.get('topic')}'. Marking skipped_duplicate.")
                    d["status"] = "skipped_duplicate"
                    d["duplicate_similarity"] = sim_score
                    dirty = True
                    continue
                
                d["status"] = "generating"
                selected_entry = d
                dirty = True
                break

        if dirty:
            with open(PLAN_30_DAYS_FILE, "w", encoding="utf-8") as f:
                json.dump(days, f, indent=2, ensure_ascii=False)

        return selected_entry
    except Exception as e:
        print(f"⚠️ Error finding pending plan entry: {e}")
        return None


def mark_plan_entry_completed(day_number: int, video_id: Optional[str] = None, video_hash: Optional[str] = None):
    """Marks a day in the 30-day master plan as completed."""
    if not os.path.exists(PLAN_30_DAYS_FILE):
        return
    try:
        with open(PLAN_30_DAYS_FILE, "r", encoding="utf-8") as f:
            days = json.load(f)
        for d in days:
            if d.get("day") == day_number:
                d["status"] = "completed"
                d["completed_at"] = datetime.datetime.now().isoformat()
                if video_id:
                    d["generated_video_id"] = video_id
                if video_hash:
                    d["video_hash"] = video_hash
                break
        with open(PLAN_30_DAYS_FILE, "w", encoding="utf-8") as f:
            json.dump(days, f, indent=2, ensure_ascii=False)
        advance_30_day_progress(day_number)
    except Exception as e:
        print(f"⚠️ Error marking plan entry completed: {e}")


def mark_plan_entry_failed(day_number: int, error_msg: str):
    """Marks a day in the 30-day master plan as failed."""
    if not os.path.exists(PLAN_30_DAYS_FILE):
        return
    try:
        with open(PLAN_30_DAYS_FILE, "r", encoding="utf-8") as f:
            days = json.load(f)
        for d in days:
            if d.get("day") == day_number:
                d["status"] = "failed"
                d["error"] = error_msg
                break
        with open(PLAN_30_DAYS_FILE, "w", encoding="utf-8") as f:
            json.dump(days, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Error marking plan entry failed: {e}")


def generate_content_plan(
    video_type: str = "auto",
    topic_hint: Optional[str] = None,
    day_number: Optional[int] = None,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Generates a complete production Content Plan via Gemini 3.6/3.8 Flash.
    Strictly follows the official BeyondEra Tech 30-Day Master Content Plan.
    Enforces pending-topic selection, semantic deduplication, and unique Generation ID.
    """
    import random
    import logging
    logger = logging.getLogger("ContentPlanEngine")

    generation_id = str(uuid.uuid4())

    # Determine day entry from 30-day master roadmap
    day_entry = None
    if day_number is not None:
        day_entry = get_30_day_plan_entry(day_number)
    elif topic_hint is None:
        # Pick next pending entry that is not duplicate
        day_entry = get_next_pending_plan_entry()
        if day_entry:
            day_number = day_entry.get("day")

    if day_entry:
        actual_type = day_entry.get("video_type", "shorts")
        target_duration = day_entry.get("duration", 45 if actual_type == "shorts" else 600)
        effective_title = day_entry["title"]
        effective_hook = day_entry["hook"]
        effective_prompt_basis = day_entry["prompt_basis"]
        effective_cliffhanger = day_entry["cliffhanger"]
        effective_cta = day_entry["cta"]
        effective_flow_prompt = day_entry["video_prompt"]
        selected_domain = random.choice(DIVERSE_TECH_DOMAINS)
    else:
        cadence = get_cadence_status()
        if video_type == "auto":
            actual_type = "long" if cadence.get("should_be_long", False) else "shorts"
        else:
            actual_type = video_type
        target_duration = 45 if actual_type == "shorts" else 600
        selected_domain = random.choice(DIVERSE_TECH_DOMAINS)
        effective_title = topic_hint or selected_domain["hint"]
        effective_hook = ""
        effective_prompt_basis = selected_domain["hint"]
        effective_cliffhanger = "Keyingi qismda yanada chuqurroq tahlil."
        effective_cta = "BeyondEra Tech kanaliga obuna bo'ling."
        effective_flow_prompt = selected_domain["hint"]


    news = fetch_future_tech_news(effective_title)
    
    # Integrate YouTube Channel Intelligence for market-driven content
    intel_context = ""
    if _intel_available and not day_entry:
        try:
            intel = YouTubeChannelIntelligence()
            today_idea = intel.get_todays_content_idea(day_index=random.randint(0, 4))
            if today_idea:
                # Use intelligence-driven content instead of random domain
                effective_title = today_idea.get("topic", effective_title)
                effective_hook = today_idea.get("hook", effective_hook)
                effective_prompt_basis = today_idea.get("topic", effective_prompt_basis)
                if today_idea.get("script"):
                    intel_context = (
                        f"\nMARKET INTELLIGENCE (from competitor analysis):\n"
                        f"- Recommended Topic: {today_idea.get('topic')}\n"
                        f"- Recommended Hook: {today_idea.get('hook')}\n"
                        f"- Recommended Script: {today_idea.get('script')}\n"
                        f"- Visual Style: {today_idea.get('visual_style', '')}\n"
                        f"- Competitor Pattern: {today_idea.get('competitor_inspired_by', 'Original')}\n"
                    )
                if today_idea.get("scene_prompts"):
                    effective_flow_prompt = today_idea["scene_prompts"][0]
                if today_idea.get("voice_model"):
                    selected_domain = dict(selected_domain)  # Make mutable copy
                    selected_domain["voice_name"] = today_idea["voice_model"]
                if today_idea.get("music_profile"):
                    selected_domain["music_profile"] = today_idea["music_profile"]
                logger.info(f"🧠 [INTELLIGENCE] Using market-driven content: '{effective_title}'")
        except Exception as e:
            logger.warning(f"Intelligence integration warning: {e}")
    is_shorts = (actual_type == "shorts")
    format_desc = (
        "YouTube Shorts (strictly 30-60s, 9:16 vertical 1080x1920, 60fps, 85-115 words voiceover, loop ending)"
        if is_shorts else
        "YouTube Long-Form Documentary (8-12 minutes, 16:9 1920x1080, 6 chapters with timestamps, cold open)"
    )

    day_context = ""
    if day_entry:
        day_context = (
            f"OFFICIAL 30-DAY MASTER ROADMAP — DAY {day_number}/30:\n"
            f"- EPISODE TITLE: {effective_title}\n"
            f"- REQUIRED HOOK: {effective_hook}\n"
            f"- SCENARIO BASIS: {effective_prompt_basis}\n"
            f"- REQUIRED CLIFFHANGER: {effective_cliffhanger}\n"
            f"- CALL TO ACTION (CTA): {effective_cta}\n"
            f"- FLOW AI SEED PROMPT: {effective_flow_prompt}\n\n"
        )

    system_prompt = (
        "You are the Senior Executive Creative Director & Retention Architect for BeyondEra Tech (@BeyondEraTech).\n"
        "NICHE RULE: High-RPM Science & Future Technology strictly focused on frontier breakthroughs.\n"
        f"{day_context}"
        f"TARGET DOMAIN: {selected_domain['domain']}\n"
        f"TARGET FORMAT: {format_desc}\n"
        f"TOPIC CONTEXT: {effective_title}\n"
        f"CONTEXT NEWS: {json.dumps(news)}\n"
        f"{intel_context}\n"
        "CREATIVE DIVERSITY & STORYTELLING MANDATE:\n"
        "Create an electrifying, ultra-high retention episode strictly fulfilling the official roadmap topic, hook, cliffhanger, and CTA.\n"
        "Return strictly ONE valid JSON object with these EXACT keys:\n"
        "{\n"
        f'  "day_number": {day_number if day_number else "null"},\n'
        f'  "topic": "{effective_title}",\n'
        f'  "target_audience": "Tech enthusiasts, AI researchers, engineers, global future-tech audience",\n'
        f'  "video_type": "{actual_type}",\n'
        f'  "duration": {target_duration},\n'
        f'  "hook": "{effective_hook or "Instant 0-3s pattern-interrupt opening sentence"}",\n'
        f'  "script": "Full spoken narrative script (90-110 words for shorts, comprehensive for long) naturally integrating the hook and ending with the cliffhanger and CTA",\n'
        f'  "creative_direction": {{\n'
        f'    "visual_theme": "{selected_domain["theme"]}",\n'
        f'    "primary_hex": "{selected_domain["primary_hex"]}",\n'
        f'    "accent_hex": "{selected_domain["accent_hex"]}",\n'
        f'    "voice_name": "{selected_domain["voice_name"]}",\n'
        f'    "voice_rate": "+3%",\n'
        f'    "music_profile": "{selected_domain["music_profile"]}",\n'
        f'    "subtitle_color": "{selected_domain["subtitle_color"]}",\n'
        f'    "hook_style": "{selected_domain["hook_style"]}"\n'
        f'  }},\n'
        f'  "cliffhanger": "{effective_cliffhanger}",\n'
        f'  "cta": "{effective_cta}",\n'
        f'  "scenes": [\n'
        f'    {{\n'
        f'      "scene": 1,\n'
        f'      "duration": 7,\n'
        f'      "title": "Act 1 Hook Headline",\n'
        f'      "prompt": "Vivid cinematic photorealistic prompt for Google Flow AI with volumetric lighting, 8k textures, shallow depth of field",\n'
        f'      "telemetry": "SYSTEM.CALIBRATION: 99.98% | LATENCY: 0.14ms",\n'
        f'      "motion_type": "zoom_in",\n'
        f'      "voiceover": "First spoken sentence of hook"\n'
        f'    }},\n'
        f'    {{\n'
        f'      "scene": 2,\n'
        f'      "duration": 8,\n'
        f'      "title": "Act 2 The Discovery",\n'
        f'      "prompt": "Detailed cinematic Flow prompt showing internal mechanisms / sensors / quantum chips",\n'
        f'      "telemetry": "SYNAPTIC BANDWIDTH: 4.8 TB/s",\n'
        f'      "motion_type": "pan_left",\n'
        f'      "voiceover": "Second spoken sentence"\n'
        f'    }},\n'
        f'    {{\n'
        f'      "scene": 3,\n'
        f'      "duration": 8,\n'
        f'      "title": "Act 3 The Demonstration",\n'
        f'      "prompt": "Macro photorealistic shot of high speed actuation or computation",\n'
        f'      "telemetry": "ACTUATOR SPEED: 480 deg/s",\n'
        f'      "motion_type": "zoom_out",\n'
        f'      "voiceover": "Third spoken sentence"\n'
        f'    }},\n'
        f'    {{\n'
        f'      "scene": 4,\n'
        f'      "duration": 8,\n'
        f'      "title": "Act 4 The Breakthrough",\n'
        f'      "prompt": "Cinematic wide angle shot of the complete robotic / quantum system operating",\n'
        f'      "telemetry": "QUANTUM COHERENCE: 100.0%",\n'
        f'      "motion_type": "pan_right",\n'
        f'      "voiceover": "Fourth spoken sentence"\n'
        f'    }},\n'
        f'    {{\n'
        f'      "scene": 5,\n'
        f'      "duration": 8,\n'
        f'      "title": "Act 5 What Comes Next",\n'
        f'      "prompt": "Futuristic cleanroom or gigafactory perspective with glowing optical signals",\n'
        f'      "telemetry": "HORIZON PROJECTION: 2026.Q4",\n'
        f'      "motion_type": "zoom_in",\n'
        f'      "voiceover": "Fifth spoken sentence"\n'
        f'    }},\n'
        f'    {{\n'
        f'      "scene": 6,\n'
        f'      "duration": 7,\n'
        f'      "title": "Act 6 Loop Closing",\n'
        f'      "prompt": "Seamless cinematic conclusion looping back to the opening motif",\n'
        f'      "telemetry": "SYNCHRONIZATION: COMPLETE",\n'
        f'      "motion_type": "zoom_out",\n'
        f'      "voiceover": "Final loop sentence"\n'
        f'    }}\n'
        f'  ],\n'
        f'  "scene_prompts": ["Prompt 1", "Prompt 2", "Prompt 3", "Prompt 4", "Prompt 5", "Prompt 6"],\n'
        f'  "voiceover_text": "Complete voiceover script ready for Edge-TTS synthesis",\n'
        f'  "title": "{"Viral Shocking Title Under 50 Chars! 🤖 #Shorts" if is_shorts else "Compelling Documentary Title Under 60 Chars 🌐"}",\n'
        f'  "description": "Optimized description with timestamps, tags and social CTA",\n'
        f'  "tags": ["Shorts", "FutureTech", "AI", "Robotics", "BeyondEraTech"],\n'
        f'  "hashtags": ["#Shorts", "#FutureTech", "#AI", "#Robotics"],\n'
        f'  "cta": "Subscribe to BeyondEra Tech for daily frontier breakthroughs",\n'
        f'  "thumbnail_concept": "High CTR visual concept description",\n'
        f'  "visual_style": "Cinematic photorealistic 8k, anamorphic lens flares, dynamic lighting",\n'
        f'  "negative_prompts": "cartoon, 3D render look, blur, artifacts, text overlay, watermark",\n'
        f'  "seo_keywords": ["AI breakthrough 2026", "humanoid robot", "BeyondEra Tech"],\n'
        f'  "uzbek_analysis": "O\'zbekcha professional tahlil: video qanday qilib tomoshabinni ushlab qoladi va yuqori retention beradi",\n'
        f'  "uzbek_voice_summary": "Telegram ovozli xabar uchun lo\'nda o\'zbekcha hisobot"\n'
        "}"
    )

    models_to_try = [
        "models/gemini-3.6-flash",
        "models/gemini-3.6-flash",
        "models/gemini-3.6-flash-lite"
    ]

    for attempt in range(max_retries):
        for model in models_to_try:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GEMINI_KEY}"
            try:
                res = requests.post(
                    endpoint,
                    json={
                        "contents": [{"parts": [{"text": system_prompt}]}],
                        "generationConfig": {"response_mime_type": "application/json"}
                    },
                    timeout=30
                )
                if res.status_code == 200:
                    text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    s = text.find("{")
                    e = text.rfind("}")
                    if s != -1 and e != -1:
                        data = json.loads(text[s:e+1])
                        # Niche Validation
                        is_valid, msg = validate_niche(data.get("topic", ""), data.get("script", ""))
                        if not is_valid:
                            print(f"⚠️ [REJECTED] {msg} -> Yangi mavzu bilan qayta urinilmoqda...")
                            continue

                        # Ensure consistent types, scenes, and creative direction
                        data["video_type"] = actual_type
                        data["duration"] = target_duration
                        if day_number:
                            data["day_number"] = day_number
                            data["cliffhanger"] = effective_cliffhanger
                            data["cta"] = effective_cta

                        if not data.get("creative_direction"):
                            data["creative_direction"] = {
                                "visual_theme": selected_domain["theme"],
                                "primary_hex": selected_domain["primary_hex"],
                                "accent_hex": selected_domain["accent_hex"],
                                "voice_name": selected_domain["voice_name"],
                                "voice_rate": "+3%",
                                "music_profile": selected_domain["music_profile"],
                                "subtitle_color": selected_domain["subtitle_color"],
                                "hook_style": selected_domain["hook_style"]
                            }
                        if not data.get("scene_prompts") and data.get("scenes"):
                            data["scene_prompts"] = [sc.get("prompt", "") for sc in data["scenes"]]
                        if not data.get("voiceover_text"):
                            data["voiceover_text"] = data.get("script", "")

                        day_tag = f" [KUN {day_number}/30]" if day_number else ""
                        print(f"✅ [CONTENT PLAN ENGINE] Kontent reja tayyorlandi{day_tag}: '{data.get('title')}'")
                        print(f"🎨 [CREATIVE DIRECTION] Mavzu: {selected_domain['domain']} | Uslub: {data['creative_direction'].get('visual_theme')} | Ovoz: {data['creative_direction'].get('voice_name')} | Musiqa: {data['creative_direction'].get('music_profile')}")

                        # Inject Generation Tracking & Hashes
                        data["generation_id"] = generation_id
                        data["topic_hash"] = compute_sha256_text(data.get("topic", ""))
                        data["script_hash"] = compute_sha256_text(data.get("script", "") or data.get("voiceover_text", ""))
                        primary_prompt = (data.get("scene_prompts", [""])[0] if data.get("scene_prompts") else "") or (data.get("scenes", [{}])[0].get("prompt", ""))
                        data["prompt_hash"] = compute_sha256_text(primary_prompt)

                        return data
            except Exception as exc:
                print(f"Model {model} xatosi: {exc}")
                continue

    # Fallback to high-quality pre-validated content plan
    print("⚠️ Gemini API javob bermadi, yuqori sifatli zaxira reja ishga tushirilmoqda...")
    if is_shorts:
        return {
            "topic": topic_hint or "Tesla Optimus Gen-3 Micro-Assembly Breakthrough",
            "target_audience": "Tech enthusiasts, AI researchers, global YouTube audience",
            "video_type": "shorts",
            "duration": 45,
            "hook": "You won't believe what Tesla's humanoid robot just pulled off in secret.",
            "script": "You won't believe what Tesla's humanoid robot just pulled off in secret. Inside the Fremont Gigafactory, engineers gave Optimus Gen-3 zero training data—only a single video demonstration. Within twenty minutes, its neural network calibrated millimeter-precise micro-assembly of battery cells, moving at double human speed without a single error. While the world debates whether robotics will take years, the physical AI inflection point just arrived. And what makes this truly terrifying is that...",
            "scenes": [
                {
                    "scene": 1,
                    "duration": 12,
                    "title": "The Secret Awakening",
                    "prompt": "Cinematic vertical 9:16 8k photorealistic close-up of sleek matte-black humanoid robot fingers delicately aligning micro-battery cells in cleanroom, volumetric blue laser lighting, kinetic push-in, shallow depth of field, Unreal Engine 5 realism",
                    "voiceover": "You won't believe what Tesla's humanoid robot just pulled off in secret."
                },
                {
                    "scene": 2,
                    "duration": 12,
                    "title": "Zero Training Calibration",
                    "prompt": "Vertical 9:16 photorealistic shot of humanoid robot standing in Tesla gigafactory floor, glowing cyan optical sensors scanning worktable, high-speed fluid mechanical movements, cinematic anamorphic lens flares",
                    "voiceover": "Inside the Fremont Gigafactory, engineers gave Optimus Gen-3 zero training data—only a single video demonstration."
                },
                {
                    "scene": 3,
                    "duration": 11,
                    "title": "Double Human Speed",
                    "prompt": "Vertical 9:16 macro shot of titanium robot hand executing lightning-fast micro-welding with precision sparks, cinematic motion blur, volumetric steam, 60fps high shutter speed",
                    "voiceover": "Within twenty minutes, its neural network calibrated millimeter-precise micro-assembly, moving at double human speed."
                },
                {
                    "scene": 4,
                    "duration": 10,
                    "title": "The Infinite Loop",
                    "prompt": "Vertical 9:16 wide dramatic tracking shot of dozens of humanoid robots working continuously under neon industrial lights, cinematic cybernetic atmosphere, hyper-realistic reflections",
                    "voiceover": "While the world debates timelines, the physical AI inflection point just happened. And what makes this truly terrifying is that..."
                }
            ],
            "scene_prompts": [
                "Cinematic vertical 9:16 8k photorealistic close-up of sleek matte-black humanoid robot fingers delicately aligning micro-battery cells in cleanroom, volumetric blue laser lighting, kinetic push-in",
                "Vertical 9:16 photorealistic shot of humanoid robot standing in Tesla gigafactory floor, glowing cyan optical sensors scanning worktable, high-speed fluid mechanical movements",
                "Vertical 9:16 macro shot of titanium robot hand executing lightning-fast micro-welding with precision sparks, cinematic motion blur, volumetric steam",
                "Vertical 9:16 wide dramatic tracking shot of dozens of humanoid robots working continuously under neon industrial lights, cinematic cybernetic atmosphere"
            ],
            "voiceover_text": "You won't believe what Tesla's humanoid robot just pulled off in secret. Inside the Fremont Gigafactory, engineers gave Optimus Gen-3 zero training data—only a single video demonstration. Within twenty minutes, its neural network calibrated millimeter-precise micro-assembly of battery cells, moving at double human speed without a single error. While the world debates whether robotics will take years, the physical AI inflection point just arrived. And what makes this truly terrifying is that...",
            "title": "🤖 Tesla Optimus Just Broke Physics! #Shorts",
            "description": "Tesla Optimus Gen 3 just accomplished the impossible inside the Gigafactory without prior training data. The physical AI inflection point is officially here.\n\nSubscribe to BeyondEra Tech for daily breakthrough robotics!\n\n#Shorts #BeyondEraTech #TeslaOptimus #HumanoidRobots #AI #FutureTech",
            "tags": ["Shorts", "TeslaOptimus", "HumanoidRobots", "FutureTech", "BeyondEraTech", "AI2026", "Robotics"],
            "hashtags": ["#Shorts", "#TeslaOptimus", "#FutureTech", "#AI"],
            "cta": "Subscribe to BeyondEra Tech for daily breakthroughs in frontier robotics.",
            "thumbnail_concept": "High contrast close-up of glowing cyan optical robot eye reflecting gigafactory lights",
            "visual_style": "Cinematic photorealistic 8k, Unreal Engine 5, volumetric lighting, cyan cybernetic glow",
            "negative_prompts": "cartoon, 3d render, blurry, distorted anatomy, watermark, text overlay",
            "seo_keywords": ["Tesla Optimus Gen 3", "humanoid robotics 2026", "physical AI", "BeyondEra Tech"],
            "uzbek_analysis": "Ushbu Short 45 soniyaga qat'iy moslangan. Dastlabki 3 soniyada tomoshabin to'xtatiladi, 25-soniyadagi burilish orqali qiziqish oshiriladi va loop orqali 110%+ takroriy tomosha ta'minlanadi.",
            "uzbek_voice_summary": "BeyondEra Tech kanali uchun 45 soniyali yuqori sifatli vertikal Short rejalashtirildi. Mavzu: Tesla Optimus robotining yangi yutug'i. Video avtomatik loop ulanishi bilan tayyorlandi."
        }
    else:
        return {
            "topic": topic_hint or "The AGI & Humanoid Robotics Timeline: 2026-2030 In-Depth Documentary",
            "target_audience": "Tech executives, engineers, global future-tech documentary viewers",
            "video_type": "long",
            "duration": 600,
            "hook": "By 2030, the nature of human labor will be transformed forever. In this documentary breakdown, we enter the classified laboratories building the physical intelligence revolution.",
            "script": "By 2030, human labor will be transformed forever. In this 10-minute documentary breakdown, we go inside the classified laboratories reshaping the future of human society.",
            "scenes": [
                {
                    "scene": 1,
                    "duration": 60,
                    "title": "The Silent Revolution",
                    "prompt": "Cinematic 16:9 widescreen 8k IMAX style shot of automated gigafactory cleanroom with dozens of humanoid robots working alongside high-tech conveyor belts, dramatic lens flares, anamorphic bokeh, volumetric lighting",
                    "voiceover": "Human civilization stands at the precipice of an intelligence revolution."
                }
            ],
            "scene_prompts": [
                "Cinematic 16:9 widescreen 8k IMAX style shot of automated gigafactory cleanroom with dozens of humanoid robots working alongside high-tech conveyor belts, dramatic lens flares, anamorphic bokeh, volumetric lighting"
            ],
            "voiceover_text": "By 2030, the nature of human labor will be transformed forever. Welcome to the BeyondEra Tech documentary investigation.",
            "title": "🤖 How Humanoid Robots Will Reshape Civilization (2026-2030) 🌐",
            "description": "The humanoid robotics revolution is accelerating beyond what experts predicted. In this comprehensive documentary, BeyondEra Tech breaks down the real technological race happening right now.\n\nChapters:\n0:00 - The Silent Revolution Begins\n1:40 - Tesla vs Boston Dynamics: The Titan Duel\n4:15 - The Brain Problem: Why Physical AI Was Impossible\n6:30 - The Breakthrough That Solved It All\n8:20 - The 2030 Workforce Disruption\n9:40 - The Human Verdict & What Comes Next\n\n🔔 Subscribe to BeyondEra Tech for daily breakthroughs in frontier science & technology!",
            "tags": ["Documentary", "LongForm", "10DayCadence", "HumanoidRobots", "TeslaOptimus", "FutureTech", "BeyondEraTech", "AI2026"],
            "hashtags": ["#Documentary", "#HumanoidRobots", "#BeyondEraTech", "#FutureTech"],
            "cta": "Subscribe to BeyondEra Tech for daily long-form investigative documentaries.",
            "thumbnail_concept": "Cinematic split screen: Humanoid robot hand shaking human scientist hand under volumetric laboratory light",
            "visual_style": "Widescreen 16:9 8k IMAX cinematic photorealism",
            "negative_prompts": "cartoon, 3D render look, blur, artifacts, text overlay, watermark",
            "seo_keywords": ["humanoid robotics documentary", "physical AI timeline", "AGI 2026", "BeyondEra Tech"],
            "uzbek_analysis": "Ushbu 10-daqiqalik dokumental video kanal obro'si va 4000 soatlik monetizatsiyani yig'ish uchun mo'ljallangan.",
            "uzbek_voice_summary": "BeyondEra Tech kanali uchun har 10 kunda chiqadigan maxsus 10 daqiqalik to'liq dokumental video tayyorlandi."
        }


if __name__ == "__main__":
    plan = generate_content_plan()
    print("\n--- GENERATED PLAN PREVIEW ---")
    print(f"Title: {plan['title']}")
    print(f"Type: {plan['video_type']} ({plan['duration']}s)")
    print(f"Scenes: {len(plan.get('scenes', []))}")
    print(f"Hook: {plan['hook']}")
    print(f"SEO Tags: {', '.join(plan.get('tags', [])[:5])}")
