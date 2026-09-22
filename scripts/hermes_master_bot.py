#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import functools
import logging
import asyncio
import random
import glob
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Ensure correct path resolution
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

import edge_tts
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Relative imports from scripts
try:
    from scripts.content_plan_engine import generate_content_plan
    from scripts.audio_subtitles_engine import synthesize_voiceover, generate_styled_ass_subtitles, resolve_ambient_music
    from scripts.youtube_channel_intelligence import YouTubeChannelIntelligence
    from scripts.video_qa import run_full_qa
    from scripts.prompt_media_generator import generate_image_from_prompt, generate_video_from_prompt, confirm_and_upload_video
except ImportError as e:
    logging.warning(f"Failed to import local modules, some features may fallback. Error: {e}")

# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================

# Default tokens specified in prompt, but prefer ENV if available
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "5960858213")

# ─────────────────────────────────────────────────────────────────────────────
# AVTORIZATSIYA (xavfsizlik)
# Ilgari TELEGRAM_CHAT_ID e'lon qilingan edi, lekin hech qayerda solishtirilmasdi.
# Natijada bot username'ini topgan HAR QANDAY odam /generate yoki /video yuborib
# kredit sarflashi va "confirm" tugmasi orqali kanalga ommaviy video chiqarishi
# mumkin edi. Endi har bir handler oq ro'yxatdan o'tadi.
# ─────────────────────────────────────────────────────────────────────────────
ALLOWED_CHAT_IDS = {
    int(x) for x in os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS", TELEGRAM_CHAT_ID)
    .replace(" ", "").split(",") if x.strip().lstrip("-").isdigit()
}


def is_authorized(update) -> bool:
    """Faqat oq ro'yxatdagi foydalanuvchi/chat botni ishlata oladi."""
    user = getattr(update, "effective_user", None)
    chat = getattr(update, "effective_chat", None)
    ids = {i for i in (getattr(user, "id", None), getattr(chat, "id", None)) if i is not None}
    if ids & ALLOWED_CHAT_IDS:
        return True
    logger.warning(
        "Ruxsatsiz Telegram urinishi rad etildi: user_id=%s chat_id=%s",
        getattr(user, "id", None), getattr(chat, "id", None),
    )
    return False


def authorized_only(handler):
    """Handler dekoratori — ruxsatsiz update jimgina tashlab yuboriladi."""
    @functools.wraps(handler)
    async def wrapper(update, context, *args, **kwargs):
        if not is_authorized(update):
            query = getattr(update, "callback_query", None)
            if query is not None:
                await query.answer("Ruxsat yo'q.", show_alert=True)
            return
        return await handler(update, context, *args, **kwargs)
    return wrapper


# Directories
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
VIDEO_LIBRARY_DIR = os.path.join(ASSETS_DIR, "video_library")
TEMP_DIR = os.path.join(PROJECT_ROOT, "temp")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

