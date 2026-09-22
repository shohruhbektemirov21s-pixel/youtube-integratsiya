# 🚀 YouTube Avtomatlashtirish & Content-Factory Tizimi

Ushbu loyiha **Google Gemini AI**, **Nous Research Hermes Agent**, **4 ta Flow AI profillari (1000 kreditdan)**, **YouTube Data API / Browser Studio** va **Telegram Bot** integratsiyasiga ega to'liq avtonom kontent-fabrika tizimidir.

Laptop server rejimida 24/7 ishlaydi, qopqog'i yopilganda ham uxlab qolmaydi, kompyuter yoqilishi bilan barcha servislar (Docker + Hermes Agent) avtomatik ishga tushadi.

---

## 📌 Asosiy Texnologik Stack

- **Backend**: Python 3.12, Django 5/6, Django REST Framework (DRF), Gunicorn, WhiteNoise
- **Frontend**: TypeScript 5, React 19, Vite, Tailwind/Modern CSS
- **AI Agent Miyasi**: Nous Research Hermes Agent (`hermes-agent`) + Google Gemini AI (`gemini-3.8-flash`)
- **Ma'lumotlar Bazasi**: PostgreSQL 16
- **Reverse Proxy**: Nginx Alpine
- **Konteynerizatsiya**: Docker & Docker Compose (`restart: unless-stopped`)
- **Brauzer Avtomatizatsiyasi**: Playwright, Google Chrome Persistent Sessions
- **Xabarnomalar**: Telegram Bot (`@youtubebildirishnoma_bot`)

---

## 🏗 Arxitektura va Tizim Ishlash Prinsipi

```text
┌─────────────────────────────────────────────────────────────┐
│                 Foydalanuvchi (Telegram)                    │
│                @youtubebildirishnoma_bot                    │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Savol-javob, Buyruqlar, Kunlik hisobot)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│           Hermes Agent (Systemd User Service)               │
│     (Gemini AI Miyasi + Cron Jadvali + Xotira Tizimi)       │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
       (Vazifalarni saqlash)          (Avto-yuklash va statistika)
               ▼                              ▼
┌──────────────────────────────┐ ┌─────────────────────────────┐
│    Django REST API Backend   │ │  Nginx (Port 80) & React    │
│  PostgreSQL (Flow AI, Video) │ │  TypeScript Veb-Boshqaruv   │
└──────────────┬───────────────┘ └─────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│              Playwright & Chrome Profillari                 │
│  • Flow AI 4 ta profil (har birida 1000 kredit)             │
│  • YouTube Studio (Har kuni soat 19:00 da bitta mavzuda)    │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚡️ Asosiy Imkoniyatlar

1. **Bitta Aniq Mavzu (Single Niche Strategy):**
   - Kanal qat'iy ravishda 1 ta mavzu bo'yicha yuritiladi (masalan: *Sun'iy Intellekt va Kelajak Texnologiyalari*).
   - Gemini AI mavzudan chetga chiqmagan holda sarlavha, tavsif, teglar va vizual promptlarni avtomatik yaratadi.

2. **Flow AI 4 ta Akkaunt Balansi (1000 kreditdan):**
   - 4 ta brauzer profili (`Profile 1`, `Profile 3`, `Profile 4`, `Profile 6`) ulangan.
   - Kreditlar avtomatik hisoblanadi va eng ko'p kreditga ega akkaunt navbatma-navbat tanlanadi.

3. **Har Kuni Soat 19:00 da Avto-Yuklash:**
   - Hermes Agent Cron scheduler har kuni soat 19:00 da videoni sarlavha, tavsif va teglari bilan YouTube kanalga rejalashtiradi va yuklaydi.

4. **Telegram Kunlik Hisoboti va Savol-Javob:**
   - Har kuni bajarilgan ishlar, yangi yuklangan video, kunlik prosmotrlar o'sishi (+X ko'rish, +Y%) va obunachilar statistikasi `@youtubebildirishnoma_bot`ga avtomatik yuboriladi.
   - Botga istalgan savol bersangiz, Gemini AI sizga shaxsiy yordamchi sifatida o'zbek tilida batafsil javob beradi.

5. **Laptop Server Rejimi & Auto-Boot:**
   - Laptop qopqog'i yopilganda va bo'sh turganda uyqu rejimiga ketmaydi (`lid-action = 0`, `inactivity = 0`).
   - Kompyuter o'chib yoqilganda (boot):
     - `docker.service` avtomatik ko'tariladi va barcha konteynerlar ishga tushadi.
     - `hermes-gateway.service` systemd orqali avtomatik Telegram bot va cronni ishga tushiradi.

---

## 🛠 O'rnatish va Ishga Tushirish Qo'llanmasi

### 1. Muhit O'zgaruvchilari (.env)

`backend/.env` faylini quyidagicha sozlang:

```env
# Django Settings
DJANGO_SECRET_KEY=your_secret_key_here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
DB_NAME=youtube_db
DB_USER=youtube_user
DB_PASSWORD=your_secure_db_password
DB_HOST=db
DB_PORT=5432

