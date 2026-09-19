#!/usr/bin/env bash
set -e

echo "[+] YouTube Integratsiya Backend ishga tushmoqda..."

# Database availability check (if DB_HOST is set)
if [ -n "$DB_HOST" ]; then
  echo "[+] Ma'lumotlar bazasi ($DB_HOST:$DB_PORT) kutilmoqda..."
  until python -c "
import sys, psycopg, os
try:
    psycopg.connect(
        dbname=os.getenv('DB_NAME', 'youtube_db'),
        user=os.getenv('DB_USER', 'youtube_user'),
        password=os.getenv('DB_PASSWORD', 'youtube_secure_pass_2026'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        connect_timeout=3
    )
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    echo "[!] Baza ulanishini kutmoqda... (2 soniya)"
    sleep 2
  done
  echo "[+] Ma'lumotlar bazasi tayyor!"
fi

# Run database migrations
echo "[+] Migratsiyalar tekshirilmoqda va qo'llanilmoqda..."
python manage.py migrate --noinput

# Collect static files
echo "[+] Statik fayllar to'planmoqda..."
python manage.py collectstatic --noinput

# Execute main command (e.g. gunicorn)
echo "[+] Server ishga tushirilmoqda: $@"
exec "$@"
