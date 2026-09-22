import os
import json
import time
import logging
import subprocess
import datetime
import traceback
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
# Set up logging for the module
# This ensures all activities are properly tracked for debugging and monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# GLOBAL CONSTANTS & ENVIRONMENT SETUP
# ============================================================================
PROJECT_ROOT = '/home/kali/Рабочий стол/Youtube akkaunt integratsiyasi'
# Load environment variables from the project root .env file
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# Constants required for the module's core functionality
GEMINI_KEY = os.getenv('GEMINI_API_KEY', '')
OWN_CHANNEL_ID = 'UC525J1r4HA1qV8DVf6FKQEg'
CACHE_DIR = os.path.join(PROJECT_ROOT, 'assets', 'intelligence_cache')

# Ensure the cache directory exists to store intelligence reports
os.makedirs(CACHE_DIR, exist_ok=True)

# ============================================================================
# GEMINI API HELPER (REST-based, no SDK needed)
# ============================================================================
import requests

def call_gemini_api(prompt_text: str, temperature: float = 0.9) -> Optional[str]:
    """Calls Gemini API via REST with model fallback chain."""
    if not GEMINI_KEY:
        logger.warning("GEMINI_API_KEY not configured.")
        return None
    models = ['models/gemini-3.6-flash', 'models/gemini-3.6-flash-lite']
    for model in models:
        url = f'https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GEMINI_KEY}'
        try:
            resp = requests.post(url, json={
                'contents': [{'parts': [{'text': prompt_text}]}],
                'generationConfig': {'temperature': temperature}
            }, timeout=45)
            if resp.status_code == 200:
                text = resp.json()['candidates'][0]['content']['parts'][0]['text']
                return text.strip()
            else:
                logger.warning(f"Gemini {model} returned {resp.status_code}")
        except Exception as e:
            logger.warning(f"Gemini {model} error: {e}")
    return None


