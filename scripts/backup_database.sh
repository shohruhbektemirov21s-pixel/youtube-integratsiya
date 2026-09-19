#!/usr/bin/env bash
# ==============================================================================
# Database Backup Script for YouTube Integratsiya (PostgreSQL)
# Runs pg_dump with gzip, rotation, and integrity verification.
# ==============================================================================
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/var/backups/youtube_integratsiya}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
DATE_TAG="$(date +'%Y-%m-%d_%H%M%S')"
BACKUP_FILE="${BACKUP_DIR}/youtube_db_${DATE_TAG}.sql.gz"

DB_NAME="${DB_NAME:-youtube_db}"
DB_USER="${DB_USER:-youtube_user}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

mkdir -p "${BACKUP_DIR}"

echo "[+] [$(date)] Baza zaxiralash boshlandi: ${DB_NAME} -> ${BACKUP_FILE}"

# Export backup using pg_dump compressed with gzip
PGPASSWORD="${DB_PASSWORD:-youtube_secure_pass_2026}" pg_dump \
  -h "${DB_HOST}" \
  -p "${DB_PORT}" \
  -U "${DB_USER}" \
  -F p \
  "${DB_NAME}" | gzip -9 > "${BACKUP_FILE}"

# Verify backup was created and not empty
if [ -s "${BACKUP_FILE}" ]; then
  FILE_SIZE="$(du -h "${BACKUP_FILE}" | cut -f1)"
  echo "[+] [$(date)] Zaxira muvaffaqiyatli saqlandi! Hajmi: ${FILE_SIZE}"
else
  echo "[!] [$(date)] XATOLIK: Zaxira fayli bo'sh yoki yaratilmadi!" >&2
  exit 1
fi

# Clean up older backups exceeding retention days
echo "[+] [$(date)] ${RETENTION_DAYS} kundan eski zaxiralar tozalanmoqda..."
find "${BACKUP_DIR}" -type f -name "youtube_db_*.sql.gz" -mtime +"${RETENTION_DAYS}" -delete

echo "[+] [$(date)] Zaxiralash jarayoni yakunlandi."
