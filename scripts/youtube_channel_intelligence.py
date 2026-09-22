#!/usr/bin/env python3
"""
BeyondEra Tech - YouTube Channel Intelligence & Competitor Analysis Engine.
Senior-grade autonomous system that:
1. Discovers and monitors competitor channels in AI/Robotics/Future Tech niche
2. Analyzes own channel performance, finds weaknesses and gaps
3. Studies competitor top-performing videos and extracts winning patterns
4. Uses Gemini AI to generate unique content ideas based on market intelligence
5. Produces daily actionable intelligence reports for the content pipeline
"""

import os
import sys
import json
import re
import time
import random
import hashlib
import subprocess
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

try:
    import requests
except ImportError:
    requests = None


from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [INTELLIGENCE] %(message)s")
logger = logging.getLogger("ChannelIntelligence")

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
OWN_CHANNEL_ID = "UC525J1r4HA1qV8DVf6FKQEg"
OWN_CHANNEL_URL = f"https://www.youtube.com/channel/{OWN_CHANNEL_ID}"

# Intelligence cache
INTEL_CACHE_DIR = os.path.join(PROJECT_ROOT, "assets/intelligence_cache")
os.makedirs(INTEL_CACHE_DIR, exist_ok=True)

# Known competitor channels in Future Tech / AI niche (seed list)
COMPETITOR_SEEDS = [
    {"name": "Fireship", "url": "https://www.youtube.com/@Fireship", "niche": "tech_explainer"},
    {"name": "Two Minute Papers", "url": "https://www.youtube.com/@TwoMinutePapers", "niche": "ai_research"},
    {"name": "Digital Engine", "url": "https://www.youtube.com/@DigitalEngine", "niche": "future_tech"},
    {"name": "AI Uncovered", "url": "https://www.youtube.com/@AIUncovered", "niche": "ai_news"},
    {"name": "Undecided with Matt Ferrell", "url": "https://www.youtube.com/@UndecidedMF", "niche": "clean_energy"},
    {"name": "Tech Vision", "url": "https://www.youtube.com/@TechVision", "niche": "future_tech"},
    {"name": "The AI Advantage", "url": "https://www.youtube.com/@aiadvantage", "niche": "ai_tools"},
    {"name": "Marques Brownlee", "url": "https://www.youtube.com/@mkbhd", "niche": "tech_review"},
]

# Search queries to discover MORE competitors dynamically
DISCOVERY_QUERIES = [
    "humanoid robot breakthrough 2026",
    "quantum computing explained shorts",
    "AI future technology",
    "robots replacing humans",
    "neuralink brain chip update",
    "fusion energy breakthrough",
    "AGI artificial general intelligence",
    "future technology 2030",
]


