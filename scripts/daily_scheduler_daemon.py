#!/usr/bin/env python3
"""
BeyondEra Tech - 24/7 Autonomous Publishing & Supervisor Daemon.
Features:
1. Enforces EXACTLY 1 VIDEO PER DAY at 19:00:00.
2. Buffer Management: Maintains 3-day pre-scheduled buffer in PostgreSQL.
3. Stuck Job Recovery: Detects tasks stuck in 'generating' or 'processing' > 30 mins and recovers them.
4. Process Health & Auto-Restart: Self-monitoring supervisor loop.
5. 19:00 Automated Live Publishing & Telegram celebration announcement.
"""

import os
import sys
import time
import json
import logging
import datetime
import subprocess
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [DAEMON] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/tmp/beyondera_daemon.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("AutonomousDaemon")


from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
if not TELEGRAM_BOT_TOKEN:
    logger.warning("⚠️ TELEGRAM_BOT_TOKEN muhit o'zgaruvchisi o'rnatilmagan. Telegram xabarlari yuborilmaydi.")
DEFAULT_CHAT_ID = "5960858213"
BEYOND_ERA_CHANNEL_ID = "UC525J1r4HA1qV8DVf6FKQEg"


def get_schedule_queue() -> list:
    """Retrieves upcoming scheduled uploads from PostgreSQL."""
    cmd = [
        "docker", "exec", "-i", "youtube_integratsiya_backend",
        "python", "manage.py", "shell", "-c",
        f"""
import json
from apps.youtube.models import ScheduledUpload

uploads = ScheduledUpload.objects.filter(
    channel__channel_id='{BEYOND_ERA_CHANNEL_ID}'
).order_by('scheduled_date')

result = []
for u in uploads:
    result.append({{
        'id': u.id,
        'title': u.title,
        'date': str(u.scheduled_date),
        'time': str(u.scheduled_time),
        'status': u.status,
        'tags': u.tags
    }})
print('QUEUE_JSON:' + json.dumps(result))
"""
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
        for line in proc.stdout.splitlines():
            if line.startswith("QUEUE_JSON:"):
                return json.loads(line.replace("QUEUE_JSON:", "").strip())
    except Exception as e:
        logger.error(f"Navbatni tekshirishda xatolik: {e}")
    return []


def gather_daily_intelligence():
    """Generates the daily intelligence report if not already generated today."""
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    intel_cache_dir = os.path.join(PROJECT_ROOT, "assets", "intelligence_cache")
    report_path = os.path.join(intel_cache_dir, f"daily_report_{today_str}.json")
    
    if not os.path.exists(report_path):
        logger.info("🧠 Bugungi kunlik YouTube Intelligence hisoboti mavjud emas. Generatsiya qilinmoqda...")
        try:
            if PROJECT_ROOT not in sys.path:
                sys.path.insert(0, PROJECT_ROOT)
            from scripts.youtube_channel_intelligence import YouTubeChannelIntelligence
            intel = YouTubeChannelIntelligence()
            intel.generate_daily_intelligence_report()
            logger.info("✅ Kunlik Intelligence hisoboti tayyorlandi.")
        except Exception as e:
            logger.error(f"Intelligence hisobotini yaratishda xatolik: {e}")

def recover_stuck_tasks():
    """Recovers any tasks stuck in processing or generating for over 30 minutes."""
    cmd = [
        "docker", "exec", "-i", "youtube_integratsiya_backend",
        "python", "manage.py", "shell", "-c",
        """
from django.utils import timezone
from datetime import timedelta
from apps.youtube.models import ScheduledUpload, VideoGenerationTask

cutoff = timezone.now() - timedelta(minutes=30)
stuck_tasks = VideoGenerationTask.objects.filter(status='generating', created_at__lt=cutoff)
recovered = stuck_tasks.update(status='failed', error_message='Stuck task timeout recovered by daemon')

stuck_uploads = ScheduledUpload.objects.filter(status='processing', updated_at__lt=cutoff)
for u in stuck_uploads:
    u.status = 'scheduled'
    u.save(update_fields=['status'])
print(f'RECOVERED:{recovered}')
"""
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except Exception as e:
        logger.warning(f"Qotib qolgan vazifalarni tekshirishda ogohlantirish: {e}")


def mark_today_published_if_due():
    """Bugungi (va kechikkan) rejalashtirilgan videolarni YouTube'ga yuklaydi.

    DIQQAT — bu funksiya ilgari HECH NARSA YUKLAMASDAN shunchaki
    `status = 'published'` qo'yib, Telegram'ga "JONLI EFIRGA CHIQDI!" deb
    yozardi. Natijada bazada `youtube_video_id` bo'sh bo'lgan, sanasi
    kelajakda turgan 4 ta "nashr qilingan" yozuv paydo bo'lgan edi.

    Endi holat faqat haqiqiy yuklashdan keyin o'zgaradi.
    """
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    if now.hour >= 19:
        cmd = [
            "docker", "exec", "-i", "youtube_integratsiya_backend",
            "python", "manage.py", "shell", "-c",
            f"""
import json
from django.utils import timezone
from apps.youtube.models import ScheduledUpload

today = timezone.now().date()
# `scheduled_date=today` edi: daemon bir kun ishlamasa, o'sha kun ABADIY
# o'tkazib yuborilardi (bazada 2 kunlik yetim yozuv shundan qolgan).
due_uploads = ScheduledUpload.objects.filter(
    channel__channel_id='{BEYOND_ERA_CHANNEL_ID}',
    scheduled_date__lte=today,
    status='scheduled'
).order_by('scheduled_date')

due = [{'id': u.id, 'title': u.title, 'date': str(u.scheduled_date)} for u in due_uploads]
print('DUE_UPLOADS:' + json.dumps(due))
"""
        ]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            if proc.returncode != 0:
                logger.error("Navbatni o'qishda xatolik (rc=%s): %s",
                             proc.returncode, (proc.stderr or "")[-1000:])
                return

            for line in proc.stdout.splitlines():
                if line.startswith("DUE_UPLOADS:"):
                    due = json.loads(line.replace("DUE_UPLOADS:", "").strip())
                    if not due:
                        continue

                    if DIR not in sys.path:
                        sys.path.insert(0, DIR)
                    from youtube_uploader import upload_pending_for_schedule
                    titles = upload_pending_for_schedule(due)
                    for t in titles:
                        logger.info(f"🎉 Video YouTube'ga yuklandi va e'lon qilindi: {t}")
                        try:
                            msg = (
                                f"🎉 <b>YOUTUBE 19:00: BUGUNGI VIDEO JONLI EFIRGA CHIQDI!</b>\n\n"
                                f"🎬 <b>Sarlavha:</b> {t}\n"
                                f"📅 <b>Sana:</b> Bugun ({today_str}) soat 19:00:00\n"
                                f"✅ <b>Holati:</b> Published (Muvaffaqiyatli e'lon qilindi)\n"
                                f"🚀 <b>BeyondEra Tech:</b> Har kuni soat 19:00 da uzluksiz 1 tadan video."
                            )
                            requests.post(
                                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                                json={"chat_id": DEFAULT_CHAT_ID, "text": msg, "parse_mode": "HTML"},
                                timeout=10
                            )
                        except Exception:
                            pass
        except Exception as e:
            logger.error(f"Nashr qilishda xatolik: {e}")


def generate_next_scheduled_video():
    """Triggers the full auto video pipeline for the next empty day."""
    logger.info("🎬 Kunlik yangi video generatsiyasi boshlanmoqda (Avtomatik 19:00 rejasi)...")
    cmd = [
        sys.executable,
        os.path.join(DIR, "auto_video_pipeline.py"),
        "--type", "auto"
    ]
    # 180s to'liq pipeline uchun (Gemini + Flow AI brauzeri + FFmpeg render +
    # QA + thumbnail + Telegram yuklash) hech qachon yetmasdi: har safar
    # TimeoutExpired bilan SIGKILL bo'lib, yarim fayllar va `generating`
    # holatidagi zombi yozuvlar qolardi.
    timeout_s = int(os.environ.get("PIPELINE_TIMEOUT_SECONDS", "2700"))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
        if proc.returncode == 0:
            logger.info("Pipeline muvaffaqiyatli yakunlandi.")
        else:
            # Ilgari bu yerda returncode'dan qat'i nazar "muvaffaqiyatli" deb
            # yozilardi — yiqilgan pipeline loglarda yashirin qolardi.
            logger.error("Pipeline XATO bilan tugadi (rc=%s): %s",
                         proc.returncode, (proc.stderr or "")[-2000:])
    except subprocess.TimeoutExpired:
        logger.error("Pipeline %ss ichida tugamadi va to'xtatildi.", timeout_s)
    except Exception as e:
        logger.error(f"Pipeline ishga tushirishda xatolik: {e}")


def run_supervisor_loop():
    """24/7 Infinite supervision loop."""
    logger.info("=================================================================")
    logger.info("🚀 BEYONDERA TECH 24/7 AUTONOMOUS CONTENT SUPERVISOR DAEMON")
    logger.info("   Qat'iy qoida: Har kuni soat 19:00 da 1 ta video e'lon qilinadi.")
    logger.info("=================================================================")

    while True:
        try:
            # 1. Recover stuck jobs
            recover_stuck_tasks()

            # 1.5. Gather daily intelligence
            gather_daily_intelligence()

            # 2. Check current queue
            queue = get_schedule_queue()
            active_scheduled = [q for q in queue if q.get("status", "").lower() == "scheduled"]
            logger.info(f"📊 Navbatdagi rejalashtirilgan videolar: {len(active_scheduled)} ta")

            # 3. Check if today's 19:00 video is due to publish
            mark_today_published_if_due()

            # 4. Maintain healthy buffer (at least 3 upcoming daily videos)
            if len(active_scheduled) < 3:
                logger.info(f"⚠️ Reja zaxirasi kam ({len(active_scheduled)} ta). Keyingi kun uchun yangi video yaratilmoqda...")
                generate_next_scheduled_video()
            else:
                logger.info(f"✅ Reja to'liq ta'minlangan ({len(active_scheduled)} kunlik zaxira bor). Keyingi tekshiruv 10 daqiqadan so'ng.")

        except Exception as e:
            logger.error(f"Daemon siklida xatolik: {e}")

        time.sleep(600)


if __name__ == "__main__":
    run_supervisor_loop()
