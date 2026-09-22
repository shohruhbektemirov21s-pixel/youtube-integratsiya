#!/usr/bin/env python3
"""
Flow Engine - YouTubePublisher.
Syncs video metadata to PostgreSQL Django models (VideoGenerationTask, ScheduledUpload)
and delegates publishing to the YouTube Uploader module.
"""

import os
import sys
import json
import time
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)


class YouTubePublisher:
    """Manages database record synchronization and YouTube publication."""

    def __init__(self):
        pass

    def record_to_database(
        self,
        topic: str,
        prompt: str,
        video_path: str,
        credits_used: int = 15,
        status: str = "completed"
    ) -> Optional[int]:
        """
        Inserts record into PostgreSQL via Django docker container.
        Returns created Task ID.
        Uses base64 encoding to safely pass data without SQL injection risk.
        """
        import base64
        payload = json.dumps({
            "topic": topic,
            "prompt": prompt[:250],
            "video_path": video_path,
            "credits_used": credits_used,
            "status": status
        }, ensure_ascii=False)
        b64_payload = base64.b64encode(payload.encode("utf-8")).decode("ascii")

        py_cmd = f"""
import base64, json
from django.apps import apps
from django.utils import timezone

data = json.loads(base64.b64decode('{b64_payload}').decode('utf-8'))
FlowAIAccount = apps.get_model('youtube', 'FlowAIAccount')
VideoGenerationTask = apps.get_model('youtube', 'VideoGenerationTask')

acc = FlowAIAccount.objects.filter(profile_dir='Profile 17').first() or FlowAIAccount.objects.first()

task = VideoGenerationTask.objects.create(
    account=acc,
    topic=data['topic'],
    prompt=data['prompt'],
    status=data['status'],
    video_file_path=data['video_path'],
    credits_used=data['credits_used'],
    completed_at=timezone.now()
)
print('TASK_ID:' + str(task.id))
"""
        cmd = [
            "docker", "exec", "-i", "youtube_integratsiya_backend",
            "python", "manage.py", "shell", "-c", py_cmd
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
            for line in res.stdout.splitlines():
                if line.startswith("TASK_ID:"):
                    task_id = int(line.split(":")[1].strip())
                    print(f"🗄 [DATABASE] Video metadata bazaga yozildi (Task ID: {task_id})")
                    return task_id
        except Exception as e:
            print(f"⚠️ Ma'lumotlar bazasiga yozishda ogohlantirish: {e}")
        return None

    def publish_video(self, video_path: str, meta_package: Dict[str, Any], thumbnail_path: Optional[str] = None) -> Dict[str, Any]:
        """Delegates video publication to the official YouTube uploader."""
        from scripts.youtube_uploader import upload_to_youtube
        print(f"🚀 [PUBLISHER] YouTube yuklash boshlanmoqda: \"{meta_package.get('title')}\"")
        return upload_to_youtube(video_path, meta_package, thumbnail_path=thumbnail_path)
