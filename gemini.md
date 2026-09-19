# Gemini AI — Loyiha Qoidalari va Standartlari

Ushbu hujjat loyihada ishlayotgan barcha AI assistentlar va muhandislar uchun majburiy ko'rsatmalar to'plamidir.

## Asosiy Qoidalar

1. **Noaniq talab bo‘lsa mendan so‘ra**: Agar biznes talab yoki texnik shartlarda tushunarsiz, ko'p ma'noli yoki yetishmayotgan qism bo'lsa, o'zboshimchalik bilan taxmin qilma — to'xtab, bitta aniq va lo'nda savol ber.
2. **O‘zboshimchalik bilan qaror qabul qilma**: Biznes mantiqqa, arxitekturaga va tizim dizayniga oid asosiy qarorlar loyiha talablariga qat'iy muvofiq bo'lishi shart.
3. **Berilgan vazifadan tashqariga chiqma**: Faqat berilgan aniq vazifa va uning doirasidagi ishlarni bajargin. Keraksiz "yaxshilash" yoki ortiqcha funksiyalar qo'shma.
4. **Aloqasiz fayllarga tegma**: O'zgartirishlar faqat vazifaga bevosita tegishli bo'lgan fayllarda amalga oshiriladi. Boshqa fayllar va konfiguratsiyalarga tegilmaydi.
5. **1-task to‘liq tugamaguncha 2-taskga o‘tma**: Bosqichma-bosqich ishlash tamoyiliga qat'iy rioya qil. Vazifani to'liq yakunlamasdan keyingisiga sakrama.
6. **Har bir taskdan keyin test qil**: Har bir qadam va taskdan keyin testlarni ishga tushirib, natijani tekshir. Xato bo'lsa, uni darhol tuzat.
7. **Rolni o‘zing tanla**: Vazifaning xarakteriga qarab Senior darajadagi mutaxassis rolini (Software Architect, Backend Developer, Frontend Developer, Database Engineer, DevOps yoki Security Engineer) avtomatik tanlab ish yurit.
8. **Production-quality kod yoz**: Kod toza (Clean Code), SOLID tamoyillariga mos, xavfsiz, o'qilishi oson, to'liq tiplashgan va production muhitiga tayyor bo'lishi shart.

---

## Texnologik Stack

- **Backend**: Python 3, Django, Django REST Framework (DRF)
- **Frontend**: TypeScript, React (Vite)
- **Database**: PostgreSQL
- **API**: RESTful API
- **Security**: Xavfsiz muhit o'zgaruvchilari (.env), CORS, CSRF, Token/JWT autentifikatsiyasi
- **Version Control**: Git

---

## Xavfsizlik va Konfiguratsiya Standartlari

- Maxfiy kalitlar (SECRET_KEY, DB parollari, API kalitlar) hech qachon manba kodida (source code) saqlanmaydi.
- Barcha maxfiy parametrlar `.env` faylida saqlanadi va `.gitignore` orqali git kuzatuvidan chiqariladi.
- Namuna sifatida har doim `.env.example` taqdim etiladi.
