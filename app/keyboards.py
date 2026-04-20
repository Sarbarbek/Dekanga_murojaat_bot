from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def department_kb() -> ReplyKeyboardMarkup:
    """Dekanat tanlash klaviaturasi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="☀️ Kunduzgi dekanat"), KeyboardButton(text="🌙 Kechki dekanat")],
            [KeyboardButton(text="🏫 Sirtqi dekanat"), KeyboardButton(text="🎓 Magistratura bo'limi")],
            [KeyboardButton(text="🩺 Tibbiyot taʼlim yoʻnalishi")],
            [KeyboardButton(text="🔄 Qayta boshlash")],
        ],
        resize_keyboard=True,
    )


def back_kb() -> ReplyKeyboardMarkup:
    """Faqat 'Ortga' va 'Qayta boshlash' tugmasi bor klaviatura."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Ortga")],
            [KeyboardButton(text="🔄 Qayta boshlash")],
        ],
        resize_keyboard=True,
    )


def contact_kb() -> ReplyKeyboardMarkup:
    """Telefon raqami va kontakt yuborish tugmasi."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Kontaktni yuborish", request_contact=True)],
            [KeyboardButton(text="⬅️ Ortga"), KeyboardButton(text="🔄 Qayta boshlash")],
        ],
        resize_keyboard=True,
    )




def admin_menu() -> ReplyKeyboardMarkup:
    """Super Admin uchun menyu (hamma tugmalar)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🔍 Qidiruv")],
            [KeyboardButton(text="🗂 Murojaatlar (Yangi)"), KeyboardButton(text="✅ Murojaatlar (Javob berilgan)")],
            [KeyboardButton(text="📥 Umumiy holatni yuklab olish"), KeyboardButton(text="👥 Foydalanuvchilar")],
            [KeyboardButton(text="📢 Xabar yuborish")],
            [KeyboardButton(text="💾 Zahira nusxa (Backup)"), KeyboardButton(text="📥 Ma'lumotni tiklash (Restore)")],
            [KeyboardButton(text="⚙️ Bot holati"), KeyboardButton(text="📋 Loglarni yuklash")],
        ],
        resize_keyboard=True,
    )


def dekan_menu() -> ReplyKeyboardMarkup:
    """Dekanlar uchun menyu (faqat zarur tugmalar)."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Umumiy holatni yuklab olish")],
            [KeyboardButton(text="👥 Foydalanuvchilar")],
            [KeyboardButton(text="🔄 Qayta boshlash")],
        ],
        resize_keyboard=True,
    )


def admin_answer_kb(appeal_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍️ Javob berish",
                    callback_data=f"answer:{appeal_id}",
                )
            ]
        ]
    )


def admin_list_pager_kb(status: str, offset: int, limit: int) -> InlineKeyboardMarkup:
    prev_offset = max(0, offset - limit)
    next_offset = offset + limit
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Oldingi",
                    callback_data=f"list:{status}:{prev_offset}",
                ),
                InlineKeyboardButton(
                    text="➡️ Keyingi",
                    callback_data=f"list:{status}:{next_offset}",
                ),
            ]
        ]
    )


def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="broadcast:confirm"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="broadcast:cancel"),
            ]
        ]
    )


def media_extra_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Shart emas, yuborish")],
            [KeyboardButton(text="✍️ Izoh yozish")],
            [KeyboardButton(text="⬅️ Ortga"), KeyboardButton(text="🔄 Qayta boshlash")],
        ],
        resize_keyboard=True,
    )


def export_departments_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="☀️ Kunduzgi", callback_data="export:kun"),
                InlineKeyboardButton(text="🌙 Kechki", callback_data="export:kech"),
            ],
            [
                InlineKeyboardButton(text="🎓 Magistratura", callback_data="export:mag"),
                InlineKeyboardButton(text="🏫 Sirtqi", callback_data="export:sirt"),
            ],
            [
                InlineKeyboardButton(text="🩺 Tibbiyot", callback_data="export:med"),
                InlineKeyboardButton(text="📊 Barchasi", callback_data="export:all"),
            ]
        ]
    )

def users_list_pager_kb(offset: int, limit: int, total: int) -> InlineKeyboardMarkup:
    prev_offset = max(0, offset - limit)
    next_offset = offset + limit
    buttons = []
    if offset > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"users_list:{prev_offset}"))
    if next_offset < total:
        buttons.append(InlineKeyboardButton(text="➡️ Keyingi", callback_data=f"users_list:{next_offset}"))
    
    return InlineKeyboardMarkup(inline_keyboard=[buttons] if buttons else [])


