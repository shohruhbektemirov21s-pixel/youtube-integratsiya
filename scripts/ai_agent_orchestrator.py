#!/usr/bin/env python3
"""
BeyondEra Tech - Central AI Agent Orchestrator Architecture.
Unifies all specialized autonomous agents into a resilient, self-healing pipeline:
1. Analytics Agent (Feedback loop & trend detection)
2. Content Agent (Topic discovery, single-niche, 30-day roadmap)
3. Research Agent (Browser automation, fact cross-checking, source tiering)
4. Script Agent (Scene-by-scene storyboard, narration, hook, CTA)
5. Voice Agent (Edge-TTS natural speech with duration synchronization)
6. Visual Agent (Detailed scene visual prompts)
7. Video Agent (Flow AI acquisition & unique clip generation)
8. Editor Agent (FFmpeg dynamic multi-scene compositing, subtitles, ducking)
9. QC Agent (Duration, resolution, black-frame, and audio integrity)
10. Thumbnail Agent (Topic-aligned high-contrast mobile-first art)
11. Deduplication Agent (SHA-256 video hash & semantic deduplication)
12. YouTube Agent (YouTube Data API v3 upload, archiving, scheduling)
13. Memory Agent (Permanent content memory & state machine persistence)
"""

import os
import sys
import json
import time
import uuid
import shutil
import logging
import argparse
import datetime
from typing import Dict, Any, Optional

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.browser_research_agent import DeepResearchAgent
from scripts.analytics_feedback_agent import AnalyticsFeedbackAgent
from scripts.content_plan_engine import (
    generate_content_plan, get_cadence_status, validate_niche,
    get_30_day_plan_entry, mark_plan_entry_completed, mark_plan_entry_failed,
    get_next_pending_plan_entry
)
from scripts.flow_controller import generate_video_with_flow, acquire_multi_prompt_assets
from scripts.ffmpeg_render_engine import assemble_final_video, generate_video_thumbnail
from scripts.video_qa import run_full_qa
from scripts.content_history_manager import ContentHistoryManager, compute_sha256_file
from scripts.youtube_uploader import upload_to_youtube, READY_DIR, ARCHIVE_DIR, FAILED_DIR
from scripts.auto_video_pipeline import send_telegram_message, send_telegram_video, send_telegram_voice_note

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [ORCHESTRATOR] %(message)s"
)
logger = logging.getLogger("CentralOrchestrator")


class JobState:
    NEW = "NEW"
    RESEARCHING = "RESEARCHING"
    RESEARCHED = "RESEARCHED"
    SCRIPTING = "SCRIPTING"
    SCRIPT_READY = "SCRIPT_READY"
    GENERATING_ASSETS = "GENERATING_ASSETS"
    VIDEO_RENDERING = "VIDEO_RENDERING"
    VIDEO_READY = "VIDEO_READY"
    QC_PASSED = "QC_PASSED"
    READY_TO_UPLOAD = "READY_TO_UPLOAD"
    UPLOADING = "UPLOADING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    FAILED_DUPLICATE = "FAILED_DUPLICATE"


