from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from app.config import Settings
from app.keyboards import admin_menu, dekan_menu, department_kb
from aiogram.types import ReplyKeyboardRemove
from app.states import MurojaatStates
from app.utils import is_admin, is_super_admin

from app.db import Database
import logging
router = Router(name=__name__)

logger = logging.getLogger(__name__)

DEPARTMENTS = {"🌙 Kechki dekanat", "☀️ Kunduzgi dekanat", "🎓 Magistratura bo'limi"}

import os
from aiogram.types import FSInputFile

@router.message(Command("start"), StateFilter("*"))
async def start_cmd(message: types.Message, state: FSMContext, settings: Settings, db: Database) -> None:
    # Debug log
    logger.info(f"DEBUG: /start received from {message.from_user.id}")
    await state.clear()
    
    has_photo = os.path.exists("image.png")
    if has_photo:
        photo = FSInputFile("image.png")
    
    # Foydalanuvchini DBga saqlash (broadcast uchun)
    await db.update_user(message.from_user.id, message.from_user.full_name, message.from_user.username)

    # Adminlikni tekshirish
    if is_admin(settings, message.from_user.id):
        logger.info(f"DEBUG: User {message.from_user.id} is ADMIN")
        
        # Super admin yoki dekan ekanligiga qarab menyu tanlash
        if is_super_admin(settings, message.from_user.id):
            menu = admin_menu()
            text = "Salom super admin"
        else:
            from app.utils import get_admin_role
            role = get_admin_role(settings, message.from_user.id)
            role_names = {
                "kun": "Kunduzgi",
                "kech": "Kechki",
                "mag": "Magistratura",
                "sirt": "Sirtqi",
                "med": "Tibbiyot",
            }
            role_label = role_names.get(role, "")
            menu = dekan_menu()
            text = (
                f"Salom {role_label} ta'lim yo'nalish rahbari.\n\n"
                "Siz o'zingizni bo'limingizga tegishli talabalardan kelgan murojaatlarni "
                "qabul qilib, javob yozishingiz mumkin bo'ladi."
            )
            
        if has_photo:
            await message.answer_photo(
                photo=photo,
                caption=text,
                reply_markup=menu,
            )
        else:
            await message.answer(
                text=text,
                reply_markup=menu,
            )
    else:
        logger.info(f"DEBUG: User {message.from_user.id} is NORMAL USER")
        caption_text = (
            "👋 Assalomu aleykum!\n\n"
            "<b>TOSHKENT KIMYO XALQARO UNIVERSITETI NAMANGAN FILIALI yo'nalish rahbarlariga murojaat botiga xush kelibsiz.</b>\n\n"
            "Mazkur bot talabalar o‘z murojaatlarini yuborishlari uchun mo‘ljallangan. Barcha xabarlar to‘g‘ridan-to‘g‘ri fakultet dekanlariga yuboriladi.\n\n"
            "Iltimos, qaysi bo'limga murojaat qilmoqchisiz?"
        )
        if has_photo:
            await message.answer_photo(
                photo=photo,
                caption=caption_text,
                parse_mode="HTML",
                reply_markup=department_kb(),
            )
        else:
             await message.answer(
                text=caption_text,
                parse_mode="HTML",
                reply_markup=department_kb(),
            )
        await state.set_state(MurojaatStates.department)


@router.message(F.text == "🔄 Qayta boshlash", StateFilter("*"))
async def restart_cmd(message: types.Message, state: FSMContext, settings: Settings, db: Database) -> None:
    await state.clear()
    await start_cmd(message, state, settings, db)


@router.message(Command("cancel"))
async def cancel_cmd(message: types.Message, state: FSMContext, settings: Settings) -> None:
    await state.clear()
    if is_admin(settings, message.from_user.id):
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
    else:
        await message.answer("Bekor qilindi.", reply_markup=department_kb())
        await state.set_state(MurojaatStates.department)
