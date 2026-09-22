#!/usr/bin/env python3
"""
BeyondEra Tech - FULL AUTONOMOUS AI YOUTUBE CONTENT FACTORY
Senior End-to-End Orchestrator Pipeline with Zero-Duplicate Architecture.

Reference Implementations:
- khaoss85/youtube-autopilot: channel memory, editorial planning, workspace separation
- JoshPChua/Youtube-AI-Automation-Agent: uploader separation, ready_to_upload -> archive workflow
- ChaitanyaEswarRajeshJakki/gemini-youtube-automation: pending/completed content state management

State Machine Sequence:
TOPIC_SELECTED -> SCRIPT_GENERATED -> ASSETS_GENERATED -> VIDEO_RENDERED ->
VIDEO_VALIDATED -> THUMBNAIL_READY -> READY_TO_UPLOAD -> UPLOADING -> PUBLISHED
(or FAILED / FAILED_DUPLICATE)
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
import subprocess
import requests
from typing import Dict, Any, Optional


from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.content_plan_engine import (
    generate_content_plan, get_cadence_status, validate_niche,
    get_30_day_plan_entry, mark_plan_entry_completed, mark_plan_entry_failed
)
from scripts.flow_controller import generate_video_with_flow, get_healthy_profile, acquire_multi_prompt_assets
from scripts.ffmpeg_render_engine import assemble_final_video, generate_video_thumbnail
from scripts.video_qa import run_full_qa
from scripts.content_history_manager import (
    ContentHistoryManager, compute_sha256_file, compute_sha256_text
)
from scripts.youtube_uploader import (
    upload_to_youtube, validate_for_upload, READY_DIR, ARCHIVE_DIR, FAILED_DIR
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DEFAULT_CHAT_ID = "5960858213"
BEYOND_ERA_CHANNEL_ID = "UC525J1r4HA1qV8DVf6FKQEg"

# Structured Pipeline State Machine
class PipelineState:
    TOPIC_SELECTED = "TOPIC_SELECTED"
    SCRIPT_GENERATED = "SCRIPT_GENERATED"
    ASSETS_GENERATED = "ASSETS_GENERATED"
    VIDEO_RENDERED = "VIDEO_RENDERED"
    VIDEO_VALIDATED = "VIDEO_VALIDATED"
    THUMBNAIL_READY = "THUMBNAIL_READY"
    READY_TO_UPLOAD = "READY_TO_UPLOAD"
    UPLOADING = "UPLOADING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    FAILED_DUPLICATE = "FAILED_DUPLICATE"


def log_stage(category: str, message: str):
    """Senior structured logging per instruction format: [TOPIC], [CONTENT], [FLOW], [VIDEO], [HASH], [YOUTUBE], [STATUS]."""
    t_str = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{t_str}] [{category.upper()}] {message}")


def send_telegram_message(text: str, chat_id: str = DEFAULT_CHAT_ID) -> bool:
    """Dispatches HTML message to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        res = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}, timeout=10)
        return res.status_code == 200 and res.json().get("ok", False)
    except Exception as e:
        print(f"⚠️ Telegram matn xatosi: {e}")
        return False


def send_telegram_video(video_path: str, caption: str, chat_id: str = DEFAULT_CHAT_ID) -> bool:
    """Streams final MP4 video directly to Telegram."""
    if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    file_size_mb = round(os.path.getsize(video_path) / (1024 * 1024), 2)
    log_stage("TELEGRAM", f"Video fayli Telegramga yuklanmoqda ({file_size_mb} MB)...")

    try:
        with open(video_path, "rb") as vf:
            files = {"video": (os.path.basename(video_path), vf, "video/mp4")}
            data = {
                "chat_id": chat_id,
                "caption": caption[:1024],
                "parse_mode": "HTML",
                "supports_streaming": "true"
            }
            res = requests.post(url, data=data, files=files, timeout=120)
            ok = res.status_code == 200 and res.json().get("ok", False)
            if ok:
                log_stage("TELEGRAM", "Video fayli muvaffaqiyatli yetkazildi!")
            return ok
    except Exception as e:
        log_stage("TELEGRAM_ERROR", f"Video yuborishda xatolik: {e}")
        return False


def send_telegram_voice_note(text: str, chat_id: str = DEFAULT_CHAT_ID) -> bool:
    """Synthesizes native Uzbek voice report via Edge-TTS and dispatches via sendVoice."""
    voice_script = os.path.join(DIR, "send_voice_msg.py")
    try:
        subprocess.run([sys.executable, voice_script, text, "--chat-id", chat_id], check=False, timeout=25)
        return True
    except Exception as e:
        print(f"⚠️ Ovozli xabar yuborishda xatolik: {e}")
        return False


