import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher

from app.config import load_settings
from app.db import Database
from app.routers import admin, common, user

async def schedule_daily_backup(bot: Bot, db: Database, admin_ids: list[int]):
    import datetime
    import json
    import io
    from aiogram.types import BufferedInputFile
    
    while True:
        # Hozirgi vaqtni UTC+5 da aniqlash
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5)))
        target_time = now.replace(hour=0, minute=1, second=0, microsecond=0)
        
        # Agar soat 00:01 dan o'tib ketgan bo'lsa, keyingi kunga o'tkazamiz
        if now >= target_time:
            target_time += datetime.timedelta(days=1)
            
        wait_seconds = (target_time - now).total_seconds()
        logging.info(f"Keyingi avtomatik backup {wait_seconds} soniyadan so'ng (00:01) olinadi.")
        await asyncio.sleep(wait_seconds)
        
        try:
            backup_data = await db.get_full_backup()
            json_str = json.dumps(backup_data, indent=2, ensure_ascii=False)
            
            bio = io.BytesIO(json_str.encode('utf-8'))
            bio.seek(0)
            
            filename = f"auto_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            file = BufferedInputFile(bio.getvalue(), filename=filename)
            
            for admin_id in admin_ids:
                try:
                    await bot.send_document(
                        chat_id=admin_id, 
                        document=file, 
                        caption="🕒 Server avtomatik zahira nusxasi (00:01)\nUshbu faylni ehtiyot chorasi sifatida saqlab qo'ying."
                    )
                except Exception as e:
                    logging.error(f"Avto-backup yuborishda xatolik (admin_id={admin_id}): {e}")
        except Exception as e:
            logging.error(f"Avto-backup olishda xatolik: {e}")


async def main() -> None:
    settings = load_settings()

    # Logs papkasini yaratish
    if not os.path.exists("logs"):
        os.makedirs("logs")

    import datetime
    def get_time_utc5(*args):
        return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5))).timetuple()

    # Logging sozlamalari
    log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    log_formatter.converter = get_time_utc5
    # Konsolga chiqarish
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    
    # Faylga yozish (max 5MB, 5 ta zaxira fayl)
    file_handler = RotatingFileHandler("logs/bot.log", maxBytes=5*1024*1024, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(log_formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler]
    )

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    db = Database(
        host=settings.pg_host,
        user=settings.pg_user,
        password=settings.pg_password,
        db=settings.pg_database,
        port=settings.pg_port,
        dsn=settings.database_url
    )
    try:
        await db.init()
    except Exception as e:
        logging.error(f"Ma'lumotlar bazasiga ulanishda xatolik: {e}")
        print(f"\n❌ DIQQAT: PostgreSQL ma'lumotlar bazasiga ulanib bo'lmadi!\nSabab: {e}")
        print("💡 Iltimos, PostgreSQL xizmati yoqilganligini va '.env' faylidagi sozlamalar to'g'riligini tekshiring.\n")
        return

    # Bot menyusini (Menu tugmasi) sozlash
    from aiogram.types import BotCommand
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="cancel", description="Qayta ishga tushirish")
    ]
    await bot.set_my_commands(commands)
    
    dp["settings"] = settings
    dp["db"] = db

    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(user.router)

    # Avtomatik zahira taskini ishga tushirish (orqa fonda)
    asyncio.create_task(schedule_daily_backup(bot, db, settings.super_admin_ids))

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
