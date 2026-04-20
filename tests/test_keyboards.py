"""
keyboards.py funksiyalari uchun unit testlar.
"""
from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

from app.keyboards import (
    admin_answer_kb,
    admin_list_pager_kb,
    admin_menu,
    back_kb,
    broadcast_confirm_kb,
    contact_kb,
    dekan_menu,
    department_kb,
    media_extra_kb,
    user_menu,
)


class TestUserMenu:
    def test_returns_reply_keyboard(self):
        kb = user_menu()
        assert isinstance(kb, ReplyKeyboardMarkup)

    def test_has_yangi_murojaat_button(self):
        kb = user_menu()
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "📝 Yangi murojaat" in texts

    def test_resize_keyboard_enabled(self):
        assert user_menu().resize_keyboard is True


class TestDepartmentKb:
    def test_returns_reply_keyboard(self):
        assert isinstance(department_kb(), ReplyKeyboardMarkup)

    def test_contains_all_departments(self):
        kb = department_kb()
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "☀️ Kunduzgi dekanat" in texts
        assert "🌙 Kechki dekanat" in texts
        assert "🎓 Magistratura bo'limi" in texts

    def test_contains_back_button(self):
        kb = department_kb()
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "⬅️ Ortga" in texts

    def test_contains_restart_button(self):
        kb = department_kb()
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "🔄 Qayta boshlash" in texts

    def test_sirtqi_not_visible(self):
        """Sirtqi dekanat comment qilingan bo'lishi kerak."""
        kb = department_kb()
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "🏫 Sirtqi dekanat" not in texts


class TestBackKb:
    def test_has_ortga_button(self):
        kb = back_kb()
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "⬅️ Ortga" in texts

    def test_has_restart_button(self):
        kb = back_kb()
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "🔄 Qayta boshlash" in texts


class TestAdminMenu:
    def test_returns_reply_keyboard(self):
        assert isinstance(admin_menu(), ReplyKeyboardMarkup)

    def test_contains_statistika(self):
        kb = admin_menu()
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "📊 Statistika" in texts

    def test_contains_qidiruv(self):
        kb = admin_menu()
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "🔍 Qidiruv" in texts

    def test_contains_all_download_buttons(self):
        kb = admin_menu()
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "📥 Javob berilmaganlarni yuklab olish" in texts
        assert "📥 Javob berilganlarni yuklab olish" in texts
        assert "📥 Umumiy holatni yuklab olish" in texts

    def test_contains_broadcast(self):
        kb = admin_menu()
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "📢 Xabar yuborish" in texts


class TestDekanMenu:
    def test_returns_reply_keyboard(self):
        assert isinstance(dekan_menu(), ReplyKeyboardMarkup)

    def test_contains_only_download_and_restart(self):
        kb = dekan_menu()
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "📥 Umumiy holatni yuklab olish" in texts
        assert "🔄 Qayta boshlash" in texts

    def test_no_statistika(self):
        kb = dekan_menu()
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "📊 Statistika" not in texts

    def test_no_qidiruv(self):
        kb = dekan_menu()
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "🔍 Qidiruv" not in texts

    def test_no_murojaatlar_buttons(self):
        """Dekanlarda eski murojaatlar roʻyxat tugmalar boʻlmasligi kerak."""
        kb = dekan_menu()
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "🗂 Murojaatlar (Yangi)" not in texts
        assert "✅ Murojaatlar (Javob berilgan)" not in texts


class TestAdminAnswerKb:
    def test_returns_inline_keyboard(self):
        kb = admin_answer_kb(42)
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_callback_data_contains_id(self):
        kb = admin_answer_kb(42)
        btn = kb.inline_keyboard[0][0]
        assert "42" in btn.callback_data
        assert btn.callback_data == "answer:42"


class TestAdminListPagerKb:
    def test_returns_inline_keyboard(self):
        kb = admin_list_pager_kb("new", 0, 10)
        assert isinstance(kb, InlineKeyboardMarkup)

    def test_prev_offset_min_zero(self):
        """offset=0 da prev ham 0 bo'lishi kerak."""
        kb = admin_list_pager_kb("new", 0, 10)
        prev_btn = kb.inline_keyboard[0][0]
        assert "0" in prev_btn.callback_data

    def test_next_offset_increments(self):
        kb = admin_list_pager_kb("new", 0, 10)
        next_btn = kb.inline_keyboard[0][1]
        assert "10" in next_btn.callback_data

    def test_callback_data_includes_status(self):
        kb = admin_list_pager_kb("answered", 10, 10)
        for btn in kb.inline_keyboard[0]:
            assert "answered" in btn.callback_data


class TestBroadcastConfirmKb:
    def test_has_confirm_and_cancel(self):
        kb = broadcast_confirm_kb()
        callbacks = [btn.callback_data for row in kb.inline_keyboard for btn in row]
        assert "broadcast:confirm" in callbacks
        assert "broadcast:cancel" in callbacks


class TestMediaExtraKb:
    def test_has_shart_emas_button(self):
        kb = media_extra_kb()
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "✅ Shart emas, yuborish" in texts

    def test_has_izoh_button(self):
        kb = media_extra_kb()
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "✍️ Izoh yozish" in texts


class TestContactKb:
    def test_has_contact_button(self):
        kb = contact_kb()
        texts = [btn.text for row in kb.keyboard for btn in row]
        assert "📱 Kontaktni yuborish" in texts

    def test_contact_button_requests_contact(self):
        kb = contact_kb()
        for row in kb.keyboard:
            for btn in row:
                if btn.text == "📱 Kontaktni yuborish":
                    assert btn.request_contact is True