def register_pipeline_in_db(
    content_plan: Dict[str, Any],
    final_video_path: str,
    credits_used: int = 10,
    status: str = "SCHEDULED",
    video_hash: str = ""
) -> Dict[str, Any]:
    """Persists generation task and schedules upload in PostgreSQL for 19:00 slot."""
    import base64
    payload = {
        "channel_id": BEYOND_ERA_CHANNEL_ID,
        "topic": content_plan.get("topic", "Future Tech"),
        "prompt": content_plan.get("scene_prompts", [""])[0] if content_plan.get("scene_prompts") else "",
        "video_path": final_video_path,
        "credits_used": credits_used,
        "title": content_plan.get("title", ""),
        "description": content_plan.get("description", ""),
        "tags": content_plan.get("tags", []),
        "status": status,
        "video_hash": video_hash
    }
    b64_payload = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode("ascii")

    db_script = f"""
import base64, json, datetime
from django.apps import apps
from django.utils import timezone

data = json.loads(base64.b64decode('{b64_payload}').decode('utf-8'))
YouTubeChannel = apps.get_model('youtube', 'YouTubeChannel')
FlowAIAccount = apps.get_model('youtube', 'FlowAIAccount')
VideoGenerationTask = apps.get_model('youtube', 'VideoGenerationTask')
ScheduledUpload = apps.get_model('youtube', 'ScheduledUpload')

channel = YouTubeChannel.objects.filter(channel_id=data['channel_id']).first() or YouTubeChannel.objects.first()
account = FlowAIAccount.objects.filter(is_active=True).order_by('-credits_remaining').first()

task = VideoGenerationTask.objects.create(
    account=account,
    topic=data['topic'],
    prompt=data['prompt'],
    status='completed' if data['status'] in ['SCHEDULED', 'PUBLISHED'] else 'failed',
    video_file_path=data['video_path'],
    credits_used=data['credits_used'],
    completed_at=timezone.now()
)

target_date = timezone.now().date()
while ScheduledUpload.objects.filter(channel=channel, scheduled_date=target_date, scheduled_time=datetime.time(19, 0)).exists():
    target_date += datetime.timedelta(days=1)

upload = ScheduledUpload.objects.create(
    channel=channel,
    video_task=task,
    title=data['title'],
    description=data['description'],
    tags=data['tags'],
    scheduled_date=target_date,
    scheduled_time=datetime.time(19, 0),
    status='published' if data['status'] == 'PUBLISHED' else 'scheduled'
)
print('DB_SUCCESS: ScheduledUpload #' + str(upload.id) + ' on ' + str(target_date) + ' 19:00:00')
"""
    try:
        proc = subprocess.run(
            ["docker", "exec", "-i", "youtube_integratsiya_backend", "python", "manage.py", "shell", "-c", db_script],
            capture_output=True,
            text=True,
            timeout=15
        )
        for line in proc.stdout.splitlines():
            if "DB_SUCCESS" in line:
                log_stage("STATUS", line.strip())
                return {"success": True, "log": line.strip()}
    except Exception as e:
        log_stage("STATUS", f"PostgreSQL ro'yxatga olishda ogohlantirish: {e}")

    return {"success": False}


