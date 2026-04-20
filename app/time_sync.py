import asyncio
import aiohttp
from datetime import datetime, timezone, timedelta
import logging

logger = logging.getLogger(__name__)

# Global offset = True Time - Local Time
time_offset = timedelta(seconds=0)

async def sync_time_task():
    global time_offset
    url = "http://worldtimeapi.org/api/timezone/Asia/Tashkent"
    
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        true_time = datetime.fromisoformat(data['datetime'])
                        local_time = datetime.now(timezone(timedelta(hours=5)))
                        # calculate the difference between real time and machine time
                        time_offset = true_time - local_time
                        logger.debug(f"Vaqt sinxronizatsiya qilindi. Farq: {time_offset.total_seconds():.2f} s")
        except Exception as e:
            logger.debug(f"Vaqtni sinxronizatsiya qilishda xatolik: {e}")
            
        # Har 1 daqiqada yangilab turish
        await asyncio.sleep(60)

def now_utc5() -> datetime:
    """Aniq, internet orqali tekshirilgan UTC+5 vaqtini qaytaradi."""
    local_time = datetime.now(timezone(timedelta(hours=5)))
    return local_time + time_offset

def get_now_utc5_str() -> str:
    """Aniq vaqtni matn ko'rinishida qaytarish."""
    return now_utc5().strftime("%Y-%m-%d %H:%M:%S")
