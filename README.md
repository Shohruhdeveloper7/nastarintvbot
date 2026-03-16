# 🎬 KinoBot — O'rnatish yo'riqnomasi

## Tizim tuzilmasi

```
kinobot/
├── bot.py                  ← Asosiy fayl
├── requirements.txt        ← Kutubxonalar
├── .env.example            ← Sozlamalar namunasi
├── database/
│   ├── db.py               ← Ulanish va jadvallar
│   └── queries.py          ← Barcha so'rovlar
├── handlers/
│   ├── common.py           ← /start, obuna tekshirish
│   ├── user.py             ← Foydalanuvchi handlerlari
│   └── admin.py            ← Admin handlerlari
├── middlewares/
│   ├── anti_spam.py        ← Spam himoyasi
│   └── subscription.py    ← Majburiy obuna
└── keyboards/
    └── keyboards.py        ← Barcha tugmalar
```

---

## Kod tizimi qanday ishlaydi?

```
Admin kino qo'shadi → Bot avtomatik kod beradi (1001, 1002, 1003...)
Foydalanuvchi: 1001 → Bot: 🎬 Kino yuboradi
```

---

## O'rnatish

### 1. Bot token olish
- @BotFather ga yozing
- /newbot → nom bering → token oling

### 2. Telegram ID olish
- @userinfobot ga yozing → ID oling

### 3. PostgreSQL o'rnatish
Railway.app da bepul PostgreSQL:
- railway.app ga kiring
- New Project → PostgreSQL
- DATABASE_URL ni nusxalang

### 4. Fayllarni yuklash

```bash
git clone yoki fayllarni serverga yuklang
cd kinobot
pip install -r requirements.txt
```

### 5. .env fayl yaratish

```bash
cp .env.example .env
```

`.env` faylini oching va to'ldiring:
```
BOT_TOKEN=7123456789:AAF...
DATABASE_URL=postgresql://...
SUPER_ADMIN_ID=123456789
```

### 6. Botni ishga tushirish

```bash
python bot.py
```

---

## Admin buyruqlari

| Buyruq | Vazifasi |
|--------|---------|
| `➕ Kino qo'shish` | Yangi kino qo'shish (kod avtomatik) |
| `🗑 Kino o'chirish` | Kod bo'yicha o'chirish |
| `📢 Kanal qo'shish` | Majburiy obuna kanali qo'shish |
| `📨 Reklama yuborish` | Barchaga xabar yuborish |
| `📊 Statistika` | Bot statistikasi |
| `/addadmin ID` | Admin qo'shish |
| `/removeadmin ID` | Adminni olib tashlash |
| `/block ID` | Foydalanuvchini bloklash |
| `/unblock ID` | Blokdan chiqarish |

---

## Foydalanuvchi imkoniyatlari

| Funksiya | Tavsif |
|----------|--------|
| `1001` yuborish | Kod bo'yicha kino olish |
| `Avengers` yuborish | Nom bo'yicha qidirish |
| ❤️ tugma | Sevimlilarga qo'shish |
| 🎬 Barcha kinolar | Kodlar ro'yxati |
| 📊 Top kinolar | Eng ko'p ko'rilganlar |

---

## Railway.app ga deploy qilish (bepul)

1. railway.app ga kiring (GitHub bilan)
2. New Project → Deploy from GitHub repo
3. PostgreSQL qo'shing
4. Variables bo'limida `.env` qiymatlarini kiriting
5. Deploy tugmasini bosing ✅