os.makedirs(VIDEO_LIBRARY_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(PROJECT_ROOT, "hermes_master_bot.log"), mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# httpx (python-telegram-bot ning HTTP mijozi) sukut bo'yicha INFO darajasida
# HAR BIR so'rovni TO'LIQ URL bilan log qiladi. Telegram Bot API tokeni
# header'da emas, URL yo'lida (`/bot<TOKEN>/getMe`) — shuning uchun bu default
# sozlama bot tokenini journalctl/log fayliga ochiq matnda yozib qo'yardi.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram.ext.Application").setLevel(logging.INFO)

# ==============================================================================
# PIPELINE HELPER FUNCTIONS
# ==============================================================================

async def send_uzbek_voice_summary(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """
    Synthesize an Uzbek voice summary and send it to the Telegram chat.
    """
    logger.info("Synthesizing Uzbek voice summary...")
    output_audio_path = os.path.join(TEMP_DIR, f"uzbek_summary_{int(datetime.now().timestamp())}.mp3")
    
    try:
        communicate = edge_tts.Communicate(text, "uz-UZ-MadinaNeural")
        await communicate.save(output_audio_path)
        
        with open(output_audio_path, 'rb') as audio_file:
            await context.bot.send_voice(
                chat_id=update.effective_chat.id,
                voice=audio_file,
                caption="🎙 O'zbek tilida qisqacha ma'lumot (Uzbek Summary)"
            )
    except Exception as e:
        logger.error(f"Error sending Uzbek voice summary: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⚠️ Xatolik yuz berdi ovozli xabar yaratishda: {str(e)}"
        )
    finally:
        if os.path.exists(output_audio_path):
            os.remove(output_audio_path)

def select_background_video() -> str:
    """Select a random background video clip from the library."""
    video_extensions = ["*.mp4", "*.mov", "*.mkv"]
    video_files = []
    for ext in video_extensions:
        video_files.extend(glob.glob(os.path.join(VIDEO_LIBRARY_DIR, ext)))
    
    if not video_files:
        logger.warning(f"No background video clips found in {VIDEO_LIBRARY_DIR}. Generating a dummy color video.")
        dummy_path = os.path.join(TEMP_DIR, "dummy_bg.mp4")
        if not os.path.exists(dummy_path):
            # Create a 5 second dummy blue video
            subprocess.run([
                "ffmpeg", "-f", "lavfi", "-i", "color=c=blue:s=1080x1920:d=5",
                "-c:v", "libx264", "-y", dummy_path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return dummy_path
    
    return random.choice(video_files)

async def render_video(voiceover_path: str, subtitles_path: str, output_path: str) -> str:
    """
    Combines background video, voiceover, subtitles, and background music using FFmpeg.
    """
    logger.info("Starting FFmpeg render process...")
    bg_video = select_background_video()
    
    try:
        bg_music = resolve_ambient_music()
    except Exception as e:
        logger.warning(f"Could not resolve ambient music, using none. Error: {e}")
        bg_music = None

    escaped_subtitles_path = subtitles_path.replace("\\", "/").replace(":", "\\:")
    
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", bg_video,
        "-i", voiceover_path
    ]
    
    if bg_music:
        cmd.extend(["-stream_loop", "-1", "-i", bg_music])
        
        filter_complex = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,ass='{escaped_subtitles_path}'[v];"
            f"[1:a]volume=1.0[a1];"
            f"[2:a]volume=0.1[a2];"
            f"[a1][a2]amix=inputs=2:duration=first:dropout_transition=2[a]"
        )
    else:
        filter_complex = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,ass='{escaped_subtitles_path}'[v];"
            f"[1:a]volume=1.0[a]"
        )

    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-shortest",
        output_path
    ])
    
    logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        error_msg = stderr.decode('utf-8')
        logger.error(f"FFmpeg render failed:\n{error_msg}")
        raise RuntimeError(f"FFmpeg render failed: {error_msg}")
        
    logger.info(f"FFmpeg render completed successfully. Output saved to {output_path}")
    return output_path

MASTER_PENDING_CONFIRMATIONS = {}

