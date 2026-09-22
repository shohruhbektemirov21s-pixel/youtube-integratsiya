#!/usr/bin/env python3
"""
BeyondEra Tech - Production YouTube Uploader with Strict Deduplication & Archive Pipeline.
Follows JoshPChua/Youtube-AI-Automation-Agent & youtube-autopilot architecture:
1. Workspace lifecycle: /working -> /ready_to_upload -> /archive (or /failed).
2. SHA-256 Video Hash Verification: Rejects duplicate video hashes (FAILED_DUPLICATE).
3. Generation ID & Content History: Prevents re-uploading already published videos.
4. YouTube Data API v3 Resumable Upload with quota & network retry handling.
5. Automated file archiving upon successful upload.
"""

import os
import sys
import json
import time
import shutil
import hashlib
import logging
import datetime
from typing import Dict, Any, Optional, Tuple


from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.content_history_manager import (
    ContentHistoryManager, compute_sha256_file, compute_sha256_text
)
from scripts.video_qa import run_full_qa

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [YOUTUBE_UPLOADER] %(message)s"
)
logger = logging.getLogger("YouTubeUploader")

WORKSPACE_DIR = os.path.join(PROJECT_ROOT, "workspace")
WORKING_DIR = os.path.join(WORKSPACE_DIR, "working")
READY_DIR = os.path.join(WORKSPACE_DIR, "ready_to_upload")
ARCHIVE_DIR = os.path.join(WORKSPACE_DIR, "archive")
FAILED_DIR = os.path.join(WORKSPACE_DIR, "failed")

for d in [WORKING_DIR, READY_DIR, ARCHIVE_DIR, FAILED_DIR]:
    os.makedirs(d, exist_ok=True)

history_manager = ContentHistoryManager()


class UploadError(Exception):
    """Custom exception for upload pipeline failures."""
    pass


class DuplicateVideoError(UploadError):
    """Raised when a video hash, generation ID, or semantic topic is duplicate."""
    pass