# API Kalitlar
GEMINI_API_KEY=<Google AI Studio'dan olingan kalit>
TELEGRAM_BOT_TOKEN=<@BotFather bergan token>
```

### 2. Docker orqali ishga tushirish

```bash
# Barcha konteynerlarni qurish va fonda ishga tushirish:
docker compose up -d --build

# Bazani migratsiya qilish:
docker exec youtube_integratsiya_backend python manage.py migrate

# 4 ta Flow AI akkaunti va Niche strategiyasini yuklash:
docker exec youtube_integratsiya_backend python manage.py shell -c "
from apps.youtube.models import FlowAIAccount, ChannelNiche, YouTubeChannel
accounts = [
    {'name': 'Flow AI Profil 1 (Ustaai)', 'profile_dir': 'Profile 1', 'credits_remaining': 1000},
    {'name': 'Flow AI Profil 2', 'profile_dir': 'Profile 3', 'credits_remaining': 1000},
    {'name': 'Flow AI Profil 3', 'profile_dir': 'Profile 4', 'credits_remaining': 1000},
    {'name': 'Flow AI Profil 4', 'profile_dir': 'Profile 6', 'credits_remaining': 1000},
]
for a in accounts:
    FlowAIAccount.objects.get_or_create(name=a['name'], defaults=a)
print('Flow AI akkauntlari tayyor!')
"
```

### 3. Hermes Agent va Telegram Botni boshqarish

```bash
# Gateway holatini ko'rish:
hermes gateway status

# Gatewayni qayta ishga tushirish:
hermes gateway restart

# Systemd loglarini jonli kuzatish:
journalctl --user -u hermes-gateway -f

# Cron vazifalarini ko'rish:
hermes cron list
```

---

## 📱 Telegram Bot Buyruqlari (@youtubebildirishnoma_bot)

- `/start` — Botni faollashtirish va shaxsiy ID ni biriktirish
- `Bugun qanday videolar yuklandi?` — 19:00 dagi yuklashlar va tayyorlangan videolar ro'yxatini beradi
- `Prosmotrlar qancha bo'ldi?` — Bugungi ko'rishlar, o'sish dinamikasi va tahlilini yuboradi
- `Kreditlar holati` — 4 ta Flow AI akkauntidagi qoldiq kreditlarni ko'rsatadi

---

## 🌐 Veb Boshqaruv Paneli (Frontend)

Brauzeringizda quyidagi manzilga kiring:
👉 **`http://localhost/`**

Veb interfeys orqali quyidagilarni ko'rishingiz mumkin:
- **⚡️ Avtomatlashtirish & Flow AI:** 4 ta Flow AI hisobining kreditlari (1000/1000 progress bar), 19:00 yuklash navbati, oxirgi generatsiya qilingan videolar.
- **Kanallar & Playlistlar:** YouTube kanal parametrlari va playlistlar ro'yxati.
- **Tizim Holati:** Docker, Nginx, PostgreSQL va API larning sog'lomlik holati (Health Check).

---

## 👨‍💻 Boshqa Dasturchilar Uchun Eslatma (Maintenance)

1. **Yangi Flow AI profil qo'shish:** `backend/apps/youtube/models.py` dagi `FlowAIAccount` modeliga yangi profil nomi va Chrome katalogini qo'shish kifoya.
2. **Yuklash vaqtini o'zgartirish:** `ScheduledUpload` modelidagi `scheduled_time` maydonini o'zgartirish yoki Hermes Cronda `/cron edit` qilish mumkin.
3. **Mavzuni yangilash:** `ChannelNiche` jadvalidagi `niche_name` va `prompt_guidelines` maydonlari tahrirlansa, Gemini AI avtomatik yangi mavzu bo'yicha video g'oyalarni ishlab chiqaradi.
