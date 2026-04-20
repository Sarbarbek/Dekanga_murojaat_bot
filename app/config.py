from __future__ import annotations

from dataclasses import dataclass
from typing import List

from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: List[int]        # Jami adminlar (super + dekanlar)
    super_admin_ids: List[int]  # Faqat super adminlar (ADMIN_IDS dan)
    kun_dekan_ids: List[int]    # Kunduzgi dekanat
    kech_dekan_ids: List[int]    # Kechki dekanat
    mag_dekan_ids: List[int]    # Magistratura
    sirt_dekan_ids: List[int]   # Sirtqi dekanat
    med_dekan_ids: List[int]    # Tibbiyot bo'limi
    pg_host: str
    pg_user: str
    pg_password: str
    pg_database: str
    pg_port: int
    database_url: str | None


def _parse_ids(raw: str) -> List[int]:
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    ids: List[int] = []
    for p in parts:
        try:
            ids.append(int(p))
        except ValueError as e:
            raise ValueError(f"Invalid ID value: {p}") from e
    return ids


def load_settings() -> Settings:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set in environment")

    admin_ids = _parse_ids(os.getenv("ADMIN_IDS", ""))
    kun_dekan_ids = _parse_ids(os.getenv("KUN_DEKAN_IDS", ""))
    kech_dekan_ids = _parse_ids(os.getenv("KECH_DEKAN_IDS", ""))
    mag_dekan_ids = _parse_ids(os.getenv("MAG_DEKAN_IDS", ""))
    sirt_dekan_ids = _parse_ids(os.getenv("SIRT_DEKAN_IDS", ""))
    med_dekan_ids = _parse_ids(os.getenv("MED_DEKAN_IDS", ""))

    all_admin_ids = list(set(admin_ids + kun_dekan_ids + kech_dekan_ids + mag_dekan_ids + sirt_dekan_ids + med_dekan_ids))
    
    # Debug log
    logger.info(f"DEBUG: Loaded {len(all_admin_ids)} total admins (Kun: {len(kun_dekan_ids)}, Kech: {len(kech_dekan_ids)}, Mag: {len(mag_dekan_ids)}, Sirt: {len(sirt_dekan_ids)}, Med: {len(med_dekan_ids)})")

    pg_host = os.getenv("PGHOST", "localhost").strip()
    pg_user = os.getenv("PGUSER", "postgres").strip()
    pg_password = os.getenv("PGPASSWORD", "").strip()
    pg_database = os.getenv("PGDATABASE", "murojaat_bot").strip()
    pg_port = int(os.getenv("PGPORT", "5432").strip() or "5432")
    database_url = os.getenv("DATABASE_URL", "").strip() or None

    return Settings(
        bot_token=bot_token,
        admin_ids=all_admin_ids,
        super_admin_ids=admin_ids,
        kun_dekan_ids=kun_dekan_ids,
        kech_dekan_ids=kech_dekan_ids,
        mag_dekan_ids=mag_dekan_ids,
        sirt_dekan_ids=sirt_dekan_ids,
        med_dekan_ids=med_dekan_ids,
        pg_host=pg_host,
        pg_user=pg_user,
        pg_password=pg_password,
        pg_database=pg_database,
        pg_port=pg_port,
        database_url=database_url,
    )
