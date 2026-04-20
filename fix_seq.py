import asyncio
import asyncpg
from app.config import load_settings

async def main():
    settings = load_settings()
    pool = await asyncpg.create_pool(
        host=settings.pg_host,
        user=settings.pg_user,
        password=settings.pg_password,
        database=settings.pg_database,
        port=settings.pg_port
    )
    async with pool.acquire() as conn:
        await conn.execute("SELECT setval(pg_get_serial_sequence('murojaatlar', 'id'), coalesce(max(id), 0) + 1, false) FROM murojaatlar;")
        print("Sequence muvaffaqiyatli to'g'rilandi!")
    await pool.close()

if __name__ == '__main__':
    asyncio.run(main())
