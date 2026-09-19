# youtube-integratsiya

YouTube integratsiya va boshqaruv tizimi.

## Texnologiyalar Stagi

- **Backend**: Python 3, Django, Django REST Framework (DRF)
- **Frontend**: TypeScript, React
- **Database**: PostgreSQL
- **Arxitektura**: REST API, Modulli monolit / Ajratilgan Frontend-Backend

## Loyiha Strukturasi

```text
├── backend/                  # Django & DRF loyihasi
│   ├── config/               # Asosiy loyiha sozlamalari
│   ├── apps/                 # Alohida ilovalar (modules)
│   ├── manage.py
│   ├── requirements.txt
│   └── .env
├── frontend/                 # TypeScript & React frontend
│   ├── src/
│   ├── package.json
│   ├── tsconfig.json
│   └── .env
├── gemini.md                 # Loyiha qoidalari va standartlari
├── .env.example              # Muhit o'zgaruvchilari namunasi
├── .gitignore                # Git e'tibor bermaydigan fayllar
└── README.md
```

## O'rnatish va Ishga Tushirish

### 1. Backend sozlash

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### 2. Frontend sozlash

```bash
cd frontend
npm install
npm run dev
```