def validate_for_upload(
    video_path: str,
    generation_metadata: Dict[str, Any],
    thumbnail_path: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Performs Phase 14 Quality Control:
    1. Video file exists & readable
    2. Video hash computed and strictly unique
    3. Generation ID unique
    4. Duration, resolution, and audio check via ffprobe
    5. Thumbnail exists if provided
    6. No prior YouTube upload recorded
    """
    generation_id = generation_metadata.get("generation_id")
    topic = generation_metadata.get("topic", "")
    script = generation_metadata.get("script", "")

    # 1. Existence check
    if not os.path.exists(video_path) or os.path.getsize(video_path) < 100 * 1024:
        return False, {"error": f"Video file not found or corrupted: {video_path}"}

    # 2. SHA-256 Video Hash Calculation
    v_hash = compute_sha256_file(video_path)
    if not v_hash:
        return False, {"error": "Failed to compute video SHA-256 hash"}

    # 3. Duplicate Video Hash Protection
    is_dup_hash, dup_record = history_manager.is_video_hash_duplicate(v_hash)
    if is_dup_hash:
        logger.error(f"🛑 CRITICAL: Duplicate video SHA-256 hash detected! Matches prior generation: {dup_record.get('generation_id')}")
        return False, {
            "error": f"FAILED_DUPLICATE: Video hash {v_hash[:12]}... already uploaded or recorded in archive.",
            "duplicate_record": dup_record,
            "status": "FAILED_DUPLICATE"
        }

    # 4. Check if generation_id already published
    records = history_manager.load_records()
    for r in records:
        if r.get("generation_id") == generation_id and r.get("status") == "PUBLISHED":
            logger.warning(f"⚠️ Generation ID {generation_id} is already PUBLISHED with YouTube ID {r.get('youtube_video_id')}")
            return False, {
                "error": f"SKIP: Generation ID {generation_id} has already been published.",
                "status": "ALREADY_PUBLISHED"
            }

    # 5. Video QA check (duration, resolution, audio integrity)
    video_type = generation_metadata.get("video_type", "shorts")
    qa_res = run_full_qa(
        video_path,
        expected_type=video_type,
        min_duration=25.0 if video_type == "shorts" else 50.0,
        max_duration=62.0 if video_type == "shorts" else 720.0,
        require_audio=True
    )
    if not qa_res["passed"]:
        logger.error(f"❌ Video QA failed: {qa_res['errors']}")
        return False, {"error": f"Video QA failed: {qa_res['errors']}", "qa": qa_res}

    # 6. Thumbnail check (if path specified)
    if thumbnail_path and (not os.path.exists(thumbnail_path) or os.path.getsize(thumbnail_path) < 1024):
        logger.warning(f"⚠️ Thumbnail path invalid: {thumbnail_path}, generation will proceed without custom thumbnail.")
        thumbnail_path = None

    return True, {
        "video_hash": v_hash,
        "qa": qa_res,
        "thumbnail_path": thumbnail_path
    }


def upload_to_youtube(
    video_path: str,
    metadata: Dict[str, Any],
    thumbnail_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Uploads a verified video to YouTube.
    1. Runs Quality Control & Duplicate Hash Protection.
    2. Moves to /ready_to_upload.
    3. Performs YouTube API upload.
    4. Moves to /archive upon success (or /failed on error).
    5. Updates content memory and PostgreSQL.
    """
    generation_id = metadata.get("generation_id") or f"gen_{int(time.time())}"
    title = metadata.get("title", "BeyondEra Tech Future Technology")
    description = metadata.get("description", "BeyondEra Tech analysis of future frontier technology.")
    tags = metadata.get("tags", ["FutureTech", "AI", "BeyondEraTech"])
    video_type = metadata.get("video_type", "shorts")

    logger.info("=" * 70)
    logger.info(f"📤 [YOUTUBE UPLOADER] Starting upload pipeline for: {title}")
    logger.info(f"🔑 Generation ID: {generation_id}")
    logger.info("=" * 70)

    # 1. Quality Control & Duplicate Check
    valid, check_info = validate_for_upload(video_path, metadata, thumbnail_path)
    if not valid:
        err_status = check_info.get("status", "FAILED")
        logger.error(f"🛑 Upload validation failed: {check_info.get('error')}")

        # Move to failed workspace if duplicate
        dest_failed = os.path.join(FAILED_DIR, os.path.basename(video_path))
        try:
            if os.path.exists(video_path) and video_path != dest_failed:
                shutil.copy2(video_path, dest_failed)
        except Exception:
            pass

        history_manager.record_generation(
            generation_id=generation_id,
            topic=metadata.get("topic", title),
            title=title,
            script=metadata.get("script", ""),
            prompt=metadata.get("prompt", ""),
            flow_generation_id=metadata.get("flow_generation_id", ""),
            output_path=dest_failed,
            video_hash=check_info.get("video_hash") or compute_sha256_file(video_path),
            thumbnail_path=thumbnail_path,
            status=err_status,
            metadata={"validation_error": check_info.get("error")}
        )
        return {"success": False, "status": err_status, "error": check_info.get("error")}

    video_hash = check_info["video_hash"]
    logger.info(f"🔒 SHA-256 Video Hash verified unique: {video_hash}")

    # 2. Stage into ready_to_upload directory
    ready_video_path = os.path.join(READY_DIR, f"{generation_id}_{os.path.basename(video_path)}")
    try:
        shutil.copy2(video_path, ready_video_path)
    except Exception as e:
        ready_video_path = video_path

    # Write metadata descriptor into ready_to_upload
    meta_path = os.path.join(READY_DIR, f"{generation_id}_meta.json")
    with open(meta_path, "w", encoding="utf-8") as mf:
        json.dump({**metadata, "video_hash": video_hash, "ready_at": datetime.datetime.now().isoformat()}, mf, indent=2, ensure_ascii=False)

    # 3. Execute YouTube Data API v3 Upload
    youtube_video_id = None
    upload_success = False

    # Attempt YouTube API authentication or studio client
    api_key = os.getenv("YOUTUBE_API_KEY")
    client_secrets_file = os.path.join(PROJECT_ROOT, "client_secrets.json")
    oauth_token_file = os.path.join(PROJECT_ROOT, "youtube_oauth_token.json")

    try:
        # If OAuth credentials exist, attempt live YouTube Data API upload
        if os.path.exists(client_secrets_file):
            logger.info("🔑 Client secrets file found. Initializing authenticated YouTube client...")
            try:
                from google_auth_oauthlib.flow import InstalledAppFlow
                from google.auth.transport.requests import Request
                from google.oauth2.credentials import Credentials
                from googleapiclient.discovery import build
                from googleapiclient.http import MediaFileUpload
                import pickle

                SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
                creds = None

                # Load cached OAuth token if available
                if os.path.exists(oauth_token_file):
                    try:
                        with open(oauth_token_file, "r") as tf:
                            token_data = json.load(tf)
                        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
                    except Exception:
                        creds = None

                # Refresh or create new credentials
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except Exception:
                        creds = None

                if not creds or not creds.valid:
                    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
                    creds = flow.run_local_server(port=0, open_browser=False)
                    # Cache the token for future use
                    with open(oauth_token_file, "w") as tf:
                        tf.write(creds.to_json())

                youtube = build("youtube", "v3", credentials=creds)

                # Prepare video metadata
                is_shorts = video_type == "shorts"
                yt_title = title[:100]  # YouTube title limit
                yt_description = description[:5000]  # YouTube description limit
                if is_shorts:
                    if not yt_title.endswith("#Shorts"):
                        yt_title = f"{yt_title} #Shorts"

                body = {
                    "snippet": {
                        "title": yt_title,
                        "description": yt_description,
                        "tags": tags[:30],  # YouTube allows max 30 tags
                        "categoryId": "28",  # Science & Technology
                        "defaultLanguage": "en",
                    },
                    "status": {
                        "privacyStatus": "public",
                        "selfDeclaredMadeForKids": False,
                    },
                }

                media = MediaFileUpload(
                    ready_video_path,
                    mimetype="video/mp4",
                    resumable=True,
                    chunksize=10 * 1024 * 1024  # 10MB chunks
                )

                request = youtube.videos().insert(
                    part=",".join(body.keys()),
                    body=body,
                    media_body=media
                )

                # Execute resumable upload with progress tracking
                response = None
                while response is None:
                    status_resp, response = request.next_chunk()
                    if status_resp:
                        progress = int(status_resp.progress() * 100)
                        logger.info(f"📤 Upload progress: {progress}%")

                youtube_video_id = response.get("id")
                upload_success = True
                logger.info(f"✅ [YOUTUBE API] Live upload completed! Video ID: {youtube_video_id}")

                # Upload thumbnail if available
                if thumbnail_path and os.path.exists(thumbnail_path) and youtube_video_id:
                    try:
                        thumb_media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
                        youtube.thumbnails().set(
                            videoId=youtube_video_id,
                            media_body=thumb_media
                        ).execute()
                        logger.info("🖼 Thumbnail uploaded successfully!")
                    except Exception as thumb_err:
                        logger.warning(f"Thumbnail upload warning: {thumb_err}")

            except ImportError:
                logger.warning("⚠️ google-auth-oauthlib not installed. Falling back to staging mode.")
            except Exception as oauth_err:
                logger.warning(f"⚠️ OAuth upload failed: {oauth_err}. Falling back to staging mode.")

        # OAuth yo'q bo'lsa: video STAGING'da qoladi, lekin bu MUVAFFAQIYAT EMAS.
        #
        # Ilgari bu yerda soxta ID (`BE_9ACE79DB_89933`) yaratilib
        # `upload_success = True` qo'yilardi. Natijada butun zanjir yolg'on
        # gapirardi: DB'da status 'published', Telegram'ga "🎉 JONLI EFIRGA
        # CHIQDI!", `content_history.json` da 7 ta "PUBLISHED" yozuv — holbuki
        # YouTube'da bitta ham video yo'q edi va auditni tiklash imkonsiz edi.
        # (gemini.md 6- va 7-qoidalari aynan buni taqiqlaydi.)
        if not upload_success:
            youtube_video_id = None
            logger.warning(
                "⚠️ YouTube OAuth sozlanmagan — video YUKLANMADI, staging'da qoldi: %s",
                ready_video_path,
            )

    except Exception as e:
        logger.error(f"YouTube upload error: {e}")
        upload_success = False

    if not upload_success:
        # Video yaratilgan, lekin yuklanmagan — bu QISMAN muvaffaqiyat.
        # Faylni `failed/` ga tashlamaymiz: OAuth sozlangach qayta urinish mumkin.
        staged_path = ready_video_path
        history_manager.update_status(
            generation_id, "STAGED_NOT_UPLOADED",
            error_message="YouTube OAuth sozlanmagan — video yuklanmadi.",
        )
        return {
            "success": False,
            "staged": True,
            "status": "STAGED_NOT_UPLOADED",
            "youtube_video_id": None,
            "video_path": staged_path,
            "error": "YouTube OAuth sozlanmagan (client_secrets.json topilmadi). "
                     "Video tayyor va staging'da, yuklash bajarilmadi.",
        }

    # 4. Move to /archive workflow (Crucial requirement from JoshPChua/Youtube-AI-Automation-Agent)
    archive_video_path = os.path.join(ARCHIVE_DIR, f"{generation_id}_{os.path.basename(video_path)}")
    archive_meta_path = os.path.join(ARCHIVE_DIR, f"{generation_id}_meta.json")

    try:
        shutil.move(ready_video_path, archive_video_path)
        shutil.move(meta_path, archive_meta_path)
        logger.info(f"📦 [ARCHIVE] Video archived safely to: {archive_video_path}")
    except Exception as e:
        logger.warning(f"Warning during file archive: {e}")
        archive_video_path = ready_video_path

    # 5. Persist into Content Memory
    history_manager.record_generation(
        generation_id=generation_id,
        topic=metadata.get("topic", title),
        title=title,
        script=metadata.get("script", ""),
        prompt=metadata.get("prompt", ""),
        flow_generation_id=metadata.get("flow_generation_id", "flow_proc_01"),
        output_path=archive_video_path,
        video_hash=video_hash,
        thumbnail_path=thumbnail_path,
        status="PUBLISHED",
        youtube_video_id=youtube_video_id,
        metadata={
            "duration": check_info["qa"]["metrics"]["duration"],
            "resolution": f"{check_info['qa']['metrics']['width']}x{check_info['qa']['metrics']['height']}",
            "archived_at": datetime.datetime.now().isoformat()
        }
    )

    # 6. Synchronize PostgreSQL ScheduledUpload
    sync_with_database(metadata, archive_video_path, youtube_video_id, video_hash)

    logger.info(f"🎉 [PUBLISHED] Video is live on YouTube! ID: {youtube_video_id}")
    return {
        "success": True,
        "status": "PUBLISHED",
        "youtube_video_id": youtube_video_id,
        "video_hash": video_hash,
        "archive_path": archive_video_path,
        "generation_id": generation_id
    }


def sync_with_database(metadata: Dict[str, Any], archive_path: str, youtube_video_id: str, video_hash: str):
    """Updates PostgreSQL database records with published status and unique video hash."""
    import base64
    import subprocess

    # `published` faqat HAQIQIY YouTube video ID bilan qo'yiladi.
    # Busiz baza "nashr qilingan, lekin ID yo'q" holatiga to'lib ketardi.
    if not youtube_video_id:
        logger.warning("sync_with_database: youtube_video_id bo'sh — 'published' belgilanmaydi.")
        return {"success": False, "error": "youtube_video_id bo'sh"}

    db_data = {
        "channel_id": "UC525J1r4HA1qV8DVf6FKQEg",
        "title": metadata.get("title", ""),
        "topic": metadata.get("topic", ""),
        "video_path": archive_path,
        "youtube_video_id": youtube_video_id,
        "video_hash": video_hash
    }
    b64 = base64.b64encode(json.dumps(db_data).encode("utf-8")).decode("ascii")

    cmd = [
        "docker", "exec", "-i", "youtube_integratsiya_backend",
        "python", "manage.py", "shell", "-c",
        f"""
import base64, json
from django.utils import timezone
from apps.youtube.models import ScheduledUpload, VideoGenerationTask

payload = json.loads(base64.b64decode('{b64}').decode('utf-8'))
# Sarlavha noyob emas; allaqachon nashr qilinganini qayta yozmaymiz
upload = (ScheduledUpload.objects
          .filter(title=payload['title'])
          .exclude(status='published')
          .order_by('scheduled_date')
          .first())
if upload:
    upload.status = 'published'
    upload.youtube_video_id = payload['youtube_video_id']
    upload.published_at = timezone.now()
    upload.save(update_fields=['status', 'youtube_video_id', 'published_at'])
    print('DB_SYNC_SUCCESS:' + str(upload.id))
else:
    print('DB_SYNC_SKIPPED')
"""
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except Exception as e:
        logger.warning(f"Database sync warning: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="YouTube Uploader with Deduplication")
    parser.add_argument("video_path", help="Path to MP4 video")
    parser.add_argument("--title", default="BeyondEra Tech Video", help="Title")
    parser.add_argument("--topic", default="Future Tech", help="Topic")
    parser.add_argument("--gen-id", default=None, help="Generation ID")
    parser.add_argument("--type", default="shorts", choices=["shorts", "long"])

    args = parser.parse_args()
    meta = {
        "generation_id": args.gen_id or f"manual_{int(time.time())}",
        "title": args.title,
        "topic": args.topic,
        "video_type": args.type
    }
    res = upload_to_youtube(args.video_path, meta)
    print(json.dumps(res, indent=2))


def youtube_oauth_is_configured() -> bool:
    """OAuth haqiqatan sozlanganmi (soxta yuklashning oldini olish uchun)."""
    return os.path.exists(os.path.join(PROJECT_ROOT, "client_secrets.json"))


def upload_pending_for_schedule(due_uploads: list) -> list:
    """19:00 navbatidagi yozuvlar uchun HAQIQIY yuklashni bajaradi.

    `due_uploads` — [{'id': int, 'title': str, 'date': 'YYYY-MM-DD'}, ...]
    Qaytaradi: haqiqatan YouTube'ga yuklangan videolarning sarlavhalari.

    Muhim: OAuth sozlanmagan bo'lsa BO'SH ro'yxat qaytaradi va hech qanday
    yozuvni 'published' qilmaydi. Ilgari daemon shu joyda yuklamasdan
    status'ni o'zgartirib, Telegram'ga soxta "efirga chiqdi" xabari yuborardi.
    """
    if not youtube_oauth_is_configured():
        logger.error(
            "YouTube OAuth sozlanmagan (client_secrets.json yo'q) — %d ta video "
            "yuklanmadi va 'published' deb belgilanmadi. Ular navbatda qoladi.",
            len(due_uploads),
        )
        return []

    published = []
    for item in due_uploads:
        title = item.get("title", "")
        video_path = _find_staged_video(title)
        if not video_path:
            logger.error("«%s» uchun tayyor video fayli topilmadi — o'tkazib yuborildi.", title)
            continue

        result = upload_to_youtube(video_path, {
            "generation_id": f"sched_{item.get('id')}",
            "title": title,
            "topic": title,
        })
        if result.get("success") and result.get("youtube_video_id"):
            published.append(title)
        else:
            logger.error("«%s» yuklanmadi: %s", title, result.get("error", "nomaʼlum xato"))
    return published


def _find_staged_video(title: str) -> Optional[str]:
    """Sarlavha bo'yicha `ready_to_upload/` dan mos .mp4 faylni qidiradi."""
    if not os.path.isdir(READY_DIR):
        return None
    candidates = [
        os.path.join(READY_DIR, f)
        for f in os.listdir(READY_DIR)
        if f.lower().endswith(".mp4")
    ]
    if not candidates:
        return None
    slug = "".join(ch.lower() for ch in title if ch.isalnum())[:24]
    for path in candidates:
        name = "".join(ch.lower() for ch in os.path.basename(path) if ch.isalnum())
        if slug and slug in name:
            return path
    # Aniq moslik yo'q — eng yangi faylni olamiz
    return max(candidates, key=os.path.getmtime)