def run_ytdlp(args: List[str], timeout: int = 30) -> str:
    """Runs yt-dlp command safely with timeout."""
    cmd = ["yt-dlp", "--no-warnings", "--no-check-certificate"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout
    except subprocess.TimeoutExpired:
        logger.warning(f"yt-dlp timeout: {' '.join(args[:3])}")
        return ""
    except FileNotFoundError:
        logger.error("yt-dlp not installed! Install with: pip install yt-dlp")
        return ""
    except Exception as e:
        logger.error(f"yt-dlp error: {e}")
        return ""


def parse_ytdlp_json_lines(output: str) -> List[Dict[str, Any]]:
    """Parses multiple JSON objects from yt-dlp output."""
    results = []
    for line in output.strip().splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return results


class YouTubeChannelIntelligence:
    """Master intelligence engine for competitive analysis and content strategy."""

    def __init__(self):
        self.competitor_cache: Dict[str, Any] = {}
        self.own_channel_data: Dict[str, Any] = {}

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 1: OWN CHANNEL ANALYSIS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def analyze_own_channel(self) -> Dict[str, Any]:
        """Scrapes BeyondEra Tech channel and analyzes performance metrics."""
        logger.info(f"📊 Analyzing own channel: {OWN_CHANNEL_URL}")

        # Get recent videos from own channel
        output = run_ytdlp([
            "--dump-json", "--flat-playlist",
            "--playlist-end", "20",
            f"{OWN_CHANNEL_URL}/videos"
        ], timeout=25)

        videos = parse_ytdlp_json_lines(output)
        if not videos:
            logger.warning("Could not fetch own channel videos. Using cached data.")
            return self._load_cached("own_channel") or {"videos": [], "analysis": "No data"}

        processed = []
        total_views = 0
        for v in videos:
            views = v.get("view_count", 0) or 0
            total_views += views
            processed.append({
                "id": v.get("id", ""),
                "title": v.get("title", "Unknown"),
                "views": views,
                "views_formatted": self._format_views(views),
                "duration": v.get("duration", 0),
                "upload_date": v.get("upload_date", ""),
                "description": (v.get("description") or "")[:200],
            })

        # Sort by views
        processed.sort(key=lambda x: x["views"], reverse=True)

        avg_views = total_views / max(1, len(processed))
        top_video = processed[0] if processed else None
        worst_video = processed[-1] if processed else None

        # Find gaps - what topics are missing
        all_titles = " ".join(v["title"] for v in processed).lower()
        missing_topics = []
        for topic in ["quantum", "neuralink", "fusion", "space", "agi", "nanotechnology"]:
            if topic not in all_titles:
                missing_topics.append(topic)

        analysis = {
            "channel_id": OWN_CHANNEL_ID,
            "total_videos_analyzed": len(processed),
            "total_views": total_views,
            "average_views": int(avg_views),
            "top_performing": top_video,
            "worst_performing": worst_video,
            "missing_topics": missing_topics,
            "videos": processed,
            "recommendations": [],
            "analyzed_at": datetime.now().isoformat()
        }

        # Generate recommendations
        if avg_views < 500:
            analysis["recommendations"].append("Ko'rishlar soni past. Hook va thumbnail sifatini oshiring.")
        if missing_topics:
            analysis["recommendations"].append(f"Quyidagi mavzular bo'yicha video yo'q: {', '.join(missing_topics)}")
        if worst_video and worst_video["views"] < avg_views * 0.3:
            analysis["recommendations"].append(f"Eng kam ko'rilgan video: '{worst_video['title']}' - sarlavhani yangilang.")

        self.own_channel_data = analysis
        self._save_cached("own_channel", analysis)
        return analysis

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 2: COMPETITOR DISCOVERY & ANALYSIS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def discover_competitors(self, max_channels: int = 10) -> List[Dict[str, Any]]:
        """Discovers competitor channels by searching YouTube for top videos in our niche."""
        logger.info("🔍 Discovering competitor channels...")
        discovered = {}

        for query in random.sample(DISCOVERY_QUERIES, min(4, len(DISCOVERY_QUERIES))):
            output = run_ytdlp([
                "--dump-json", "--flat-playlist",
                "--default-search", "ytsearch5",
                query
            ], timeout=20)

            for entry in parse_ytdlp_json_lines(output):
                channel = entry.get("channel") or entry.get("uploader") or ""
                channel_url = entry.get("channel_url") or entry.get("uploader_url") or ""
                if channel and channel_url and channel not in discovered:
                    discovered[channel] = {
                        "name": channel,
                        "url": channel_url,
                        "sample_video": entry.get("title", ""),
                        "sample_views": entry.get("view_count", 0) or 0,
                        "discovered_via": query
                    }

        # Merge with seed list
        for seed in COMPETITOR_SEEDS:
            if seed["name"] not in discovered:
                discovered[seed["name"]] = seed

        competitors = sorted(discovered.values(), key=lambda x: x.get("sample_views", 0), reverse=True)
        logger.info(f"✅ Discovered {len(competitors)} competitor channels")
        return competitors[:max_channels]

    def analyze_competitor_top_videos(self, channel_url: str, channel_name: str = "", limit: int = 8) -> Dict[str, Any]:
        """Analyzes a competitor channel's top-performing videos."""
        logger.info(f"📺 Analyzing competitor: {channel_name or channel_url}")

        output = run_ytdlp([
            "--dump-json", "--flat-playlist",
            "--playlist-end", str(limit),
            f"{channel_url}/videos"
        ], timeout=25)

        videos = parse_ytdlp_json_lines(output)
        if not videos:
            return {"channel": channel_name, "videos": [], "patterns": []}

        processed = []
        for v in videos:
            views = v.get("view_count", 0) or 0
            title = v.get("title", "")
            processed.append({
                "title": title,
                "views": views,
                "views_formatted": self._format_views(views),
                "duration": v.get("duration", 0),
                "id": v.get("id", ""),
                "description": (v.get("description") or "")[:300],
            })

        processed.sort(key=lambda x: x["views"], reverse=True)

        # Extract title patterns from top videos
        patterns = self._extract_title_patterns([v["title"] for v in processed[:5]])

        return {
            "channel": channel_name or channel_url,
            "total_analyzed": len(processed),
            "top_videos": processed[:5],
            "title_patterns": patterns,
            "avg_views": sum(v["views"] for v in processed) // max(1, len(processed)),
            "analyzed_at": datetime.now().isoformat()
        }

    def _extract_title_patterns(self, titles: List[str]) -> List[str]:
        """Extracts common patterns from successful video titles."""
        patterns = []
        for title in titles:
            if "?" in title:
                patterns.append("QUESTION_HOOK")
            if any(w in title.lower() for w in ["why", "how", "what"]):
                patterns.append("CURIOSITY_GAP")
            if any(c in title for c in ["🤖", "🔥", "⚡", "🧠"]):
                patterns.append("EMOJI_ENGAGEMENT")
            if re.search(r'\d+', title):
                patterns.append("NUMBER_PATTERN")
            if any(w in title.lower() for w in ["shocking", "insane", "unbelievable", "secret"]):
                patterns.append("SHOCK_VALUE")
            if "#shorts" in title.lower() or "#short" in title.lower():
                patterns.append("SHORTS_TAG")
        return list(set(patterns))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 3: GEMINI-POWERED CONTENT STRATEGY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def generate_daily_content_ideas(self, competitor_data: List[Dict], own_analysis: Dict) -> List[Dict[str, Any]]:
        """
        Uses Gemini AI to generate 5 unique daily content ideas based on:
        - Competitor top-performing videos
        - Own channel gaps and weaknesses
        - Current trending topics
        Returns list of content ideas with prompts, hooks, and scripts.
        """
        if not GEMINI_KEY:
            logger.warning("Gemini API key not set. Using intelligent fallback.")
            return self._generate_fallback_ideas(competitor_data, own_analysis)

        # Compile competitor intelligence
        comp_summary = []
        for comp in competitor_data[:5]:
            for vid in comp.get("top_videos", [])[:2]:
                comp_summary.append(f"- [{comp['channel']}] '{vid['title']}' ({self._format_views(vid['views'])})")

        # Own channel weaknesses
        weaknesses = own_analysis.get("recommendations", [])
        missing_topics = own_analysis.get("missing_topics", [])
        avg_views = own_analysis.get("average_views", 0)

        # Today's date for freshness
        today = datetime.now().strftime("%Y-%m-%d")

        gemini_prompt = f"""You are the Senior Content Strategist for BeyondEra Tech, a YouTube channel focused on Future Technology, AI, Robotics, Quantum Computing, and Space.

TODAY: {today}

COMPETITOR TOP-PERFORMING VIDEOS:
{chr(10).join(comp_summary) if comp_summary else 'No competitor data available'}

OWN CHANNEL STATUS:
- Average views per video: {avg_views}
- Missing topic coverage: {', '.join(missing_topics) if missing_topics else 'None'}
- Weaknesses: {'; '.join(weaknesses) if weaknesses else 'None identified'}

GENERATE exactly 5 unique YouTube Shorts content ideas (30-60 seconds each). Each must be COMPLETELY DIFFERENT from each other in topic and visual style.

For EACH idea, return a JSON object with these EXACT keys:
{{
  "topic": "Specific technology topic (must be unique, never repeat)",
  "title": "Viral YouTube Shorts title under 60 chars with emoji",
  "hook": "First 3 seconds hook sentence that STOPS scrolling",
  "script": "Full 80-110 word English voiceover script. Must sound natural, dramatic, and conversational. Include the hook at the start and end with a cliffhanger/loop.",
  "scene_prompts": ["5 detailed cinematic Google Flow AI video generation prompts, each describing a specific 8K photorealistic scene with lighting, camera angle, and motion"],
  "visual_style": "Cinematic description of the overall visual approach",
  "voice_model": "One of: en-US-ChristopherNeural, en-US-AndrewNeural, en-US-BrianNeural, en-GB-RyanNeural, en-US-GuyNeural, en-US-EricNeural",
  "music_profile": "One of: cyber_pulse, quantum_suspense, ambient_flow_synth, epic_uplifting",
  "tags": ["5-8 YouTube tags"],
  "competitor_inspired_by": "Which competitor video pattern inspired this (or 'Original')"
}}

Return ONLY a JSON array of 5 objects. No other text."""

        try:
            models = ["models/gemini-3.6-flash", "models/gemini-3.6-flash", "models/gemini-3.6-flash-lite"]
            for model in models:
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GEMINI_KEY}"
                resp = requests.post(
                    endpoint,
                    json={
                        "contents": [{"parts": [{"text": gemini_prompt}]}],
                        "generationConfig": {"response_mime_type": "application/json", "temperature": 0.9}
                    },
                    timeout=45
                )
                if resp.status_code == 200:
                    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    # Parse JSON array
                    s = text.find("[")
                    e = text.rfind("]")
                    if s != -1 and e != -1:
                        ideas = json.loads(text[s:e+1])
                        logger.info(f"✅ Gemini generated {len(ideas)} unique content ideas")
                        return ideas
                    # Try single object
                    s = text.find("{")
                    e = text.rfind("}")
                    if s != -1 and e != -1:
                        return [json.loads(text[s:e+1])]
        except Exception as e:
            logger.error(f"Gemini content generation error: {e}")

        return self._generate_fallback_ideas(competitor_data, own_analysis)

    def _generate_fallback_ideas(self, competitor_data: List[Dict], own_analysis: Dict) -> List[Dict[str, Any]]:
        """Generates diverse content ideas without Gemini API."""
        missing = own_analysis.get("missing_topics", ["quantum", "neuralink", "fusion"])
        ideas = [
            {
                "topic": "Quantum Processor Micro-Assembly",
                "title": "🔬 This Quantum Chip Changes Everything! #Shorts",
                "hook": "Scientists just built a chip that makes every computer on Earth look like a calculator.",
                "script": "Scientists just built a chip that makes every computer on Earth look like a calculator. Inside a cryogenic chamber at negative 273 degrees Celsius, photons are locked into quantum states that can solve problems no supercomputer ever could. This single processor contains more computational pathways than atoms in the visible universe. The revolution isn't coming. It just arrived. And what they're building next will terrify you.",
                "scene_prompts": [
                    "Cinematic macro shot of glowing blue quantum processor chip inside cryogenic chamber with frost particles, volumetric laser beams, 8K photorealistic",
                    "Extreme close-up of photon pathways inside silicon photonic chip, neon blue light traces, shallow depth of field, anamorphic lens flares",
                    "Wide shot of cleanroom laboratory with scientists in white suits examining holographic quantum state displays, dramatic overhead lighting",
                    "Tracking shot along quantum computing rack with hundreds of golden cables and cryogenic cooling systems, cinematic fog",
                    "Final dramatic zoom into the processor core showing quantum entanglement visualization, particle effects, cosmic scale transition"
                ],
                "visual_style": "Cyberpunk cold laboratory, volumetric blue/cyan lighting",
                "voice_model": "en-US-ChristopherNeural",
                "music_profile": "quantum_suspense",
                "tags": ["Shorts", "QuantumComputing", "FutureTech", "Science", "AI", "BeyondEraTech"],
                "competitor_inspired_by": "Original"
            },
            {
                "topic": "Neuralink Telepathic Communication",
                "title": "🧠 Humans Can Now Read Minds! #Shorts",
                "hook": "For the first time in human history, two people just had a conversation using only their thoughts.",
                "script": "For the first time in human history, two people just had a conversation using only their thoughts. Neuralink's N2 implant decoded neural signals at sixteen thousand electrodes per second, translating raw brain activity into words with ninety-seven percent accuracy. The subject typed forty words per minute without moving a single muscle. This isn't science fiction anymore. Telepathic communication is now a medical reality. And the next upgrade will let you control any machine on Earth with your mind.",
                "scene_prompts": [
                    "Cinematic close-up of brain-computer interface chip being precisely implanted by robotic surgical arm, sterile blue lighting, photorealistic 8K",
                    "Visualization of neural pathways firing between two human brains connected by digital light streams, dark background with neon synapses",
                    "Medical laboratory with patient using thought-controlled cursor on holographic display, volumetric lighting, shallow depth of field",
                    "Macro shot of the N2 neural implant chip with microscopic electrode threads, reflective titanium surface, extreme detail",
                    "Wide establishing shot of futuristic neuroscience research facility with glass walls showing brain scan holograms"
                ],
                "visual_style": "Medical futuristic, electric violet and white lighting",
                "voice_model": "en-US-BrianNeural",
                "music_profile": "ambient_flow_synth",
                "tags": ["Shorts", "Neuralink", "BrainChip", "Telepathy", "FutureTech", "BeyondEraTech"],
                "competitor_inspired_by": "Original"
            },
            {
                "topic": "Nuclear Fusion Net Energy Gain",
                "title": "⚡ Unlimited Energy Just Became Real! #Shorts",
                "hook": "A reactor the size of a shipping container just produced more energy than the entire city of London uses in one hour.",
                "script": "A reactor the size of a shipping container just produced more energy than the entire city of London uses in one hour. Inside a magnetic confinement chamber, hydrogen plasma reaches two hundred million degrees, four times hotter than the core of the sun. For the first time, the machine produced ten times more energy than it consumed. Fusion power is no longer thirty years away. It just happened. And this changes everything about human civilization.",
                "scene_prompts": [
                    "Cinematic wide shot of compact tokamak fusion reactor with glowing plasma ring inside magnetic confinement, dramatic orange/blue lighting, 8K",
                    "Extreme macro of plasma discharge inside fusion chamber, intense white-hot core with magnetic field lines visible, photorealistic",
                    "Exterior shot of modular fusion power plant with steam rising, futuristic industrial architecture, golden hour lighting",
                    "Control room with engineers monitoring holographic plasma stability displays, blue terminal glow, cinematic atmosphere",
                    "Final shot zooming into the fusion core showing atomic nuclei merging, particle physics visualization, cosmic energy release"
                ],
                "visual_style": "Industrial cinematic, plasma orange and deep blue contrast",
                "voice_model": "en-GB-RyanNeural",
                "music_profile": "epic_uplifting",
                "tags": ["Shorts", "FusionEnergy", "CleanEnergy", "Nuclear", "FutureTech", "BeyondEraTech"],
                "competitor_inspired_by": "Original"
            },
            {
                "topic": "Humanoid Robot Mass Production",
                "title": "🤖 Robots Are Now Building Themselves! #Shorts",
                "hook": "Inside this factory, humanoid robots are assembling other humanoid robots, and nobody told them how.",
                "script": "Inside this factory, humanoid robots are assembling other humanoid robots, and nobody told them how. Using zero-shot learning from a single video demonstration, these machines calibrated sub-millimeter precision assembly in under twenty minutes. They work twenty-four hours a day, never make errors, and learn faster with each unit they build. The production line is now fully autonomous. No human intervention required. And by next year, ten thousand of these will roll off the line every single month.",
                "scene_prompts": [
                    "Cinematic tracking shot through automated gigafactory with rows of humanoid robots assembling components, neon blue industrial lighting, 8K",
                    "Close-up of robot hands precisely connecting micro-actuators with sub-millimeter accuracy, sparks and precision tools, shallow DOF",
                    "Overhead drone shot of entire production floor with hundreds of robots in synchronized motion, dramatic scale",
                    "Macro shot of robot optical sensor scanning and learning from another robot's movements, data overlay holographic effect",
                    "Final wide shot of completed humanoid robots standing in formation, LED eyes activating sequentially, cinematic reveal"
                ],
                "visual_style": "Industrial cyberpunk, neon cyan and dark steel",
                "voice_model": "en-US-AndrewNeural",
                "music_profile": "cyber_pulse",
                "tags": ["Shorts", "Robotics", "HumanoidRobot", "Tesla", "AI", "FutureTech", "BeyondEraTech"],
                "competitor_inspired_by": "Original"
            },
            {
                "topic": "AGI Self-Recursive Intelligence",
                "title": "🌐 AI Just Wrote Its Own Upgrade! #Shorts",
                "hook": "An AI system just rewrote its own source code and became ten times smarter overnight.",
                "script": "An AI system just rewrote its own source code and became ten times smarter overnight. Without any human programmer, the model analyzed its own architecture, identified inefficiencies, and generated forty-seven thousand lines of optimized code. The next morning, it solved three unsolved physics problems that stumped human scientists for decades. This is recursive self-improvement, and experts say it's the last invention humanity will ever need to make. The singularity isn't a theory anymore. It's a timestamp.",
                "scene_prompts": [
                    "Cinematic visualization of AI neural network self-modifying its architecture, flowing data streams and recursive code patterns, dark void with neon green",
                    "Close-up of holographic code being written autonomously on transparent displays, matrix-style cascading symbols, 8K photorealistic",
                    "Wide shot of massive data center with thousands of GPU racks pulsing with computation light, dramatic fog and volumetric rays",
                    "Abstract visualization of recursive intelligence loops expanding fractally, cosmic scale, mathematical beauty",
                    "Final shot of a single terminal screen displaying 'OPTIMIZATION COMPLETE - PERFORMANCE: +1000%', dramatic lighting"
                ],
                "visual_style": "Matrix emerald green, digital consciousness aesthetic",
                "voice_model": "en-US-GuyNeural",
                "music_profile": "cyber_pulse",
                "tags": ["Shorts", "AGI", "ArtificialIntelligence", "Singularity", "FutureTech", "BeyondEraTech"],
                "competitor_inspired_by": "Original"
            }
        ]
        # If we know missing topics, prioritize those
        random.shuffle(ideas)
        return ideas

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SECTION 4: FULL INTELLIGENCE REPORT
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    def generate_daily_intelligence_report(self) -> Dict[str, Any]:
        """
        Generates a comprehensive daily intelligence report:
        1. Own channel performance analysis
        2. Competitor discovery and top video analysis
        3. AI-generated content ideas based on intelligence
        4. Actionable recommendations
        """
        logger.info("=" * 70)
        logger.info("🧠 DAILY INTELLIGENCE REPORT GENERATION STARTED")
        logger.info("=" * 70)

        # 1. Analyze own channel
        own_analysis = self.analyze_own_channel()
        logger.info(f"📊 Own channel: {own_analysis.get('total_videos_analyzed', 0)} videos, avg {own_analysis.get('average_views', 0)} views")

        # 2. Discover and analyze competitors
        competitors = self.discover_competitors(max_channels=6)
        competitor_analyses = []
        for comp in competitors[:4]:  # Analyze top 4
            url = comp.get("url", "")
            name = comp.get("name", "Unknown")
            if url:
                analysis = self.analyze_competitor_top_videos(url, name, limit=5)
                competitor_analyses.append(analysis)
                time.sleep(1)  # Rate limiting

        # 3. Generate content ideas
        content_ideas = self.generate_daily_content_ideas(competitor_analyses, own_analysis)

        # 4. Compile full report
        report = {
            "report_date": datetime.now().isoformat(),
            "own_channel": {
                "total_views": own_analysis.get("total_views", 0),
                "average_views": own_analysis.get("average_views", 0),
                "top_video": own_analysis.get("top_performing"),
                "weaknesses": own_analysis.get("recommendations", []),
                "missing_topics": own_analysis.get("missing_topics", []),
            },
            "competitor_intelligence": [{
                "channel": c.get("channel", ""),
                "avg_views": c.get("avg_views", 0),
                "top_video": c.get("top_videos", [{}])[0] if c.get("top_videos") else None,
                "title_patterns": c.get("title_patterns", []),
            } for c in competitor_analyses],
            "content_ideas": content_ideas,
            "total_ideas": len(content_ideas),
        }

        # Save report
        report_path = os.path.join(INTEL_CACHE_DIR, f"daily_report_{datetime.now().strftime('%Y%m%d')}.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ Intelligence report saved: {report_path}")
        logger.info(f"💡 Generated {len(content_ideas)} unique content ideas")

        return report

    def get_todays_content_idea(self, day_index: int = 0) -> Dict[str, Any]:
        """
        Gets a specific content idea for today.
        Checks for cached report first, generates new one if needed.
        """
        today_file = os.path.join(INTEL_CACHE_DIR, f"daily_report_{datetime.now().strftime('%Y%m%d')}.json")

        if os.path.exists(today_file):
            with open(today_file, "r", encoding="utf-8") as f:
                report = json.load(f)
        else:
            report = self.generate_daily_intelligence_report()

        ideas = report.get("content_ideas", [])
        if not ideas:
            ideas = self._generate_fallback_ideas([], {})

        idx = day_index % len(ideas)
        return ideas[idx]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # UTILITY METHODS
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    @staticmethod
    def _format_views(views: int) -> str:
        if views >= 1_000_000:
            return f"{views / 1_000_000:.1f}M"
        elif views >= 1_000:
            return f"{views / 1_000:.1f}K"
        return str(views)

    def _save_cached(self, key: str, data: Dict):
        path = os.path.join(INTEL_CACHE_DIR, f"{key}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_cached(self, key: str) -> Optional[Dict]:
        path = os.path.join(INTEL_CACHE_DIR, f"{key}.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="YouTube Channel Intelligence Engine")
    parser.add_argument("action", nargs="?", default="report", choices=["report", "own", "competitors", "ideas"])
    args = parser.parse_args()

    intel = YouTubeChannelIntelligence()

    if args.action == "report":
        report = intel.generate_daily_intelligence_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    elif args.action == "own":
        own = intel.analyze_own_channel()
        print(json.dumps(own, indent=2, ensure_ascii=False))
    elif args.action == "competitors":
        comps = intel.discover_competitors()
        for c in comps:
            print(f"  📺 {c['name']} - {c.get('url', '')}")
    elif args.action == "ideas":
        idea = intel.get_todays_content_idea()
        print(json.dumps(idea, indent=2, ensure_ascii=False))
