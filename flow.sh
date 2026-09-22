#!/usr/bin/env bash
# Quick CLI for BeyondEra Tech & Flow AI 1000+ credit automation

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ━━━ Load .env configuration ━━━
if [ -f "$DIR/.env" ]; then
    set -a
    source "$DIR/.env"
    set +a
fi

PYTHON_BIN="${PYTHON_BIN:-/home/kali/.hermes/hermes-agent/venv/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then
    PYTHON_BIN="$(command -v python3 2>/dev/null || echo python)"
fi
SCRIPT_FLOW="$DIR/scripts/flow_controller.py"
SCRIPT_PIPELINE="$DIR/scripts/auto_video_pipeline.py"
SCRIPT_VOICE="$DIR/scripts/send_voice_msg.py"
SCRIPT_DAEMON="$DIR/scripts/daily_scheduler_daemon.py"

case "$1" in
    1|2|3|4)
        $PYTHON_BIN "$SCRIPT_FLOW" open --profile "$1"
        ;;
    all)
        $PYTHON_BIN "$SCRIPT_FLOW" all
        ;;
    open)
        $PYTHON_BIN "$SCRIPT_FLOW" open "${2:-4}"
        ;;
    status|list|"")
        $PYTHON_BIN "$SCRIPT_FLOW" status
        echo ""
        $PYTHON_BIN "$SCRIPT_PIPELINE" --status
        ;;
    queue|calendar)
        docker exec -i youtube_integratsiya_backend python manage.py shell -c "
from apps.youtube.models import ScheduledUpload
uploads = ScheduledUpload.objects.filter(channel__channel_id='UC525J1r4HA1qV8DVf6FKQEg').order_by('scheduled_date')
print('=' * 75)
print('📅 BEYONDERA TECH: KUNIGA 1 TADAN VIDEO CHIQARISH JADVALI (19:00):')
print('=' * 75)
for i, u in enumerate(uploads, 1):
    kind = '📽 DOKUMENTAL' if any(t in str(u.tags) for t in ['Documentary', 'LongForm']) else '📱 SHORTS     '
    status_icon = '✅ Nashr qilingan' if u.status == 'published' else '⏰ Rejalashtirilgan'
    print(f'  [{i}] {u.scheduled_date} | 19:00:00 | {kind} | {status_icon} | \"{u.title}\"')
print('=' * 75)
"
        ;;
    daemon)
        shift
        case "$1" in
            start)
                nohup $PYTHON_BIN "$SCRIPT_DAEMON" > /tmp/beyondera_daemon.log 2>&1 &
                echo "✅ Kuniga 1 tadan video chiqaruvchi Daemon fonda ishga tushdi (PID: $!)"
                ;;
            stop)
                pkill -f "daily_scheduler_daemon.py" && echo "🛑 Daemon to'xtatildi." || echo "⚠️ Daemon ishlamayapti."
                ;;
            status|"")
                if pgrep -f "daily_scheduler_daemon.py" > /dev/null; then
                    echo "🟢 Daily Scheduler Daemon faol ishlamoqda (PID: $(pgrep -f 'daily_scheduler_daemon.py'))"
                    tail -n 10 /tmp/beyondera_daemon.log 2>/dev/null
                else
                    echo "⚪️ Daily Scheduler Daemon to'xtatilgan. Ishga tushirish: ./flow.sh daemon start"
                fi
                ;;
        esac
        ;;
    day)
        shift
        $PYTHON_BIN "$SCRIPT_PIPELINE" --profile 4 --day "$1"
        ;;
    roadmap)
        shift
        $PYTHON_BIN "$SCRIPT_PIPELINE" --profile 4 "$@"
        ;;
    shorts|short)
        shift
        $PYTHON_BIN "$SCRIPT_PIPELINE" --profile 4 --type shorts "$@"
        ;;
    long|doc)
        shift
        $PYTHON_BIN "$SCRIPT_PIPELINE" --profile 4 --type long "$@"
        ;;
    cadence|auto)
        shift
        $PYTHON_BIN "$SCRIPT_PIPELINE" --profile 4 --type auto "$@"
        ;;
    generate|video)
        shift
        $PYTHON_BIN "$SCRIPT_PIPELINE" --profile 4 "$@"
        ;;
    image|rasm)
        shift
        $PYTHON_BIN "$DIR/scripts/prompt_media_generator.py" image "$*"
        ;;
    prompt-video|pvideo)
        shift
        $PYTHON_BIN "$DIR/scripts/prompt_media_generator.py" video "$*"
        ;;
    voice)
        shift
        $PYTHON_BIN "$SCRIPT_VOICE" "$*"
        ;;
    research)
        shift
        $PYTHON_BIN "$DIR/scripts/browser_research_agent.py" "$@"
        ;;
    orchestrate|agent)
        shift
        $PYTHON_BIN "$DIR/scripts/ai_agent_orchestrator.py" "$@"
        ;;
    analytics)
        shift
        $PYTHON_BIN "$DIR/scripts/analytics_feedback_agent.py" "$@"
        ;;
    test)
        shift
        $PYTHON_BIN "$DIR/scripts/test_deduplication_pipeline.py" "$@"
        ;;
    notify)
        $PYTHON_BIN "$SCRIPT_FLOW" notify
        ;;
    bot)
        echo "🤖 Hermes Master Telegram Bot ishga tushmoqda..."
        $PYTHON_BIN "$DIR/scripts/hermes_master_bot.py"
        ;;
    intel|intelligence)
        echo "🧠 Kunlik YouTube Intelligence hisoboti yaratilmoqda..."
        $PYTHON_BIN "$DIR/scripts/channel_analyzer.py"
        ;;

    *)
        echo "=========================================================================="
        echo "🎥 BEYONDERA TECH & GOOGLE FLOW AVTOMATLASHTIRISH TIZIMI"
        echo "=========================================================================="
        echo "Foydalanish:"
        echo "  ./flow.sh queue          -> Kuniga 1 tadan chiqariladigan videolar kalendarini ko'rsatadi"
        echo "  ./flow.sh daemon start   -> 24/7 avtonom nazorat daemonini ishga tushiradi (har kuni 19:00 da 1 ta video)"
        echo "  ./flow.sh shorts         -> 30-60s yuqori sifatli YouTube Short yaratadi (1080x1920, 60fps) va botga tashlaydi"
        echo "  ./flow.sh long           -> 10-kunlik maxsus to'liq Dokumental video yaratadi (1920x1080, 10 daqiqa)"
        echo "  ./flow.sh cadence        -> 10-kunlik qoidani avtomatik tekshiradi va keyingi kun 19:00 ga joylaydi"
        echo "  ./flow.sh status         -> 4 ta profil krediti va 10-kunlik video jadvali holatini ko'rsatadi"
        echo "  ./flow.sh 4              -> BeyondEra Tech (Profile 17) brauzerini ochadi"
        echo "  ./flow.sh all            -> Barcha 4 ta profil brauzerini bir vaqtda ochadi"
        echo "  ./flow.sh voice \"Matn\"   -> Telegramga o'zbek tilida professional ovozli xabar yuboradi"
        echo "=========================================================================="
        ;;
esac
