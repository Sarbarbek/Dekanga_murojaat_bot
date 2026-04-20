# Dekanga Murojaat Bot

Toshkent Davlat Agrar Universiteti (TDAU) talabalari uchun "Dekanga murojaat" telegram boti.

## Loyiha Tavsifi

Ushbu bot orqali talabalar o'z dekanatlariga murojaat yo'llashlari mumkin. Murojaatlar dekanlar tomonidan ko'rib chiqiladi va javob qaytariladi.

## Texnologiyalar

- **Python 3.10+**
- **Aiogram 3** - Telegram Bot API uchun framework
- **PostgreSQL** - Ma'lumotlar ombori
- **Aiohttp** - Asinxron HTTP so'rovlar

## O'rnatish

1. Loyihani yuklab oling:
   ```bash
   git clone https://github.com/Sarbarbek/Dekanga_murojaat_bot.git
   cd Dekanga_murojaat_bot
   ```

2. Virtual muhit yarating va faollashtiring:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. Zaruriy paketlarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```

4. `.env` faylini yarating va sozlang ( `.env.example` dan namuna oling):
   ```
   BOT_TOKEN=Sizning_bot_tokeningiz
   ADMIN_IDS=Admin_IDlar
   PGHOST=localhost
   PGUSER=postgres
   PGPASSWORD=password
   PGDATABASE=dekangamurojaat
   PGPORT=5432
   ```

5. Botni ishga tushiring:
   ```bash
   python main.py
   ```

## Muallif
[Sarbarbek](https://github.com/Sarbarbek)
