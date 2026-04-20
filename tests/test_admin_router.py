"""
routers/admin.py handlerlari uchun unit testlar.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from tests.conftest import make_message, make_settings, make_state


def _get_handlers():
    from app.routers.admin import (
        admin_cmd,
        admin_statistics,
        admin_list_new,
        admin_list_answered,
        admin_start_search,
    )
    return {
        "admin_cmd": admin_cmd,
        "admin_statistics": admin_statistics,
        "admin_list_new": admin_list_new,
        "admin_list_answered": admin_list_answered,
        "admin_start_search": admin_start_search,
    }


# ─── /admin buyrug'i ───────────────────────────────────────────────────────────

class TestAdminCmd:
    @pytest.mark.asyncio
    async def test_non_admin_ignored(self):
        h = _get_handlers()
        settings = make_settings(super_admin_ids=[100], kun_ids=[200])
        msg = make_message("/admin", user_id=999)
        state = make_state()
        await h["admin_cmd"](msg, state, settings)
        msg.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_super_admin_gets_admin_menu(self):
        h = _get_handlers()
        settings = make_settings(super_admin_ids=[100])
        msg = make_message("/admin", user_id=100)
        state = make_state()
        await h["admin_cmd"](msg, state, settings)
        msg.answer.assert_called_once()
        args, kwargs = msg.answer.call_args
        # Super admin uchun "Salom super admin" matni
        text = args[0] if args else kwargs.get("text", "")
        assert "super admin" in text.lower()

    @pytest.mark.asyncio
    async def test_dekan_gets_dekan_menu(self):
        h = _get_handlers()
        settings = make_settings(super_admin_ids=[100], kun_ids=[200])
        msg = make_message("/admin", user_id=200)
        state = make_state()
        await h["admin_cmd"](msg, state, settings)
        msg.answer.assert_called_once()
        _, kwargs = msg.answer.call_args
        # Dekan menyu `dekan_menu()` bo'lishi kerak
        from app.keyboards import dekan_menu
        expected_kb = dekan_menu()
        actual_kb = kwargs.get("reply_markup")
        # Klaviatura tugmalarini solishtirish
        actual_texts = [b.text for row in actual_kb.keyboard for b in row]
        expected_texts = [b.text for row in expected_kb.keyboard for b in row]
        assert actual_texts == expected_texts


# ─── Statistika handleri ──────────────────────────────────────────────────────

class TestAdminStatistics:
    @pytest.mark.asyncio
    async def test_non_super_admin_ignored(self):
        h = _get_handlers()
        settings = make_settings(super_admin_ids=[100], kun_ids=[200])
        msg = make_message("📊 Statistika", user_id=200)  # dekan — o'tmaydi
        db = AsyncMock()
        await h["admin_statistics"](msg, settings, db)
        db.get_statistics.assert_not_called()
        msg.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_super_admin_gets_stats(self):
        h = _get_handlers()
        settings = make_settings(super_admin_ids=[100])
        msg = make_message("📊 Statistika", user_id=100)
        db = AsyncMock()
        db.get_statistics = AsyncMock(return_value={
            "total": 10,
            "new_count": 5,
            "answered_count": 5,
            "today_total": 3,
            "today_new": 2,
        })
        await h["admin_statistics"](msg, settings, db)
        db.get_statistics.assert_called_once()
        msg.answer.assert_called_once()


# ─── Murojaatlar ro'yxati ─────────────────────────────────────────────────────

class TestAdminListNew:
    @pytest.mark.asyncio
    async def test_non_super_admin_cant_list(self):
        h = _get_handlers()
        settings = make_settings(super_admin_ids=[100], kun_ids=[200])
        msg = make_message("🗂 Murojaatlar (Yangi)", user_id=200)
        db = AsyncMock()
        await h["admin_list_new"](msg, settings, db)
        db.list_murojaatlar_by_status.assert_not_called()

    @pytest.mark.asyncio
    async def test_super_admin_can_list(self):
        h = _get_handlers()
        settings = make_settings(super_admin_ids=[100])
        msg = make_message("🗂 Murojaatlar (Yangi)", user_id=100)
        db = AsyncMock()
        db.list_murojaatlar_by_status = AsyncMock(return_value=[])
        await h["admin_list_new"](msg, settings, db)
        db.list_murojaatlar_by_status.assert_called_once()


class TestAdminListAnswered:
    @pytest.mark.asyncio
    async def test_non_super_admin_blocked(self):
        h = _get_handlers()
        settings = make_settings(super_admin_ids=[100], kech_ids=[300])
        msg = make_message("✅ Murojaatlar (Javob berilgan)", user_id=300)
        db = AsyncMock()
        await h["admin_list_answered"](msg, settings, db)
        db.list_murojaatlar_by_status.assert_not_called()


# ─── Qidiruv ──────────────────────────────────────────────────────────────────

class TestAdminStartSearch:
    @pytest.mark.asyncio
    async def test_dekan_cannot_search(self):
        h = _get_handlers()
        settings = make_settings(super_admin_ids=[100], mag_ids=[400])
        msg = make_message("🔍 Qidiruv", user_id=400)
        state = make_state()
        await h["admin_start_search"](msg, state, settings)
        state.set_state.assert_not_called()
        msg.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_super_admin_can_search(self):
        h = _get_handlers()
        settings = make_settings(super_admin_ids=[100])
        msg = make_message("🔍 Qidiruv", user_id=100)
        state = make_state()
        await h["admin_start_search"](msg, state, settings)
        msg.answer.assert_called_once()
        state.set_state.assert_called_once()
