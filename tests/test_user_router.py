"""
routers/user.py handlerlari uchun unit testlar.
"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from tests.conftest import make_message, make_settings, make_state


# ─── Yordamchi ───────────────────────────────────────────────────────────────

def _import_handlers():
    """Router handlerlariga to'g'ridan-to'g'ri murojaat qilish uchun"""
    from app.routers.user import (
        new_appeal_btn,
        appeal_department,
        appeal_group_name,
        appeal_full_name,
        appeal_passport,
        appeal_phone,
        appeal_body,
        DEPARTMENTS,
    )
    return {
        "new_appeal_btn": new_appeal_btn,
        "appeal_department": appeal_department,
        "appeal_group_name": appeal_group_name,
        "appeal_full_name": appeal_full_name,
        "appeal_passport": appeal_passport,
        "appeal_phone": appeal_phone,
        "appeal_body": appeal_body,
        "departments": DEPARTMENTS,
    }


# ─── DEPARTMENTS sluglari ─────────────────────────────────────────────────────

class TestDepartmentsDict:
    def test_kun_key(self):
        h = _import_handlers()
        assert h["departments"]["☀️ Kunduzgi dekanat"] == "kun"

    def test_kech_key(self):
        h = _import_handlers()
        assert h["departments"]["🌙 Kechki dekanat"] == "kech"

    def test_mag_key(self):
        h = _import_handlers()
        assert h["departments"]["🎓 Magistratura bo'limi"] == "mag"

    def test_sirtqi_not_in_departments(self):
        h = _import_handlers()
        assert "🏫 Sirtqi dekanat" not in h["departments"]


# ─── new_appeal_btn ──────────────────────────────────────────────────────────

class TestNewAppealBtn:
    @pytest.mark.asyncio
    async def test_clears_state(self):
        h = _import_handlers()
        msg = make_message("📝 Yangi murojaat")
        state = make_state()
        await h["new_appeal_btn"](msg, state)
        state.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_sends_answer(self):
        h = _import_handlers()
        msg = make_message("📝 Yangi murojaat")
        state = make_state()
        await h["new_appeal_btn"](msg, state)
        msg.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_sets_department_state(self):
        h = _import_handlers()
        msg = make_message("📝 Yangi murojaat")
        state = make_state()
        await h["new_appeal_btn"](msg, state)
        state.set_state.assert_called_once()


# ─── appeal_department ────────────────────────────────────────────────────────

class TestAppealDepartment:
    @pytest.mark.asyncio
    async def test_ortga_clears_and_returns(self):
        h = _import_handlers()
        msg = make_message("⬅️ Ortga")
        state = make_state()
        await h["appeal_department"](msg, state)
        state.clear.assert_called_once()
        msg.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_text_shows_departments_again(self):
        h = _import_handlers()
        msg = make_message("Noto'g'ri matn")
        state = make_state()
        await h["appeal_department"](msg, state)
        # state o'zgarmaydi, faqat javob yuboriladi
        msg.answer.assert_called_once()
        state.update_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_valid_kunduzgi_updates_state(self):
        h = _import_handlers()
        msg = make_message("☀️ Kunduzgi dekanat")
        state = make_state()
        await h["appeal_department"](msg, state)
        state.update_data.assert_called_once()
        # department_key = "kun" bo'lishi kerak
        call_kwargs = state.update_data.call_args.kwargs
        assert call_kwargs.get("department_key") == "kun"

    @pytest.mark.asyncio
    async def test_valid_kech_updates_state(self):
        h = _import_handlers()
        msg = make_message("🌙 Kechki dekanat")
        state = make_state()
        await h["appeal_department"](msg, state)
        call_kwargs = state.update_data.call_args.kwargs
        assert call_kwargs.get("department_key") == "kech"

    @pytest.mark.asyncio
    async def test_valid_mag_updates_state(self):
        h = _import_handlers()
        msg = make_message("🎓 Magistratura bo'limi")
        state = make_state()
        await h["appeal_department"](msg, state)
        call_kwargs = state.update_data.call_args.kwargs
        assert call_kwargs.get("department_key") == "mag"

    @pytest.mark.asyncio
    async def test_advances_to_group_name_state(self):
        h = _import_handlers()
        msg = make_message("☀️ Kunduzgi dekanat")
        state = make_state()
        from app.states import MurojaatStates
        await h["appeal_department"](msg, state)
        state.set_state.assert_called_once_with(MurojaatStates.group_name)


# ─── appeal_passport ──────────────────────────────────────────────────────────

class TestAppealPassport:
    @pytest.mark.asyncio
    async def test_short_passport_rejected(self):
        h = _import_handlers()
        msg = make_message("AA123")  # 5 ta — o'ta qisqa
        state = make_state()
        await h["appeal_passport"](msg, state)
        state.update_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_valid_passport_accepted(self):
        h = _import_handlers()
        msg = make_message("AA1234567")
        state = make_state()
        await h["appeal_passport"](msg, state)
        state.update_data.assert_called_once()
        call_kwargs = state.update_data.call_args.kwargs
        assert call_kwargs.get("passport") == "AA1234567"

    @pytest.mark.asyncio
    async def test_ortga_goes_back(self):
        h = _import_handlers()
        msg = make_message("⬅️ Ortga")
        state = make_state()
        from app.states import MurojaatStates
        await h["appeal_passport"](msg, state)
        state.set_state.assert_called_once_with(MurojaatStates.full_name)


# ─── appeal_phone ─────────────────────────────────────────────────────────────

class TestAppealPhone:
    @pytest.mark.asyncio
    async def test_text_phone_accepted(self):
        h = _import_handlers()
        msg = make_message("+998901234567")
        state = make_state()
        await h["appeal_phone"](msg, state)
        state.update_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_contact_phone_used(self):
        h = _import_handlers()
        msg = make_message("")
        msg.contact = MagicMock()
        msg.contact.phone_number = "+998991112233"
        state = make_state()
        await h["appeal_phone"](msg, state)
        call_kwargs = state.update_data.call_args.kwargs
        assert call_kwargs.get("phone") == "+998991112233"

    @pytest.mark.asyncio
    async def test_empty_phone_rejected(self):
        h = _import_handlers()
        msg = make_message("")
        msg.contact = None
        state = make_state()
        await h["appeal_phone"](msg, state)
        state.update_data.assert_not_called()


# ─── appeal_body (media boʻlsa) ────────────────────────────────────────────────

class TestAppealBodyMedia:
    @pytest.mark.asyncio
    async def test_photo_detected(self):
        h = _import_handlers()
        msg = make_message("")
        mock_photo = MagicMock()
        mock_photo.file_id = "photo_file_id_123"
        msg.photo = [mock_photo]

        state = make_state()
        db = AsyncMock()
        bot = AsyncMock()
        settings = make_settings()

        await h["appeal_body"](msg, state, db, bot, settings)
        # temp_body va file_id update_data ga uzatilishi kerak
        state.update_data.assert_called()

    @pytest.mark.asyncio
    async def test_text_murojaat_calls_finish_appeal(self):
        """Oddiy matn bo'lsa _finish_appeal chaqiriladi."""
        h = _import_handlers()
        msg = make_message("Bu mening murojaatim")
        state = make_state(data={
            "full_name": "Test User",
            "passport": "AA1234567",
            "phone": "+998901234567",
            "group_name": "ISE_N-23UA",
            "department_key": "kun",
            "body_text": "",
        })

        db = AsyncMock()
        db.create_murojaat = AsyncMock(return_value=1)
        bot = AsyncMock()
        settings = make_settings(super_admin_ids=[100], kun_ids=[200])

        await h["appeal_body"](msg, state, db, bot, settings)
        db.create_murojaat.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_text_no_media_rejected(self):
        h = _import_handlers()
        msg = make_message("")  # bo'sh matn
        msg.photo = None
        msg.document = None
        msg.video = None
        msg.audio = None
        msg.voice = None
        state = make_state()
        db = AsyncMock()
        bot = AsyncMock()
        settings = make_settings()

        await h["appeal_body"](msg, state, db, bot, settings)
        # create_murojaat chaqirilmasligi kerak
        db.create_murojaat.assert_not_called()
