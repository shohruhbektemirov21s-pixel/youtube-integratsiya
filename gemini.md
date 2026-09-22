# Gemini AI — Loyiha Qoidalari va Standartlari

Ushbu hujjat loyihada ishlayotgan barcha AI assistentlar va muhandislar uchun majburiy ko'rsatmalar to'plamidir.

## Asosiy Qoidalar

1. **Senior engineering standards**: Write clean, resilient, production-quality, type-annotated code adhering to SOLID and industry best practices.
2. **Task-by-task execution**: Follow the strict task sequence (TASK 1 to TASK 16). Do not skip ahead or jump between stages.
3. **Do not skip failed tasks**: Every step must pass and be verified before moving to the next task.
4. **Do not modify unrelated code**: Only touch files directly required for the autonomous content factory pipeline. Preserve existing working features.
5. **Ask only when genuinely ambiguous**: If requirements are clear, execute automatically; only pause to ask if credentials or high-risk unknown security questions arise.
6. **Never fake successful tests**: Never use mock outputs or stubs to fake real pipeline success.
7. **Never mark a failed video as successful**: Black frames, frozen videos, empty audio, or missing scripts must trigger automated retries or explicit failure status.
8. **Always verify generated files**: Check video duration, resolution, audio track, black-frame ratio, and integrity via ffprobe/ffmpeg.
9. **Preserve existing architecture**: Maintain Django models, React dashboard, PostgreSQL schemas, Telegram bot, and Chrome profiles intact.
10. **Keep secrets secure**: Never hardcode API keys, passwords, cookies, or tokens in source code; use `.env` and `.gitignore`.
11. **Document important changes**: Keep clear logs, update state machines, and document critical pipeline mechanics.

---

## Texnologik Stack

- **Backend**: Python 3, Django, Django REST Framework (DRF)
- **Frontend**: TypeScript, React (Vite)
- **Database**: PostgreSQL 16
- **Browser Automation**: Playwright, Google Chrome Profiles
- **Video & Audio Processing**: FFmpeg, Edge-TTS
- **AI Models**: Google Gemini 3.8 Flash, Google Flow AI (VideoFX)
- **Notifications**: Telegram Bot API (Text, Video, Voice Notes)
- **Security**: Environment variables (.env), CORS, CSRF, Token/JWT authentication
- **Version Control**: Git

---

## Xavfsizlik va Konfiguratsiya Standartlari

- Maxfiy kalitlar (SECRET_KEY, DB parollari, API kalitlar) hech qachon manba kodida (source code) saqlanmaydi.
- Barcha maxfiy parametrlar `.env` faylida saqlanadi va `.gitignore` orqali git kuzatuvidan chiqariladi.
- Namuna sifatida har doim `.env.example` taqdim etiladi.