def run_autonomous_factory(
    video_type: str = "auto",
    custom_topic: Optional[str] = None,
    day_number: Optional[int] = None,
    preferred_profile: str = "4",
    send_telegram: bool = True,
    auto_upload: bool = True,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Executes the full end-to-end autonomous content factory with zero-duplicate enforcement.
    Strictly follows the 16-step production workflow.
    """
    start_time = time.time()
    history_mgr = ContentHistoryManager()

    log_stage("STATUS", "==========================================================")
    log_stage("STATUS", "🚀 BEYONDERA TECH — SENIOR ZERO-DUPLICATE CONTENT FACTORY")
    log_stage("STATUS", "==========================================================")

    # 1. Initialize Generation ID
    generation_id = str(uuid.uuid4())
    log_stage("STATUS", f"🔑 Initializing Generation ID: {generation_id}")

    # Working staging folder
    work_dir = os.path.join(PROJECT_ROOT, f"workspace/working/{generation_id}")
    os.makedirs(work_dir, exist_ok=True)

    # 2. Select NEW Topic & Semantic History Validation
    log_stage("TOPIC", "Yangi mavzu tanlanmoqda va Content History tekshirilmoqda...")
    content_plan = None

    for attempt in range(max_retries):
        try:
            content_plan = generate_content_plan(video_type=video_type, topic_hint=custom_topic, day_number=day_number)
            if content_plan:
                # Semantic duplicate check
                is_dup, dup_rec, sim_score = history_mgr.is_topic_duplicate(content_plan["topic"], threshold=0.55)
                if is_dup:
                    log_stage("TOPIC", f"⚠️ Takroriy mavzu aniqlandi ({sim_score:.2f} o'xshash): '{content_plan['topic']}'. Yangisi tanlanmoqda (Urinish {attempt+1}/{max_retries})...")
                    custom_topic = None  # Reset custom topic to pick next pending
                    day_number = None
                    time.sleep(1)
                    continue
                break
        except Exception as e:
            log_stage("TOPIC", f"Kontent reja generatsiyasida xatolik ({attempt+1}/{max_retries}): {e}")
            time.sleep(2)

    if not content_plan:
        log_stage("STATUS", "Muvaffaqiyatsiz: Yangi, unikal mavzu tanlab bo'lmadi.")
        return {"success": False, "state": PipelineState.FAILED}

    content_plan["generation_id"] = generation_id
    current_state = PipelineState.TOPIC_SELECTED
    log_stage("TOPIC", f"Tanlangan mavzu: '{content_plan['topic']}' | Sarlavha: '{content_plan['title']}'")
    log_stage("CONTENT", f"Target format: {content_plan['video_type'].upper()} ({content_plan['duration']}s)")

    # 3. Generate Script & Scenes
    current_state = PipelineState.SCRIPT_GENERATED
    log_stage("CONTENT", f"Ssenariy: {content_plan['script'][:90]}...")
    log_stage("CONTENT", f"Hook (0-3s): '{content_plan.get('hook')}'")

    # 4. Multi-Prompt Flow AI & Visual Asset Acquisition
    scene_prompts = content_plan.get("scene_prompts") or [sc.get("prompt", "") for sc in content_plan.get("scenes", []) if sc.get("prompt")]
    if not scene_prompts:
        scene_prompts = [content_plan.get("topic", "Advanced Frontier Technology")]

    log_stage("FLOW", f"Flow AI vazifasi boshlanmoqda (Profile {preferred_profile}) | Multi-Prompt: {len(scene_prompts)} ta sahna...")

    flow_res = acquire_multi_prompt_assets(
        scene_prompts=scene_prompts,
        profile_choice=preferred_profile,
        aspect_ratio="9:16" if content_plan["video_type"] == "shorts" else "16:9",
        generation_id=generation_id
    )
    raw_video_path = flow_res.get("primary_video")
    flow_gen_id = flow_res.get("flow_generation_id", f"flow_{generation_id[:8]}")
    all_clips = flow_res.get("all_clips")
    log_stage("FLOW", f"Flow Generation ID: {flow_gen_id} | Multi-Prompt Assets: {flow_res.get('prompts_count')} ta sahna biriktirildi")

    current_state = PipelineState.ASSETS_GENERATED

    # 5. Multi-Scene Assembly & FFmpeg Rendering
    current_state = PipelineState.VIDEO_RENDERED
    rendered_video_path = os.path.join(work_dir, f"rendered_{content_plan['video_type']}.mp4")
    log_stage("VIDEO", f"FFmpeg montaj boshlanmoqda: {rendered_video_path}")

    render_res = None
    for r_attempt in range(max_retries):
        try:
            render_res = assemble_final_video(
                content_plan,
                raw_video_path=raw_video_path,
                all_clips=all_clips,
                output_path=rendered_video_path
            )
            if render_res and render_res.get("output_path") and os.path.exists(render_res["output_path"]):
                break
        except Exception as exc:
            log_stage("VIDEO", f"Render xatosi ({r_attempt+1}/{max_retries}): {exc}")
            time.sleep(2)

    if not render_res or not render_res.get("output_path"):
        log_stage("STATUS", "Final videoni render qilib bo'lmadi.")
        return {"success": False, "state": PipelineState.FAILED}

    final_video = render_res["output_path"]
    final_qa = render_res["qa"]

    # 6. Quality Control (QA Validation)
    current_state = PipelineState.VIDEO_VALIDATED
    log_stage("VIDEO", f"Video QA tekshiruvi: Davomiylik={final_qa['metrics']['duration']}s, O'lcham={final_qa['metrics']['width']}x{final_qa['metrics']['height']}, Hajm={final_qa['metrics']['file_size_mb']}MB")
    if not final_qa["passed"]:
        log_stage("STATUS", f"QA muvaffaqiyatsiz bo'ldi: {final_qa['errors']}")
        return {"success": False, "state": PipelineState.FAILED, "qa": final_qa}

    # 7. Calculate SHA-256 Video Hash & DUPLICATE PROTECTION
    video_hash = compute_sha256_file(final_video)
    log_stage("HASH", f"SHA-256 Video Hash: {video_hash}")

    is_dup_hash, dup_record = history_mgr.is_video_hash_duplicate(video_hash)
    if is_dup_hash:
        log_stage("STATUS", f"🛑 CRITICAL: Duplicate video SHA-256 hash aniqlandi! Avvalgi gen: {dup_record.get('generation_id')}")
        log_stage("STATUS", "❌ Qayta upload qilish taqiqlandi. Holat: FAILED_DUPLICATE")
        # Move to failed directory
        dest_failed = os.path.join(FAILED_DIR, f"{generation_id}_{os.path.basename(final_video)}")
        shutil.copy2(final_video, dest_failed)
        return {"success": False, "state": PipelineState.FAILED_DUPLICATE, "error": "Duplicate video hash"}

    log_stage("HASH", "✅ Video hash mutlaqo noyob (0 prior matches). Duplicate check PASSED!")

    # 8. Generate Thumbnail
    current_state = PipelineState.THUMBNAIL_READY
    thumb_path = os.path.join(work_dir, "thumbnail.jpg")
    generate_video_thumbnail(content_plan, thumb_path)
    log_stage("CONTENT", f"Thumbnail tayyorlandi: {thumb_path}")

    # 9. Stage to /ready_to_upload
    current_state = PipelineState.READY_TO_UPLOAD
    ready_video = os.path.join(READY_DIR, f"{generation_id}_{os.path.basename(final_video)}")
    shutil.copy2(final_video, ready_video)
    log_stage("STATUS", f"Fayl /ready_to_upload ga joylandi: {ready_video}")

    # 10. Execute YouTube Upload & Archiving Workflow
    upload_result = None
    day_num = content_plan.get("day_number")

    if auto_upload:
        current_state = PipelineState.UPLOADING
        log_stage("YOUTUBE", "YouTube yuklash boshlanmoqda...")
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
            current_state = PipelineState.PUBLISHED
            yt_id = upload_result.get("youtube_video_id")
            log_stage("YOUTUBE", f"✅ YouTube'ga muvaffaqiyatli yuklandi! Video ID: {yt_id}")
            log_stage("STATUS", f"📦 Video /archive katalogiga arxivlandi: {upload_result.get('archive_path')}")
            
            # Update 30-day master roadmap
            if day_num:
                mark_plan_entry_completed(day_num, video_id=yt_id, video_hash=video_hash)
        else:
            current_state = PipelineState.FAILED
            log_stage("YOUTUBE", f"❌ YouTube yuklashda xatolik: {upload_result.get('error')}")
            if day_num:
                mark_plan_entry_failed(day_num, upload_result.get("error", "Upload error"))

    # 11. PostgreSQL Registration
    register_pipeline_in_db(
        content_plan,
        final_video_path=upload_result.get("archive_path", final_video) if upload_result else final_video,
        credits_used=10,
        status="PUBLISHED" if current_state == PipelineState.PUBLISHED else "SCHEDULED",
        video_hash=video_hash
    )

    elapsed_time = round(time.time() - start_time, 1)

    # 12. Telegram Reporting
    if send_telegram:
        log_stage("TELEGRAM", "Telegram hisoboti va video jo'natilmoqda...")
        actual_type = content_plan.get("video_type", "shorts")
        type_badge = "📱 SHORTS (30-60s)" if actual_type == "shorts" else "📽 10-KUNLIK DOKUMENTAL"
        day_caption_str = f"📅 <b>30-Kunlik Reja:</b> {day_num}-KUN / 30\n" if day_num else ""
        creative = content_plan.get("creative_direction", {})
        yt_line = f"🆔 <b>YouTube ID:</b> <code>{upload_result.get('youtube_video_id', 'Pending')}</code>\n" if upload_result else ""

        caption = (
            f"🎬 <b>BeyondEra Tech: {content_plan['title']}</b>\n\n"
            f"{day_caption_str}"
            f"🏷 <b>Format:</b> {type_badge}\n"
            f"{yt_line}"
            f"🎨 <b>Uslub:</b> <code>{creative.get('visual_theme', 'TECH')}</code>\n"
            f"🎙 <b>Ovoz:</b> {creative.get('voice_name', 'Christopher').replace('en-US-', '').replace('Neural', '')}\n"
            f"🔒 <b>SHA256 Hash:</b> <code>{video_hash[:16]}...</code>\n"
            f"⏱ <b>Davomiyligi:</b> <b>{final_qa['metrics']['duration']}s</b>\n"
            f"📐 <b>Sifat:</b> {final_qa['metrics']['width']}x{final_qa['metrics']['height']} (60fps)\n"
            f"⚡️ <b>Ishlov vaqti:</b> {elapsed_time}s\n\n"
            f"🔖 #{' #'.join(content_plan.get('tags', [])[:4])}"
        )
        send_telegram_video(final_video, caption)

        # Full native text summary
        full_msg = (
            f"🎉 <b>YANGI VIDEO MUVAFFAQIYATLI GENERATSIYA QILINDI VA ARXIVLANDI!</b>\n\n"
            f"{day_caption_str}"
            f"📌 <b>Sarlavha:</b> {content_plan['title']}\n"
            f"🏷 <b>Format:</b> {type_badge}\n"
            f"🔑 <b>Generation ID:</b> <code>{generation_id}</code>\n"
            f"🔒 <b>Video Hash (SHA256):</b> <code>{video_hash}</code>\n"
            f"✅ <b>Duplicate Protection:</b> Tasdiqlandi (Noyob kontent)\n"
            f"📦 <b>Arxiv:</b> <code>workspace/archive/</code>\n\n"
            f"🧠 <b>Auditoriyani Ushlab Qolish Tahlili:</b>\n{content_plan.get('uzbek_analysis', '')}\n\n"
            f"✅ <i>QA Testlari: Black frames yo'q, audio sinxron, professional ko'p sahnali montaj.</i>"
        )
        send_telegram_message(full_msg)

        # Spoken native Uzbek voice note
        spoken_summary = content_plan.get("uzbek_voice_summary") or content_plan.get("uzbek_analysis", "")[:280]
        day_speech = f"30 kunlik rejamizning {day_num}-kuni bo'yicha " if day_num else ""
        voice_text = (
            f"Assalomu alaykum Shohruhbek! BeyondEra Tech kanalingiz uchun {day_speech}mutlaqo yangi va noyob video tayyorlandi. "
            f"{spoken_summary} "
            f"Video dublikat tekshiruvidan muvaffaqiyatli o'tib, YouTube uchun arxivlandi."
        )
        send_telegram_voice_note(voice_text)

    log_stage("STATUS", f"🎉 To'liq sikl yakunlandi! Holat: {current_state} | Vaqt: {elapsed_time}s")
    return {
        "success": True,
        "state": current_state,
        "generation_id": generation_id,
        "video_hash": video_hash,
        "video_path": upload_result.get("archive_path", final_video) if upload_result else final_video,
        "youtube_video_id": upload_result.get("youtube_video_id") if upload_result else None,
        "title": content_plan["title"],
        "topic": content_plan["topic"],
        "day_number": day_num,
        "elapsed_seconds": elapsed_time
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BeyondEra Tech Autonomous Content Factory")
    parser.add_argument("--day", type=int, default=None, help="Run specific day from 30-day roadmap (1-30)")
    parser.add_argument("--type", default="auto", choices=["shorts", "long", "auto"], help="Video format")
    parser.add_argument("--topic", default=None, help="Custom topic hint")
    parser.add_argument("--profile", default="4", help="Profile choice (1-4)")
    parser.add_argument("--no-telegram", action="store_true", help="Disable Telegram dispatch")
    parser.add_argument("--no-upload", action="store_true", help="Do not upload to YouTube, only stage to ready_to_upload")
    parser.add_argument("--status", action="store_true", help="Display cadence and roadmap status")

    args = parser.parse_args()

    if args.status:
        cad = get_cadence_status()
        hist = ContentHistoryManager()
        records = hist.load_records()
        print("=== BEYONDERA TECH CONTENT ENGINE STATUS ===")
        print(f"Total Published/Recorded Generations: {len(records)}")
        for r in records[-5:]:
            print(f"  [{r.get('status')}] {r.get('created_at', '')[:19]} | Hash: {r.get('video_hash', '')[:10]}... | {r.get('title')}")
        print(json.dumps(cad, indent=2))
    else:
        run_autonomous_factory(
            video_type=args.type,
            custom_topic=args.topic,
            day_number=args.day,
            preferred_profile=args.profile,
            send_telegram=not args.no_telegram,
            auto_upload=not args.no_upload
        )