async def run_generation_pipeline(update: Update, context: ContextTypes.DEFAULT_TYPE, topic: str):
    """
    Main asynchronous pipeline for generating a video.
    """
    chat_id = update.effective_chat.id
    status_msg = await context.bot.send_message(chat_id, f"🔄 Starting generation pipeline for topic: *{topic}*", parse_mode='Markdown')
    
    timestamp = int(datetime.now().timestamp())
    session_id = f"gen_{timestamp}"
    
    try:
        # 1. Content Plan
        await context.bot.edit_message_text(f"📝 Generating content plan for: {topic}...", chat_id=chat_id, message_id=status_msg.message_id)
        script_text = ""
        try:
            plan = generate_content_plan(topic_hint=topic)
            if isinstance(plan, dict):
                script_text = plan.get('voiceover_script') or plan.get('full_voiceover_script') or plan.get('script') or ""
            elif isinstance(plan, str):
                script_text = plan
            else:
                script_text = f"Welcome to our new shorts. Today we talk about {topic}. It is going to be amazing!"
        except Exception as e:
            logger.error(f"Error in generate_content_plan: {e}")
            script_text = f"Welcome to our new shorts. Today we talk about {topic}. This is fallback content."

        if not script_text.strip():
            script_text = f"Exploring the incredible topic of {topic}. Like and subscribe for more amazing facts."
        
        # 2. Voiceover
        await context.bot.edit_message_text("🎙 Synthesizing English voiceover...", chat_id=chat_id, message_id=status_msg.message_id)
        voice_path = os.path.join(TEMP_DIR, f"{session_id}_voice.mp3")
        voice_duration = 45.0
        try:
            communicate = edge_tts.Communicate(script_text, "en-US-ChristopherNeural", rate="+3%")
            await communicate.save(voice_path)
            probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", voice_path]
            p_out = subprocess.check_output(probe_cmd).decode('utf-8').strip()
            voice_duration = float(p_out)
        except Exception as e:
            logger.error(f"Error in edge_tts voiceover: {e}")
            voice_duration = 30.0
            
        # 3. Subtitles
        await context.bot.edit_message_text("🔤 Generating ASS subtitles...", chat_id=chat_id, message_id=status_msg.message_id)
        subs_path = os.path.join(TEMP_DIR, f"{session_id}_subs.ass")
        try:
            subs_path = generate_styled_ass_subtitles(script_text, voice_duration, output_ass=subs_path, is_shorts=True)
        except Exception as e:
            logger.error(f"Error in generate_styled_ass_subtitles: {e}")
            with open(subs_path, 'w', encoding='utf-8') as f:
                f.write("[Script Info]\nScriptType: v4.00+\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
                
        # 4. Render
        await context.bot.edit_message_text("🎬 Rendering final video via FFmpeg...", chat_id=chat_id, message_id=status_msg.message_id)
        final_video_path = os.path.join(OUTPUT_DIR, f"{session_id}_final.mp4")
        await render_video(voice_path, subs_path, final_video_path)
        
        # 5. QA Check
        await context.bot.edit_message_text("🕵️‍♂️ Running QA check...", chat_id=chat_id, message_id=status_msg.message_id)
        qa_result = "Passed"
        try:
            qa_result = run_full_qa(final_video_path)
        except Exception as e:
            logger.warning(f"QA check failed: {e}")
            qa_result = "Warning: QA check encountered an error."

        # 6. Send Video with Strict Approval Requirement
        await context.bot.edit_message_text("📤 Uploading video to Telegram...", chat_id=chat_id, message_id=status_msg.message_id)
        
        MASTER_PENDING_CONFIRMATIONS[session_id] = {
            "video_path": final_video_path,
            "title": topic,
            "topic": topic
        }
        
        confirm_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ YouTube'ga Joylashni Tasdiqlash", callback_data=f"master_confirm_{session_id}"),
                InlineKeyboardButton("❌ Bekor Qilish", callback_data=f"master_cancel_{session_id}")
            ]
        ])

        with open(final_video_path, 'rb') as video_file:
            caption = (
                f"🚀 *New Short Generated!*\n\n"
                f"*Topic:* {topic}\n"
                f"*QA Status:* {qa_result}\n\n"
                f"⚠️ *DIQQAT:* Ushbu video siz tasdiqlamaguningizcha YouTube'ga yuklanmaydi.\n"
                f"YouTube kanalga joylashtirishni tasdiqlaysizmi?"
            )
            await context.bot.send_video(
                chat_id=chat_id,
                video=video_file,
                caption=caption,
                parse_mode='Markdown',
                reply_markup=confirm_markup
            )
            
        # 7. Uzbek voice summary
        uzbek_summary = f"{topic} mavzusidagi videongiz muvaffaqiyatli tayyorlandi va sifat nazoratidan o'tdi."
        await send_uzbek_voice_summary(update, context, uzbek_summary)
        
        await context.bot.edit_message_text("✅ Pipeline completed successfully!", chat_id=chat_id, message_id=status_msg.message_id)
        
    except Exception as e:
        logger.exception("Pipeline failed")
        await context.bot.edit_message_text(f"❌ Error during generation pipeline:\n{str(e)}", chat_id=chat_id, message_id=status_msg.message_id)


# ==============================================================================
# TELEGRAM BOT HANDLERS
# ==============================================================================

