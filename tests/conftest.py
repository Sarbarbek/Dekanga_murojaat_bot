"""
Barcha testlar uchun umumiy fixtures (conftest.py).
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.config import Settings


def make_settings(
    super_admin_ids=None,
    kun_ids=None,
    kech_ids=None,
    mag_ids=None,
) -> Settings:
    """Test maqsadida sodda Settings obyektini yaratadi."""
    super_admin_ids = super_admin_ids or [100]
    kun_ids = kun_ids or [200]
    kech_ids = kech_ids or [300]
    mag_ids = mag_ids or [400]

    all_admins = list(set(super_admin_ids + kun_ids + kech_ids + mag_ids))

    return Settings(
        bot_token="TEST_TOKEN",
        admin_ids=all_admins,
        super_admin_ids=super_admin_ids,
        kun_dekan_ids=kun_ids,
        kech_dekan_ids=kech_ids,
        mag_dekan_ids=mag_ids,
        pg_host="localhost",
        pg_user="test",
        pg_password="test",
        pg_database="test_db",
        pg_port=5432,
        webhook_url=None,
        webhook_path="/webhook",
        webapp_host="0.0.0.0",
        webapp_port=8080,
    )


def make_message(text: str = "", user_id: int = 999) -> MagicMock:
    """Mock aiogram Message obyektini yaratadi."""
    msg = MagicMock()
    msg.text = text
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.from_user.full_name = "Test User"
    msg.answer = AsyncMock()
    msg.answer_photo = AsyncMock()
    msg.contact = None
    msg.photo = None
    msg.document = None
    msg.video = None
    msg.audio = None
    msg.voice = None
    msg.caption = None
    return msg


def make_state(data: dict = None) -> MagicMock:
    """Mock FSMContext obyektini yaratadi."""
    state = MagicMock()
    _data = data or {}
    state.get_data = AsyncMock(return_value=_data)
    state.update_data = AsyncMock()
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    return state