# ============================================================================
# CORE CLASS: ChannelAnalyzer
# ============================================================================
class ChannelAnalyzer:
    """
    This module monitors and analyzes the BeyondEra Tech YouTube channel daily.
    It focuses on:
    - Finding weaknesses in the current content strategy.
    - Learning from competitor channels.
    - Discovering missing topics that the audience might be interested in.
    - Providing actionable insights and suggestions.
    """

    def __init__(self):
        """
        Initializes the ChannelAnalyzer.
        Sets up paths and basic configuration for tools like yt-dlp.
        """
        self.project_root = PROJECT_ROOT
        self.own_channel_id = OWN_CHANNEL_ID
        self.yt_dlp_path = 'yt-dlp'
        
        # Predefined list of core topics we want to cover
        self.core_topics = [
            'quantum', 'neuralink', 'fusion', 'space', 'agi', 
            'nanotechnology', 'ai', 'robotics', 'biotech', 'cybersecurity'
        ]

    def _run_yt_dlp(self, args: List[str]) -> Optional[Dict[str, Any]]:
        """
        Helper method to run yt-dlp commands as a subprocess and parse the JSON output.
        
        Args:
            args (List[str]): List of arguments to pass to yt-dlp.
            
        Returns:
            Optional[Dict[str, Any]]: Parsed JSON output from yt-dlp, or None if it fails.
        """
        command = [self.yt_dlp_path, '-J', '--no-warnings', '--flat-playlist'] + args
        try:
            logger.info(f"Running yt-dlp command: {' '.join(command)}")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"yt-dlp command failed with exit code {e.returncode}")
            logger.error(f"Error output: {e.stderr}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse yt-dlp JSON output: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error running yt-dlp: {e}")
            logger.debug(traceback.format_exc())
            return None

    def analyze_own_channel(self) -> Dict[str, Any]:
        """
        Uses yt-dlp to scrape the BeyondEra Tech channel.
        - Gets the last 20 videos with view counts, titles, durations.
        - Calculates average views, best/worst performing videos.
        - Identifies missing topic coverage based on predefined tech topics.
        - Generates specific improvement recommendations.
        
        Returns:
            Dict[str, Any]: Structured analysis dictionary containing metrics and findings.
        """
        logger.info(f"Analyzing own channel: {self.own_channel_id}")
        channel_url = f"https://www.youtube.com/channel/{self.own_channel_id}"
        
        # Scrape last 20 videos
        args = [
            '--playlist-end', '20',
            channel_url
        ]
        
        data = self._run_yt_dlp(args)
        if not data or 'entries' not in data:
            logger.error("Failed to retrieve data for own channel.")
            return {"error": "Failed to retrieve channel data"}

        entries = [entry for entry in data['entries'] if entry is not None]
        
        videos = []
        total_views = 0
        best_video = None
        worst_video = None

        for entry in entries:
            video_data = {
                'title': entry.get('title', 'Unknown'),
                'id': entry.get('id'),
                'url': entry.get('url'),
                'duration': entry.get('duration'),
                'view_count': entry.get('view_count', 0)
            }
            videos.append(video_data)
            
            views = video_data['view_count']
            if views is not None:
                total_views += views
                if best_video is None or views > best_video.get('view_count', 0):
                    best_video = video_data
                if worst_video is None or views < worst_video.get('view_count', float('inf')):
                    worst_video = video_data

        video_count = len(videos)
        average_views = total_views / video_count if video_count > 0 else 0

        # Topic coverage analysis
        titles_text = " ".join([v['title'].lower() for v in videos])
        
        covered_topics = [topic for topic in self.core_topics if topic in titles_text]
        missing_topics = [topic for topic in self.core_topics if topic not in covered_topics]

        analysis_result = {
            'channel_id': self.own_channel_id,
            'videos_analyzed': video_count,
            'average_views': average_views,
            'total_views_recent': total_views,
            'best_performing_video': best_video,
            'worst_performing_video': worst_video,
            'missing_topics': missing_topics,
            'covered_topics': covered_topics,
            'recent_videos': videos,
            'recommendations': self._generate_internal_recommendations(missing_topics, average_views)
        }

        logger.info(f"Own channel analysis completed. Avg views: {average_views}")
        return analysis_result

    def _generate_internal_recommendations(self, missing_topics: List[str], avg_views: float) -> List[str]:
        """
        Generates simple internal recommendations based on missing topics and view counts.
        
        Args:
            missing_topics (List[str]): Topics not covered in recent videos.
            avg_views (float): Average view count for recent videos.
            
        Returns:
            List[str]: A list of actionable recommendation strings.
        """
        recs = []
        if missing_topics:
            recs.append(f"Consider creating content about: {', '.join(missing_topics)} to broaden technology coverage.")
        if avg_views < 1000:
            recs.append("Average views are low. Consider improving thumbnails, titles (using shock words or curiosity gaps), and focusing on trending tech news.")
        elif avg_views > 10000:
            recs.append("Great average view count! Keep doubling down on the topics that are working well.")
        return recs

    def discover_similar_channels(self) -> List[Dict[str, Any]]:
        """
        Finds 10+ competitor channels:
        - Searches YouTube for targeted tech queries.
        - Extracts channel names and URLs from search results.
        - Includes a predefined seed list of highly successful tech channels.
        
        Returns:
            List[Dict[str, Any]]: Sorted list of competitor channels based on relevance score.
        """
        logger.info("Discovering similar competitor channels")
        
        search_queries = [
            'ytsearch5:AI future technology shorts',
            'ytsearch5:humanoid robot breakthrough',
            'ytsearch5:quantum computing explained'
        ]

        competitors = {}
        
        # Add Seed List
        seed_list = [
            {"name": "Fireship", "url": "https://www.youtube.com/c/Fireship"},
            {"name": "Two Minute Papers", "url": "https://www.youtube.com/c/TwoMinutePapers"},
            {"name": "Digital Engine", "url": "https://www.youtube.com/c/DigitalEngine"},
            {"name": "AI Uncovered", "url": "https://www.youtube.com/@AIUncovered"},
            {"name": "Tech Vision", "url": "https://www.youtube.com/c/TechVision"},
            {"name": "Marques Brownlee", "url": "https://www.youtube.com/c/MKBHD"}
        ]
        
        for seed in seed_list:
            competitors[seed["url"]] = {
                "name": seed["name"],
                "url": seed["url"],
                "source": "seed",
                "score": 100  # Give seeds high baseline score
            }

        # Search for new competitors using yt-dlp
        for query in search_queries:
            args = [query]
            data = self._run_yt_dlp(args)
            if data and 'entries' in data:
                for entry in data['entries']:
                    if not entry:
                        continue
                    channel_url = entry.get('channel_url')
                    channel_name = entry.get('channel')
                    if channel_url and channel_name:
                        if channel_url not in competitors:
                            competitors[channel_url] = {
                                "name": channel_name,
                                "url": channel_url,
                                "source": "search",
                                "score": 50 # Base score for newly discovered
                            }
                        else:
                            # Increase score if found multiple times across different queries
                            competitors[channel_url]["score"] += 10

        # Sort by score descending to prioritize highly relevant channels
        sorted_competitors = sorted(competitors.values(), key=lambda x: x["score"], reverse=True)
        logger.info(f"Discovered {len(sorted_competitors)} competitors.")
        return sorted_competitors

    def analyze_competitor(self, channel_url: str, name: str) -> Dict[str, Any]:
        """
        Performs a deep analysis of a specific competitor channel.
        - Gets top 8 recent videos with view counts.
        - Extracts title patterns (questions, numbers, emojis, shock words).
        - Calculates average views for these top videos.
        
        Args:
            channel_url (str): The YouTube URL of the competitor.
            name (str): The name of the competitor channel.
            
        Returns:
            Dict[str, Any]: Structured competitor analysis including title patterns and top videos.
        """
        logger.info(f"Analyzing competitor: {name} ({channel_url})")
        
        args = [
            '--playlist-end', '8',
            channel_url
        ]
        
        data = self._run_yt_dlp(args)
        if not data or 'entries' not in data:
            logger.error(f"Failed to retrieve data for competitor {name}")
            return {"name": name, "url": channel_url, "error": "Failed to extract data"}

        entries = [e for e in data['entries'] if e is not None]
        
        videos = []
        total_views = 0
        shock_words = ['shocking', 'insane', 'genius', 'terrifying', 'breakthrough', 'secret', 'finally', 'banned']
        
        title_patterns = {
            'has_question': 0,
            'has_number': 0,
            'has_shock_word': 0,
            'average_length': 0
        }

        total_title_length = 0

        for entry in entries:
            title = entry.get('title', '')
            views = entry.get('view_count', 0)
            
            videos.append({
                'title': title,
                'view_count': views,
                'url': entry.get('url')
            })
            
            if views:
                total_views += views
                
            total_title_length += len(title)
            
            # Analyze title elements for common YouTube engagement tactics
            if '?' in title:
                title_patterns['has_question'] += 1
            if any(char.isdigit() for char in title):
                title_patterns['has_number'] += 1
            if any(word in title.lower() for word in shock_words):
                title_patterns['has_shock_word'] += 1

        video_count = len(videos)
        if video_count > 0:
            title_patterns['average_length'] = total_title_length / video_count
            average_views = total_views / video_count
        else:
            average_views = 0

        logger.info(f"Competitor {name} analysis complete. Avg views: {average_views}")
        return {
            'name': name,
            'url': channel_url,
            'video_count_analyzed': video_count,
            'average_views': average_views,
            'title_patterns': title_patterns,
            'top_videos': videos
        }

    def generate_daily_report(self) -> Dict[str, Any]:
        """
        Generates the full daily intelligence report.
        - Analyzes the own channel.
        - Discovers and analyzes the top 4 competitors.
        - Uses the Gemini API to generate 5 fresh content ideas based on the findings.
        - Caches the report to disk to avoid duplicate work within the same day.
        
        Returns:
            Dict[str, Any]: The complete intelligence report containing data and ideas.
        """
        logger.info("Generating daily intelligence report...")
        
        own_channel_data = self.analyze_own_channel()
        
        competitors = self.discover_similar_channels()
        top_4_competitors = competitors[:4]
        
        competitor_analysis = []
        for comp in top_4_competitors:
            analysis = self.analyze_competitor(comp['url'], comp['name'])
            competitor_analysis.append(analysis)
            
        report = {
            'date': datetime.datetime.now().isoformat(),
            'own_channel': own_channel_data,
            'competitors_analyzed': competitor_analysis,
            'content_ideas': []
        }

        # Generate fresh ideas using Gemini based on the data
        if GEMINI_KEY:
            try:
                prompt = (
                    f"You are a top-tier YouTube strategy expert advising the tech channel 'BeyondEra Tech'.\n"
                    f"Here is the channel's recent data:\n{json.dumps(own_channel_data, indent=2)}\n\n"
                    f"Here is the data from top competitors:\n{json.dumps(competitor_analysis, indent=2)}\n\n"
                    "Based strictly on this data, suggest 5 highly engaging, specific YouTube shorts content ideas.\n"
                    "Focus on topics competitors are succeeding with or missing topics from our channel.\n"
                    "For each idea, provide a JSON object with 'topic', 'hook', 'script_outline', and 'scene_prompts'.\n"
                    "Return ONLY a valid JSON list of these 5 ideas. Do not include markdown formatting like ```json."
                )
                
                logger.info("Calling Gemini API to generate content ideas...")
                response_text = call_gemini_api(prompt) or ""
                
                # Strip potential markdown from the AI response
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                    
                ideas = json.loads(response_text)
                report['content_ideas'] = ideas
                logger.info("Successfully generated ideas via Gemini.")
            except json.JSONDecodeError:
                logger.error("Failed to parse Gemini response as JSON.")
                report['content_ideas'] = [{"error": "Failed to parse AI response"}]
            except Exception as e:
                logger.error(f"Error generating ideas with Gemini: {e}")
                logger.debug(traceback.format_exc())
                report['content_ideas'] = [{"error": str(e)}]
        else:
            logger.warning("GEMINI_KEY missing, skipping idea generation.")
            report['content_ideas'] = [{"error": "GEMINI_API_KEY not configured."}]

        # Save report to cache to prevent re-running heavy analysis multiple times a day
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        report_file = os.path.join(CACHE_DIR, f'daily_report_{date_str}.json')
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=4)
            logger.info(f"Saved daily report to {report_file}")
        except IOError as e:
            logger.error(f"Failed to write daily report to disk: {e}")
            
        return report

    def get_improvement_suggestions(self) -> Dict[str, Any]:
        """
        Uses Gemini to analyze the daily report and generate improvement suggestions.
        - Focuses on missing topics and competitor strategies.
        - Provides actionable recommendations in both English and Uzbek.
        
        Returns:
            Dict[str, Any]: A dictionary containing English and Uzbek suggestion lists.
        """
        logger.info("Generating improvement suggestions...")
        
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        report_file = os.path.join(CACHE_DIR, f'daily_report_{date_str}.json')
        
        report_data = None
        if os.path.exists(report_file):
            logger.info("Loading existing daily report for suggestions...")
            with open(report_file, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
        else:
            logger.info("No daily report found for today, generating one first...")
            report_data = self.generate_daily_report()

        if not GEMINI_KEY:
            logger.error("Cannot generate suggestions without GEMINI_API_KEY")
            return {"error": "GEMINI_API_KEY not configured"}

        try:
            prompt = (
                f"Analyze the following YouTube intelligence report for BeyondEra Tech:\n"
                f"{json.dumps(report_data, indent=2)}\n\n"
                "Provide highly actionable, strategic improvement suggestions.\n"
                "Focus heavily on:\n"
                "1. Topics that are completely missing from our channel that we MUST cover.\n"
                "2. Specific tactics competitors are executing better (titles, hooks, video duration).\n"
                "3. Immediate actionable steps to improve the next video.\n\n"
                "Provide the response as a JSON object with two keys: 'english' and 'uzbek'.\n"
                "Inside each key, provide a list of strings representing the localized suggestions.\n"
                "Return ONLY valid JSON."
            )
            
            logger.info("Calling Gemini API for localized suggestions...")
            response_text = call_gemini_api(prompt) or ""
            
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
                
            suggestions = json.loads(response_text)
            return suggestions
        except json.JSONDecodeError:
            logger.error("Failed to parse Gemini suggestion response as JSON.")
            return {"error": "Failed to parse AI response"}
        except Exception as e:
            logger.error(f"Error generating suggestions with Gemini: {e}")
            logger.debug(traceback.format_exc())
            return {"error": str(e)}

    def get_todays_best_idea(self) -> Dict[str, Any]:
        """
        Picks the single best content idea for today from the daily report.
        
        Returns:
            Dict[str, Any]: A single content idea dict containing topic, hook, script, scene_prompts.
        """
        logger.info("Getting today's best content idea...")
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        report_file = os.path.join(CACHE_DIR, f'daily_report_{date_str}.json')
        
        report_data = None
        if os.path.exists(report_file):
            with open(report_file, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
        else:
            report_data = self.generate_daily_report()

        ideas = report_data.get('content_ideas', [])
        
        # Validate that we actually have ideas and not an error dictionary
        if not ideas or (len(ideas) > 0 and 'error' in ideas[0]):
            logger.warning("No valid ideas found in report. Returning fallback idea.")
            return {
                "topic": "The Future of Quantum Computing",
                "hook": "What if computers were 100 million times faster?",
                "script_outline": "Quantum computers aren't just faster, they work completely differently. Instead of 1s and 0s, they use qubits.",
                "scene_prompts": ["Glowing quantum chip in a dark room", "Matrix-style code stream transforming"]
            }

        # Select the first idea as the definitive "best" one for the day
        best_idea = ideas[0]
        logger.info(f"Selected best idea: {best_idea.get('topic', 'Unknown')}")
        return best_idea


# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    """
    When run as a standalone script, this will execute the full daily analysis pipeline
    and print the output to standard out.
    """
    analyzer = ChannelAnalyzer()
    
    print("="*50)
    print("Starting Daily YouTube Channel Analysis...")
    print("="*50)
    
    # 1. Generate full daily report
    report = analyzer.generate_daily_report()
    print("\n✅ Daily Report Generated successfully.")
    
    # 2. Get and display improvement suggestions
    print("\n" + "="*50)
    print("Improvement Suggestions (English & Uzbek):")
    print("="*50)
    suggestions = analyzer.get_improvement_suggestions()
    print(json.dumps(suggestions, indent=2, ensure_ascii=False))
    
    # 3. Get and display the best idea for today
    print("\n" + "="*50)
    print("Best Video Idea for Today:")
    print("="*50)
    best_idea = analyzer.get_todays_best_idea()
    print(json.dumps(best_idea, indent=2, ensure_ascii=False))
    
    print("\nAnalysis complete.")