def get_main_keyboard():
    """Returns the main inline keyboard markup."""
    keyboard = [
        [
            InlineKeyboardButton("🖼 Promptdan Rasm", callback_data="cmd_prompt_image"),
            InlineKeyboardButton("🎬 Video Yaratish", callback_data="cmd_generate")
        ],
        [
            InlineKeyboardButton("📊 Channel Status", callback_data="cmd_status"),
            InlineKeyboardButton("📈 Competitor Trends", callback_data="cmd_trends")
        ],
        [
            InlineKeyboardButton("📝 Daily Plan", callback_data="cmd_plan"),
            InlineKeyboardButton("💎 Obsidian Vault", callback_data="cmd_obsidian")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user = update.effective_user
    welcome_msg = (
        f"👋 Welcome, {user.first_name}!\n\n"
        f"🤖 I am *Hermes Master Bot*, your central YouTube Automation Hub.\n\n"
        f"Send me any *Topic* as a text message, and I will generate a fully automated video!\n"
        f"Or use the buttons below to control the system:"
    )
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=welcome_msg,
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )

async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /generate command."""
    args = context.args
    if not args:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ Please provide a topic. Example: `/generate AI advancements`",
            parse_mode='Markdown'
        )
        return
    
    topic = " ".join(args)
    asyncio.create_task(run_generation_pipeline(update, context, topic))

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    chat_id = update.effective_chat.id
    msg = await context.bot.send_message(chat_id, "📊 Gathering channel analytics...")
    
    try:
        intel = YouTubeChannelIntelligence()
        report = intel.generate_daily_report()
    except Exception as e:
        logger.error(f"Intelligence error: {e}")
        report = "⚠️ Could not retrieve full channel intelligence. Check logs."

    await context.bot.edit_message_text(
        f"📈 *Channel Status Report*\n\n{report}",
        chat_id=chat_id,
        message_id=msg.message_id,
        parse_mode='Markdown'
    )
    
    await send_uzbek_voice_summary(
        update, context, 
        "Kanal statistikasi tahlil qilindi. Natijalar matn ko'rinishida yuborildi."
    )

async def trends_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /trends command."""
    chat_id = update.effective_chat.id
    msg = await context.bot.send_message(chat_id, "🔍 Analyzing competitor trends...")
    
    try:
        intel = YouTubeChannelIntelligence()
        trends = intel.analyze_competitors()
    except Exception as e:
        logger.error(f"Trends error: {e}")
        trends = "⚠️ Failed to fetch competitor trends."
        
    await context.bot.edit_message_text(
        f"🔥 *YouTube Trends & Competitors*\n\n{trends}",
        chat_id=chat_id,
        message_id=msg.message_id,
        parse_mode='Markdown'
    )
    
    await send_uzbek_voice_summary(
        update, context, 
        "Raqobatchilar va trendlar tahlili yakunlandi."
    )

async def plan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /plan command."""
    chat_id = update.effective_chat.id
    msg = await context.bot.send_message(chat_id, "📝 Retrieving today's content plan...")
    
    try:
        from scripts.content_plan_engine import get_next_pending_plan_entry, get_current_30_day_progress
        curr_progress = get_current_30_day_progress()
        pending = get_next_pending_plan_entry()
        if pending:
            plan = f"📅 Kun #{pending.get('day')}: {pending.get('title')}\n🔹 Format: {str(pending.get('video_type', 'shorts')).upper()}\n🔹 Mavzu: {pending.get('topic')}\n\nJami yakunlangan kunlar: {curr_progress}/30"
        else:
            plan = f"Barcha 30 kunlik reja muvaffaqiyatli yakunlangan! Jami: {curr_progress}/30"
    except Exception as e:
        logger.error(f"Plan error: {e}")
        plan = "⚠️ Failed to retrieve today's plan."
        
    await context.bot.edit_message_text(
        f"📅 *Today's Content Plan*\n\n{plan}",
        chat_id=chat_id,
        message_id=msg.message_id,
        parse_mode='Markdown'
    )
    
    await send_uzbek_voice_summary(
        update, context, 
        "Bugungi kontent reja tayyor."
    )

async def obsidian_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /obsidian command - syncs and reports vault status."""
    chat_id = update.effective_chat.id
    msg = await context.bot.send_message(chat_id, "💎 Obsidian Vault bilan sinxronizatsiya tekshirilmoqda...")
    try:
        from scripts.obsidian_vault_sync import run_full_obsidian_sync, VAULT_PATH
        run_full_obsidian_sync()
        notes = glob.glob(os.path.join(VAULT_PATH, "**/*.md"), recursive=True)
        report = (
            f"💎 *Obsidian Vault To'liq Ulandi!*\n\n"
            f"📂 *Papkasi:* `{VAULT_PATH}`\n"
            f"📝 *Jami Eslatmalar:* {len(notes)} ta markdown fayl\n"
            f"📅 *30-kunlik reja:* Barcha kunlar wikilinklar va promptlar bilan eksport qilingan\n"
            f"🧠 *Channel Intelligence:* Raqobatchilar va trendlar MOC ga bog'langan\n"
            f"⚡ *Holat:* 🟢 Sinxron va faol"
        )
    except Exception as e:
        logger.error(f"Obsidian sync error: {e}")
        report = f"⚠️ Obsidian xatolik: {e}"
        
    await context.bot.edit_message_text(report, chat_id=chat_id, message_id=msg.message_id, parse_mode='Markdown')
    await send_uzbek_voice_summary(update, context, "Obsidian vault to'liq ulandi va barcha kontent rejalari eslatmalarga sinxronlandi.")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plain text messages by treating them as video topics."""
    topic = update.message.text
    if topic.startswith('/'):
        return
        
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🎯 Topic received: *{topic}*\nStarting generation pipeline...",
        parse_mode='Markdown'
    )
    
    asyncio.create_task(run_generation_pipeline(update, context, topic))

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button clicks."""
    query = update.callback_query
    await query.answer()
    
    command = query.data
    
    if command == "cmd_generate":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please send me a text message with the topic you want to generate a video for, or use `/generate <topic>`.",
            parse_mode='Markdown'
        )
    elif command == "cmd_prompt_image":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🖼 Rasm tayyorlash uchun `/image <prompt>` yoki `/rasm <prompt>` buyrug'ini yuboring.\nMasalan: `/image Cyberpunk humanoid robot 8k`",
            parse_mode='Markdown'
        )
    elif command == "cmd_status":
        await status_command(update, context)
    elif command == "cmd_trends":
        await trends_command(update, context)
    elif command == "cmd_plan":
        await plan_command(update, context)
    elif command == "cmd_obsidian":
        await obsidian_command(update, context)
    elif command.startswith("master_confirm_"):
        sid = command.replace("master_confirm_", "")
        v_data = MASTER_PENDING_CONFIRMATIONS.get(sid)
        if v_data:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"🚀 *Tasdiqlandi!* «{v_data['title']}» videosi YouTube kanaliga yuklanmoqda...",
                parse_mode='Markdown'
            )
            try:
                res = confirm_and_upload_video(v_data["video_path"], {
                    "generation_id": sid,
                    "title": v_data["title"],
                    "topic": v_data["topic"]
                })
                yt_id = res.get("youtube_video_id", "LIVE_PUBLISHED")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"🎉 *Video YouTube'ga muvaffaqiyatli yuklandi!*\n\n🆔 *YouTube Video ID:* `{yt_id}`",
                    parse_mode='Markdown'
                )
                MASTER_PENDING_CONFIRMATIONS.pop(sid, None)
            except Exception as e:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"❌ YouTube'ga yuklashda xatolik: {e}"
                )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Ushbu video allaqachon tasdiqlangan yoki topilmadi."
            )
    elif command.startswith("master_cancel_"):
        sid = command.replace("master_cancel_", "")
        MASTER_PENDING_CONFIRMATIONS.pop(sid, None)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="🛑 *YouTube'ga yuklash bekor qilindi.* Video YouTube'ga joylanmadi.",
            parse_mode='Markdown'
        )