class CentralAIOrchestrator:
    """
    Master Autonomous Orchestrator managing specialized sub-agents with state checkpointing
    and failure recovery.
    """

    def __init__(self, preferred_profile: str = "4"):
        self.preferred_profile = preferred_profile
        self.research_agent = DeepResearchAgent()
        self.analytics_agent = AnalyticsFeedbackAgent()
        self.history_mgr = ContentHistoryManager()

    def run_full_autonomous_cycle(
        self,
        video_type: str = "auto",
        custom_topic: Optional[str] = None,
        day_number: Optional[int] = None,
        auto_upload: bool = True,
        send_telegram: bool = True
    ) -> Dict[str, Any]:
        """
        Executes end-to-end multi-agent publishing cycle with failure checkpointing.
        """
        start_time = time.time()
        generation_id = str(uuid.uuid4())
        work_dir = os.path.join(PROJECT_ROOT, f"workspace/working/{generation_id}")
        os.makedirs(work_dir, exist_ok=True)
        job_checkpoint_file = os.path.join(work_dir, "job_state.json")

        job_data = {
            "generation_id": generation_id,
            "state": JobState.NEW,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "video_type": video_type
        }
        self._save_checkpoint(job_checkpoint_file, job_data)

        logger.info("=" * 75)
        logger.info(f"🤖 [CENTRAL ORCHESTRATOR] Initialized Autonomous Cycle (ID: {generation_id})")
        logger.info("=" * 75)

        # ---------------------------------------------------------
        # STAGE 1: Analytics Loop & Strategy Guidance
        # ---------------------------------------------------------
        logger.info("📈 [STAGE 1] Analytics Agent: Reading audience signals...")
        analytics_insights = self.analytics_agent.analyze_channel_performance()
        job_data["analytics"] = analytics_insights
        self._save_checkpoint(job_checkpoint_file, job_data)

        # ---------------------------------------------------------
        # STAGE 2: Content Discovery & Semantic History Check
        # ---------------------------------------------------------
        logger.info("💡 [STAGE 2] Content Agent: Selecting un-used topic from 30-day roadmap...")
        plan_entry = None
        if day_number:
            plan_entry = get_30_day_plan_entry(day_number)
        elif custom_topic is None:
            plan_entry = get_next_pending_plan_entry()

        effective_topic = custom_topic or (plan_entry.get("topic") if plan_entry else "Next-Gen Humanoid Robots & Physical AI")
        effective_day = plan_entry.get("day") if plan_entry else day_number

        # Duplicate Topic Check
        is_dup_topic, dup_rec, sim_score = self.history_mgr.is_topic_duplicate(effective_topic, threshold=0.55)
        if is_dup_topic:
            logger.warning(f"⚠️ [CONTENT AGENT] Topic '{effective_topic}' is semantically duplicate with '{dup_rec.get('topic')}' ({sim_score:.2f}). Finding alternative...")
            # Pick next available pending entry
            plan_entry = get_next_pending_plan_entry()
            if plan_entry:
                effective_topic = plan_entry.get("topic")
                effective_day = plan_entry.get("day")

        job_data["topic"] = effective_topic
        job_data["day_number"] = effective_day
        logger.info(f"✅ [CONTENT AGENT] Locked Topic: '{effective_topic}' (Day {effective_day})")

        # ---------------------------------------------------------
        # STAGE 3: Browser Research Agent (Deep Fact Synthesis)
        # ---------------------------------------------------------
        job_data["state"] = JobState.RESEARCHING
        self._save_checkpoint(job_checkpoint_file, job_data)
        logger.info(f"🔬 [STAGE 3] Browser Research Agent: Investigating web for: '{effective_topic}'...")

        research_dossier = self.research_agent.conduct_research(effective_topic)
        job_data["research"] = research_dossier
        job_data["state"] = JobState.RESEARCHED
        self._save_checkpoint(job_checkpoint_file, job_data)

        # ---------------------------------------------------------
        # STAGE 4: Script & Storyboard Agent
        # ---------------------------------------------------------
        job_data["state"] = JobState.SCRIPTING
        self._save_checkpoint(job_checkpoint_file, job_data)
        logger.info("✍️ [STAGE 4] Script Agent: Creating scene-by-scene storyboard from verified research...")

        content_plan = generate_content_plan(
            video_type=video_type,
            topic_hint=effective_topic,
            day_number=effective_day
        )
        content_plan["generation_id"] = generation_id

        # Enhance voiceover and scenes with verified facts if available
        if research_dossier.get("facts"):
            content_plan["research_facts"] = research_dossier["facts"]
            content_plan["research_sources"] = [s["url"] for s in research_dossier.get("sources", [])]

        job_data["content_plan"] = content_plan
        job_data["state"] = JobState.SCRIPT_READY
        self._save_checkpoint(job_checkpoint_file, job_data)
        logger.info(f"✅ [SCRIPT AGENT] Script ready: '{content_plan['title']}' ({len(content_plan.get('scenes', []))} scenes)")

        # ---------------------------------------------------------
        # STAGE 5: Creative Multi-Prompt Visual & Flow AI Video Acquisition
        # ---------------------------------------------------------
        job_data["state"] = JobState.GENERATING_ASSETS
        self._save_checkpoint(job_checkpoint_file, job_data)
        logger.info("🎬 [STAGE 5] Visual & Video Agent: Triggering Multi-Prompt Flow asset acquisition...")

        scene_prompts = content_plan.get("scene_prompts") or [sc.get("prompt", "") for sc in content_plan.get("scenes", []) if sc.get("prompt")]
        if not scene_prompts:
            scene_prompts = [content_plan.get("topic", "Advanced Frontier Technology")]

        flow_res = acquire_multi_prompt_assets(
            scene_prompts=scene_prompts,
            profile_choice=self.preferred_profile,
            aspect_ratio="9:16" if content_plan.get("video_type") == "shorts" else "16:9",
            generation_id=generation_id
        )
        raw_video_path = flow_res.get("primary_video")
        flow_gen_id = flow_res.get("flow_generation_id", f"FLOW_{generation_id[:8]}")
        all_clips = flow_res.get("all_clips")
        logger.info(f"🎨 [STAGE 5] Multi-prompt assets ready: {flow_res.get('prompts_count')} scenes mapped to creative visual themes.")

        # ---------------------------------------------------------
        # STAGE 6: Editor Agent (FFmpeg Assembly, TTS, Subtitles)
        # ---------------------------------------------------------
        job_data["state"] = JobState.VIDEO_RENDERING
        self._save_checkpoint(job_checkpoint_file, job_data)
        rendered_output = os.path.join(work_dir, f"rendered_{content_plan['video_type']}.mp4")
        logger.info(f"🎞 [STAGE 6] Editor Agent: Rendering multi-scene dynamic video -> {rendered_output}")

        render_res = assemble_final_video(
            content_plan=content_plan,
            raw_video_path=raw_video_path,
            all_clips=all_clips,
            output_path=rendered_output
        )

        final_video = render_res["output_path"]
        job_data["video_path"] = final_video
        job_data["state"] = JobState.VIDEO_READY
        self._save_checkpoint(job_checkpoint_file, job_data)

        # ---------------------------------------------------------
        # STAGE 7: Quality Control (QC Agent)
        # ---------------------------------------------------------
        logger.info("🔍 [STAGE 7] QC Agent: Running full integrity & audio verification...")
        qa_result = render_res["qa"]
        if not qa_result["passed"]:
            logger.error(f"❌ [QC AGENT] Failed verification: {qa_result['errors']}")
            job_data["state"] = JobState.FAILED
            self._save_checkpoint(job_checkpoint_file, job_data)
            return {"success": False, "state": JobState.FAILED, "error": qa_result["errors"]}

        job_data["state"] = JobState.QC_PASSED
        logger.info(f"✅ [QC AGENT] Passed! Duration={qa_result['metrics']['duration']}s, Res={qa_result['metrics']['width']}x{qa_result['metrics']['height']}")

        # ---------------------------------------------------------
        # STAGE 8: Thumbnail Agent
        # ---------------------------------------------------------
        logger.info("🖼 [STAGE 8] Thumbnail Agent: Generating high-contrast clickable visual...")
        thumb_path = os.path.join(work_dir, "thumbnail.jpg")
        generate_video_thumbnail(content_plan, thumb_path)
        job_data["thumbnail_path"] = thumb_path

        # ---------------------------------------------------------
        # STAGE 9: SHA-256 Video Hash & Deduplication Agent
        # ---------------------------------------------------------
        video_hash = compute_sha256_file(final_video)
        job_data["video_hash"] = video_hash
        logger.info(f"🔒 [STAGE 9] Deduplication Agent: SHA-256 Hash = {video_hash}")

        is_dup_hash, dup_record = self.history_mgr.is_video_hash_duplicate(video_hash)
        if is_dup_hash:
            logger.error(f"🛑 [DEDUP AGENT] CRITICAL: Duplicate video hash detected! Prior gen: {dup_record.get('generation_id')}")
            dest_failed = os.path.join(FAILED_DIR, f"{generation_id}_{os.path.basename(final_video)}")
            shutil.copy2(final_video, dest_failed)
            job_data["state"] = JobState.FAILED_DUPLICATE
            self._save_checkpoint(job_checkpoint_file, job_data)
            return {"success": False, "state": JobState.FAILED_DUPLICATE, "error": "Duplicate video hash"}

        logger.info("✅ [DEDUP AGENT] Video hash is 100% strictly UNIQUE.")

        # ---------------------------------------------------------
        # STAGE 10: YouTube Agent (Staging, Upload & Archiving)
        # ---------------------------------------------------------
        job_data["state"] = JobState.READY_TO_UPLOAD
        ready_video = os.path.join(READY_DIR, f"{generation_id}_{os.path.basename(final_video)}")
        shutil.copy2(final_video, ready_video)

        upload_result = None
        if auto_upload:
            job_data["state"] = JobState.UPLOADING
            self._save_checkpoint(job_checkpoint_file, job_data)
            logger.info("🚀 [STAGE 10] YouTube Agent: Uploading video and staging to archive...")

            meta_package = {
                "generation_id": generation_id,
                "title": content_plan["title"],
                "topic": content_plan["topic"],
                "script": content_plan["script"],
                "prompt": scene_prompts[0] if scene_prompts else content_plan.get("topic", ""),
                "scene_prompts": scene_prompts,
                "flow_generation_id": flow_gen_id,
                "video_type": content_plan["video_type"],
                "tags": content_plan.get("tags", []),
                "description": content_plan.get("description", "")
            }
            upload_result = upload_to_youtube(ready_video, meta_package, thumbnail_path=thumb_path)

            if upload_result.get("success"):
                job_data["state"] = JobState.PUBLISHED
                job_data["youtube_video_id"] = upload_result.get("youtube_video_id")
                job_data["archive_path"] = upload_result.get("archive_path")
                if effective_day:
                    mark_plan_entry_completed(effective_day, video_id=upload_result.get("youtube_video_id"), video_hash=video_hash)
            else:
                job_data["state"] = JobState.FAILED
                if effective_day:
                    mark_plan_entry_failed(effective_day, upload_result.get("error", "Upload error"))

        self._save_checkpoint(job_checkpoint_file, job_data)
        elapsed = round(time.time() - start_time, 1)

        # ---------------------------------------------------------
        # STAGE 11: Telegram Notification & Spoken Report
        # ---------------------------------------------------------
        if send_telegram:
            logger.info("📱 [STAGE 11] Dispatching Telegram notifications...")
            yt_id = upload_result.get("youtube_video_id") if upload_result else "Staged"
            caption = (
                f"🎬 <b>BeyondEra Tech: {content_plan['title']}</b>\n\n"
                f"📅 <b>Kun:</b> {effective_day} / 30\n"
                f"🆔 <b>YouTube ID:</b> <code>{yt_id}</code>\n"
                f"🔬 <b>Tadqiqot faktlari:</b> {len(research_dossier.get('facts', []))} ta tasdiqlangan fakt\n"
                f"🔒 <b>SHA256:</b> <code>{video_hash[:16]}...</code>\n"
                f"⏱ <b>Davomiyligi:</b> <b>{qa_result['metrics']['duration']}s</b>\n"
                f"⚡️ <b>Ishlov vaqti:</b> {elapsed}s"
            )
            send_telegram_video(final_video, caption)

            full_msg = (
                f"🤖 <b>CENTRAL AI ORCHESTRATOR — TO'LIQ SIKL YAKUNLANDI!</b>\n\n"
                f"📌 <b>Mavzu:</b> {effective_topic}\n"
                f"🔬 <b>Research ID:</b> <code>{research_dossier.get('research_id')}</code>\n"
                f"🔑 <b>Generation ID:</b> <code>{generation_id}</code>\n"
                f"🔒 <b>Video Hash:</b> <code>{video_hash}</code>\n"
                f"📦 <b>Arxiv:</b> <code>workspace/archive/</code>\n"
                f"✅ <b>Holati:</b> {job_data['state']}\n\n"
                f"🌐 <i>Browser Agent, Research Agent, Script Agent, Video Agent va YouTube Agent to'liq avtonom sinxronlashdi.</i>"
            )
            send_telegram_message(full_msg)

        logger.info(f"🎉 [ORCHESTRATOR] Cycle finished with state: {job_data['state']} in {elapsed}s")
        return {
            "success": job_data["state"] == JobState.PUBLISHED,
            "state": job_data["state"],
            "generation_id": generation_id,
            "topic": effective_topic,
            "title": content_plan["title"],
            "video_hash": video_hash,
            "video_path": upload_result.get("archive_path", final_video) if upload_result else final_video,
            "youtube_video_id": upload_result.get("youtube_video_id") if upload_result else None,
            "research_id": research_dossier.get("research_id"),
            "elapsed_seconds": elapsed
        }

    def _save_checkpoint(self, path: str, data: Dict[str, Any]):
        try:
            data["updated_at"] = datetime.datetime.now().isoformat()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Central AI Agent Orchestrator")
    parser.add_argument("--day", type=int, default=None, help="Specific day from roadmap")
    parser.add_argument("--type", default="shorts", choices=["shorts", "long", "auto"])
    parser.add_argument("--topic", default=None, help="Custom research topic")
    parser.add_argument("--profile", default="4", help="Flow Chrome Profile")
    parser.add_argument("--no-telegram", action="store_true")
    parser.add_argument("--no-upload", action="store_true")

    args = parser.parse_args()
    orchestrator = CentralAIOrchestrator(preferred_profile=args.profile)
    res = orchestrator.run_full_autonomous_cycle(
        video_type=args.type,
        custom_topic=args.topic,
        day_number=args.day,
        auto_upload=not args.no_upload,
        send_telegram=not args.no_telegram
    )
    print(json.dumps(res, indent=2))
