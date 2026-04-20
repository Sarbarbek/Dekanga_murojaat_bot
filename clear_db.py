import asyncio
from app.config import load_settings
from app.db import Database

async def clear_db():
    settings = load_settings()
    db = Database(
        host=settings.pg_host,
        user=settings.pg_user,
        password=settings.pg_password,
        db=settings.pg_database,
        port=settings.pg_port,
    )
    await db.init()
    async with db.pool.acquire() as conn:
        await conn.execute("DELETE FROM murojaatlar;")
        print("Murojaatlar tozalandi!")
    await db.close()

asyncio.run(clear_db())