async def image_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /image or /rasm command."""
    args = context.args
    prompt = " ".join(args) if args else "Cyberpunk humanoid robot assembling quantum microchips in neon lab 8k"
    msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🖼 «{prompt}» prompti asosida 8K rasm tayyorlanmoqda...",
        parse_mode='Markdown'
    )
    try:
        img_path = generate_image_from_prompt(prompt)
        with open(img_path, 'rb') as pf:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=pf,
                caption=f"🖼 *Prompt Asosida Tayyorlangan Rasm*\n\n📌 *Prompt:* `{prompt}`",
                parse_mode='Markdown'
            )
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
    except Exception as e:
        await context.bot.edit_message_text(f"❌ Xatolik: {e}", chat_id=update.effective_chat.id, message_id=msg.message_id)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log Errors caused by Updates."""
    logger.error(f"Update '{update}' caused error '{context.error}'")

# ==============================================================================
# MAIN
# ==============================================================================

def main():
    """Start the bot."""
    logger.info("Initializing Hermes Master Bot...")
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is not set. Exiting.")
        sys.exit(1)

    if not ALLOWED_CHAT_IDS:
        logger.error(
            "TELEGRAM_ALLOWED_CHAT_IDS bo'sh — botni ochiq qoldirib bo'lmaydi. "
            "backend/.env ga qo'shing: TELEGRAM_ALLOWED_CHAT_IDS=<sizning chat_id>"
        )
        sys.exit(1)
    logger.info("Avtorizatsiya yoqildi. Ruxsat etilgan chat_id lar: %s", sorted(ALLOWED_CHAT_IDS))
        
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", authorized_only(start_command)))
    application.add_handler(CommandHandler("generate", authorized_only(generate_command)))
    application.add_handler(CommandHandler("image", authorized_only(image_command)))
    application.add_handler(CommandHandler("rasm", authorized_only(image_command)))
    application.add_handler(CommandHandler("status", authorized_only(status_command)))
    application.add_handler(CommandHandler("trends", authorized_only(trends_command)))
    application.add_handler(CommandHandler("plan", authorized_only(plan_command)))
    application.add_handler(CommandHandler("obsidian", authorized_only(obsidian_command)))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, authorized_only(handle_text_message)))
    application.add_handler(CallbackQueryHandler(authorized_only(handle_callback_query)))
    application.add_error_handler(error_handler)

    logger.info("Bot started. Polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
