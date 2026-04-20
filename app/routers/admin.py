from __future__ import annotations

import io
import openpyxl
import asyncio
import os
import platform
import datetime
from typing import List, Tuple, Any, Optional

from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from app.config import Settings
from app.db import Database
from app.keyboards import admin_list_pager_kb, admin_menu, broadcast_confirm_kb, dekan_menu, department_kb
from app.states import AdminAnswerStates, AdminSearchStates, AdminBroadcastStates, AdminBackupStates
from app.utils import is_admin, get_admin_role, is_super_admin
import logging
import json

logger = logging.getLogger(__name__)

# Admin ID -> ism xaritasi (loglar uchun)
ADMIN_NAMES = {
    5989915268: "Sarbarbek",
    257398064: "Qahramon",
    2121812492: "Rahmatillo",
    6387458134: "Shukurillo",
    78823694: "Xadyatillo",
    6041010029: "Nosirjon",
    365271248: "Elmurod",
    2081897661: "Behruzbek",
    6369780293: "Abdullatif",
}

def admin_name(user_id: int) -> str:
    return ADMIN_NAMES.get(user_id, str(user_id))

router = Router(name=__name__)


@router.message(Command("admin"), StateFilter("*"))
async def admin_cmd(message: types.Message, state: FSMContext, settings: Settings) -> None:
    if not is_admin(settings, message.from_user.id):
        return
    await state.clear()
    
    if is_super_admin(settings, message.from_user.id):
        menu = admin_menu()
        text = "Salom super admin"
    else:
        role = get_admin_role(settings, message.from_user.id)
        menu = dekan_menu()
        if role == "kun":
            text = "Xush kelibsiz! Sizga kunduzgi ta'limga tegishli murojaatlar kelib tushadi."
        elif role == "kech":
            text = "Xush kelibsiz! Sizga kechki ta'limga tegishli murojaatlar kelib tushadi."
        elif role == "mag":
            text = "Xush kelibsiz! Sizga magistratura bo'limiga tegishli murojaatlar kelib tushadi."
        elif role == "sirt":
            text = "Xush kelibsiz! Sizga sirtqi ta'limga tegishli murojaatlar kelib tushadi."
        elif role == "med":
            text = "Xush kelibsiz! Sizga tibbiyot bo'limiga tegishli murojaatlar kelib tushadi."
        else:
            text = "Xush kelibsiz Admin. Siz o'zingizni bo'limingizga tegishli talabalardan kelgan murojaatlarni qabul qilib, javob yozishingiz mumkin bo'ladi."
        
    await message.answer(text, reply_markup=menu)


@router.message(F.text == "📊 Statistika")
async def admin_statistics(message: types.Message, settings: Settings, db: Database) -> None:
    if not is_super_admin(settings, message.from_user.id):
        return
    
    role = get_admin_role(settings, message.from_user.id)
    if role is None:
        return

    stats = await db.get_statistics(department_key=role)

    text = (
        "📈 *Statistika:*\n\n"
        f"Jami murojaatlar: {stats['total']}\n"
        f"Yangi kelganlar: {stats['new_count']}\n"
        f"Javob berilganlar: {stats['answered_count']}\n\n"
        "📅 *Bugungi holat:*\n\n"
        f"Bugun kelgan jami: {stats['today_total']}\n"
        f"Bugun kelgan yangi murojaatlar: {stats['today_new']}"
    )
    await message.answer(text, parse_mode="Markdown")


async def _send_murojaatlar_page(message: types.Message, db: Database, role: str, *, status: str, offset: int) -> None:
    limit = 10
    rows = await db.list_murojaatlar_by_status(status=status, department_key=role, limit=limit, offset=offset)
    
    menu = admin_menu() if role == "total" else dekan_menu()

    if not rows:
        await message.answer("Murojaatlar topilmadi.", reply_markup=menu)
        return

    title = "🔴 Yangi" if status == "new" else "🟢 Javob berilgan"
    icon = "🔴" if status == "new" else "🟢"
    lines = [f"{title} murojaatlar (offset={offset}):"]
    for appeal_id, user_id, full_name, group_name, created_at, body_text, username in rows:
        body_short = body_text.replace("\n", " ")[:140]
        uname_line = f' | <a href="https://t.me/{username}">@{username}</a>' if username else ""
        lines.append(
            f"{icon} {created_at}\n"
            f"{full_name} ({group_name}){uname_line}\n"
            f"{body_short}"
        )

    await message.answer("\n\n".join(lines), reply_markup=admin_list_pager_kb(status, offset, limit), parse_mode="HTML")


@router.message(F.text == "🗂 Murojaatlar (Yangi)")
async def admin_list_new(message: types.Message, settings: Settings, db: Database) -> None:
    if not is_super_admin(settings, message.from_user.id):
        return
    
    role = get_admin_role(settings, message.from_user.id)
    if role is None:
        return
    await _send_murojaatlar_page(message, db, role, status="new", offset=0)


@router.message(F.text == "✅ Murojaatlar (Javob berilgan)")
async def admin_list_answered(message: types.Message, settings: Settings, db: Database) -> None:
    if not is_super_admin(settings, message.from_user.id):
        return
    
    role = get_admin_role(settings, message.from_user.id)
    if role is None:
        return
    await _send_murojaatlar_page(message, db, role, status="answered", offset=0)


@router.callback_query(F.data.startswith("list:"))
async def admin_list_pager(call: types.CallbackQuery, settings: Settings, db: Database) -> None:
    role = get_admin_role(settings, call.from_user.id)
    if role is None:
        await call.answer("Ruxsat yo'q", show_alert=True)
        return

    try:
        _, status, offset_raw = call.data.split(":", 2)
        offset = max(0, int(offset_raw))
    except Exception:
        await call.answer("Xato", show_alert=True)
        return

    msg = call.message
    if msg is None:
        await call.answer()
        return

    limit = 10
    rows = await db.list_murojaatlar_by_status(status=status, department_key=role, limit=limit, offset=offset)
    if not rows:
        await call.answer("Murojaatlar topilmadi", show_alert=True)
        return

    title = "Yangi" if status == "new" else "Javob berilgan"
    lines = [f"{title} murojaatlar (offset={offset}):"]
    for appeal_id, user_id, full_name, group_name, created_at, body_text, username in rows:
        body_short = body_text.replace("\n", " ")[:140]
        uname_line = f' | <a href="https://t.me/{username}">@{username}</a>' if username else ""
        lines.append(
            f"{created_at}\n"
            f"{full_name} ({group_name}){uname_line}\n"
            f"{body_short}"
        )

    await msg.edit_text("\n\n".join(lines), reply_markup=admin_list_pager_kb(status, offset, limit), parse_mode="HTML")
    await call.answer()


async def _send_excel(message: types.Message, db: Database, role: str, *, status: str) -> None:
    wait_msg = await message.answer("📊 Ma'lumotlar hisoblanmoqda, iltimos kuting...")
    
    rows = await db.export_murojaatlar(status=status, department_key=role)
    total_count = len(rows)
    
    await wait_msg.edit_text(f"⏳ Jami {total_count} ta murojaat topildi. Fayl tayyorlanmoqda...")

    from openpyxl.styles import Font

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Murojaatlar"

    # Ustunlar strukturasi (updated)
    headers = [
        "№", "ID", "User ID", "Username", "F.I.SH", "Pasport", "Tel", "Guruh", "Bo'lim", 
        "Murojaat vaqti", "Javob berilgan vaqt", "Status", 
        "Murojaat matni", "Berilgan javob"
    ]
    ws.append(headers)

    # 1-qatorni bold qilish
    bold_font = Font(bold=True)
    for cell in ws[1]:
        cell.font = bold_font

    # Bo'lim nomlari xaritasi
    dep_map = {
        "kun": "Kunduzgi dekanat",
        "kech": "Kechki dekanat",
        "mag": "Magistratura bo'limi",
        "sirt": "Sirtqi dekanat",
        "med": "Tibbiyot bo'limi"
    }

    # Status xaritasi
    status_map = {
        "answered": "Javob berilgan",
        "new": "Javob berilmagan",
    }

    # Bo'limlar bo'yicha saralash (Super admin uchun 'total' bo'lganda foydali)
    # r[7] is department_key
    sorted_rows = sorted(rows, key=lambda x: x[7] or "")
    
    for idx, r in enumerate(sorted_rows, start=1):
        # r structure: (id, user_id, username, full_name, passport, phone, group_name, dep_key, created, answered, status, body, answer)
        data = list(r)
        # dep_key ni nomiga o'zgartiramiz
        data[7] = dep_map.get(data[7], data[7])
        # status ni o'zbekchaga o'zgartiramiz
        data[10] = status_map.get(data[10], data[10])
        # guruh nomini katta harflarga o'zgartiramiz
        if data[6]:
            data[6] = str(data[6]).upper()
        ws.append([idx] + data)

    # Ustunlar enini avtomatik sozlash
    for col_cells in ws.columns:
        length = max(len(str(cell.value or "")) for cell in col_cells)
        ws.column_dimensions[col_cells[0].column_letter].width = min(length + 2, 50)

    bio = io.BytesIO()
    wb.save(bio)
    bio.seek(0)

    file = types.BufferedInputFile(bio.getvalue(), filename=f"murojaatlar_{role}_{status}.xlsx")
    logger.info(f"{admin_name(message.from_user.id)} '{status}' turdagi '{role}' ro'yxatni Excel shaklida yuklab oldi. (Jami: {total_count} ta)")
    await message.answer_document(file, caption=f"✅ Jami murojaatlar soni: {total_count} ta")
    try:
        await wait_msg.delete()
    except Exception:
        pass


@router.message(F.text == "📥 Javob berilmaganlarni yuklab olish")
async def admin_export_new(message: types.Message, settings: Settings, db: Database) -> None:
    if not is_admin(settings, message.from_user.id):
        return
    role = get_admin_role(settings, message.from_user.id)
    if role is None:
        return
    await _send_excel(message, db, role, status="new")


@router.message(F.text == "📥 Javob berilganlarni yuklab olish")
async def admin_export_answered(message: types.Message, settings: Settings, db: Database) -> None:
    if not is_admin(settings, message.from_user.id):
        return
    role = get_admin_role(settings, message.from_user.id)
    if role is None:
        return
    await _send_excel(message, db, role, status="answered")


@router.message(F.text == "📥 Umumiy holatni yuklab olish")
async def admin_export_all(message: types.Message, settings: Settings, db: Database) -> None:
    role = get_admin_role(settings, message.from_user.id)
    if role is None:
        return

    if role != "total":
        await _send_excel(message, db, role, status="all")
        return

    from app.keyboards import export_departments_kb
    await message.answer("Qaysi bo'lim holatini yuklab olmoqchisiz?", reply_markup=export_departments_kb())


@router.callback_query(F.data.startswith("export:"))
async def admin_export_callback(call: types.CallbackQuery, settings: Settings, db: Database) -> None:
    role = get_admin_role(settings, call.from_user.id)
    if role != "total":
        await call.answer("Bunga ruxsatingiz yo'q!", show_alert=True)
        return
        
    target_role = call.data.split(":")[1]
    
    try:
        if call.message:
            await call.message.delete()
    except Exception:
        pass
        
    # call.message contains the chat to send the document to
    if call.message:
        await _send_excel(call.message, db, target_role, status="all")
    await call.answer()


@router.message(F.text == "🔍 Qidiruv")
async def admin_start_search(message: types.Message, state: FSMContext, settings: Settings) -> None:
    if not is_super_admin(settings, message.from_user.id):
        return

    await state.clear()
    await message.answer("Qidiruv uchun matn kiriting (ism, guruh bo'limi yoki murojaat matnining bir qismi):")
    await state.set_state(AdminSearchStates.waiting_query)


@router.message(AdminSearchStates.waiting_query)
async def admin_process_search(message: types.Message, state: FSMContext, settings: Settings, db: Database) -> None:
    role = get_admin_role(settings, message.from_user.id)
    if role is None:
        await state.clear()
        return

    query = (message.text or "").strip()
    if not query:
        await message.answer("Iltimos, qidiruv matnini yuboring yoki bekor qilish uchun menyudan foydalaning.")
        return

    rows = await db.search_murojaatlar(query=query, department_key=role, limit=10)

    if not rows:
        await message.answer("Hech qanday natija topilmadi.", reply_markup=admin_menu())
        await state.clear()
        return

    lines = [f"🔍 *'{query}' bo'yicha qidiruv natijalari:*"]
    for appeal_id, user_id, full_name, group_name, created_at, mstatus, body_text in rows:
        body_short = body_text.replace("\n", " ")[:140]
        status_icon = "🔴 Yangi (javobsiz)" if mstatus == "new" else "🟢 Javob berilgan"
        lines.append(
            f"{status_icon}\n"
            f"№{appeal_id} | {created_at}\n"
            f"{full_name} ({group_name}) | user_id={user_id}\n"
            f"{body_short}"
        )

    await message.answer("\n\n".join(lines), parse_mode="Markdown", reply_markup=admin_menu())
    await state.clear()


@router.callback_query(F.data.startswith("answer:"))
async def answer_start(call: types.CallbackQuery, state: FSMContext, settings: Settings) -> None:
    role = get_admin_role(settings, call.from_user.id)
    if role is None:
        await call.answer("Ruxsat yo'q", show_alert=True)
        return

    _, appeal_id_raw = call.data.split(":", 1)
    try:
        appeal_id = int(appeal_id_raw)
    except ValueError:
        await call.answer("Xato", show_alert=True)
        return

    await state.clear()
    await state.update_data(appeal_id=appeal_id)
    await state.set_state(AdminAnswerStates.waiting_answer)
    await call.message.answer(f"№{appeal_id} murojaat uchun javobingizni yozing:")
    await call.answer()


@router.message(AdminAnswerStates.waiting_answer)
async def answer_finish(message: types.Message, state: FSMContext, settings: Settings, db: Database, bot: types.Bot) -> None:
    if not is_admin(settings, message.from_user.id):
        await message.answer("Ruxsat yo'q")
        await state.clear()
        return

    data = await state.get_data()

    appeal_id = int(data.get("appeal_id"))
    owner_id = await db.get_murojaat_owner(appeal_id)
    if owner_id is None:
        await message.answer("Murojaat topilmadi.")
        await state.clear()
        return

    answer_text = (message.text or "").strip()
    if not answer_text:
        await message.answer("Javob matnini yuboring.")
        return

    is_success = await db.set_answer(appeal_id=appeal_id, answer_text=answer_text, answered_by=message.from_user.id)
    if not is_success:
        await message.answer("⚠️ Ushbu murojaatga allaqachon javob berilgan.")
        await state.clear()
        return

    # Unvonlarni aniqlash
    info = await db.get_murojaat_info(appeal_id)
    dep_key = info.get("department_key") if info else "kun"
    
    title = "Ta'lim yo'nalishi rahbaridan javob"
    if dep_key == "mag":
        title = "Magistratura bo'limi boshlig'idan javob"
    elif dep_key == "sirt":
        title = "Sirtqi ta'lim yo'nalishi rahbaridan javob"
    elif dep_key == "med":
        title = "Tibbiyot bo'limi dekanidan javob"

    try:
        await bot.send_message(
            owner_id,
            f"🔔 {title} keldi:\n\n{answer_text}\n\n<i>Yangi murojaat qoldirish uchun pastdagi menyudan foydalaning:</i>",
            parse_mode="HTML",
            reply_markup=department_kb()
        )
        await message.answer("Javob foydalanuvchiga yuborildi ✅")
    except Exception:
        await message.answer("Xatolik: foydalanuvchi botni bloklagan bo'lishi mumkin.")

    await state.clear()


# ─── Broadcast ─────────────────────────────────────────────────────────────

@router.message(F.text == "📢 Xabar yuborish")
async def admin_broadcast_start(message: types.Message, state: FSMContext, settings: Settings) -> None:
    if not is_super_admin(settings, message.from_user.id):
        return
    await message.answer("Barcha foydalanuvchilarga yuboriladigan xabarni kiriting (yoki bekor qilish uchun /cancel):")
    await state.set_state(AdminBroadcastStates.waiting_message)


@router.message(AdminBroadcastStates.waiting_message)
async def admin_broadcast_confirm(message: types.Message, state: FSMContext) -> None:
    await state.update_data(broadcast_msg=message.text)
    await message.answer(f"Ushbu xabarni barcha foydalanuvchilarga yuborasizmi?\n\n{message.text}", reply_markup=broadcast_confirm_kb())
    await state.set_state(AdminBroadcastStates.confirm_broadcast)


@router.callback_query(AdminBroadcastStates.confirm_broadcast, F.data.startswith("broadcast:"))
async def admin_broadcast_finish(call: types.CallbackQuery, state: FSMContext, db: Database, bot: types.Bot) -> None:
    action = call.data.split(":")[1]
    if action == "cancel":
        await call.message.edit_text("Bekor qilindi.")
        await state.clear()
        return

    data = await state.get_data()
    msg_text = str(data.get("broadcast_msg"))
    user_ids: List[int] = await db.get_all_user_ids()

    await call.message.edit_text(f"🚀 Xabar yuborish boshlandi... (Jami: {len(user_ids)})")
    
    success_count: int = 0
    fail_count: int = 0
    for uid in user_ids:
        try:
            await bot.send_message(uid, msg_text)
            success_count += 1  # type: ignore
        except Exception:
            fail_count += 1  # type: ignore
        await asyncio.sleep(0.05) # Telegram limitlariga amal qilish
        
    logger.info(f"{admin_name(call.from_user.id)} umumiy xabarnoma (broadcast) yubordi. (Yetkazildi: {success_count}, Xatolik: {fail_count})")

    await call.message.answer(f"✅ Xabar yuborish yakunlandi.\n\nYetkazildi: {success_count}\nXatolik: {fail_count}")
    await state.clear()


# ─── Monitoring ────────────────────────────────────────────────────────────

@router.message(F.text == "⚙️ Bot holati")
async def admin_bot_status(message: types.Message, settings: Settings) -> None:
    if not is_super_admin(settings, message.from_user.id):
        return

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    os_info = f"{platform.system()} {platform.release()}"
    
    # Log fayli hajmini tekshirish
    log_size = "Noma'lum"
    if os.path.exists("logs/bot.log"):
        size_bytes = os.path.getsize("logs/bot.log")
        log_size = f"{size_bytes / 1024:.2f} KB"

    text = (
        "⚙️ **Bot tizim holati:**\n\n"
        f"⏰ **Vaqt:** {now}\n"
        f"🖥 **OS:** {os_info}\n"
        f"🐍 **Python:** {platform.python_version()}\n"
        f"📁 **Log hajmi:** {log_size}\n"
        f"✅ **Holat:** Ishlamoqda (Online)"
    )
    await message.answer(text, parse_mode="Markdown")


@router.message(F.text == "📋 Loglarni yuklash")
async def admin_download_logs(message: types.Message, settings: Settings) -> None:
    if not is_super_admin(settings, message.from_user.id):
        return
        
    logger.info(f"{admin_name(message.from_user.id)} bot jurnallarini (log) yuklab oldi.")

    log_path = "logs/bot.log"
    if os.path.exists(log_path):
        file = FSInputFile(log_path, filename=f"bot_log_{datetime.datetime.now().strftime('%d_%m_%H%M')}.log")
        await message.answer_document(file, caption="📄 Botning oxirgi jurnallari (logs)")
    else:
        await message.answer("❌ Log fayli topilmadi.")

@router.message(F.text == "👥 Foydalanuvchilar")
async def admin_users_list_handler(message: types.Message, settings: Settings, db: Database) -> None:
    role = get_admin_role(settings, message.from_user.id)
    if role is None:
        return
    logger.info(f"{admin_name(message.from_user.id)} 'Foydalanuvchilar' ro'yxatini ochdi.")
    await _send_users_page(message.chat.id, message.bot, db, role, 0)

@router.callback_query(F.data.startswith("users_list:"))
async def admin_users_list_callback(call: types.CallbackQuery, settings: Settings, db: Database) -> None:
    role = get_admin_role(settings, call.from_user.id)
    if role is None:
        await call.answer("Bunga ruxsatingiz yo'q!", show_alert=True)
        return
        
    offset = int(call.data.split(":")[1])
    try:
        await _send_users_page(call.message.chat.id, call.bot, db, role, offset, call.message.message_id) # type: ignore
    except Exception as e:
        logger.error(f"Error in users_list pagination: {e}")
    await call.answer()

async def _send_users_page(chat_id: int, bot: types.Bot, db: Database, role: str, offset: int, message_id: int = None):
    limit = 20
    users, total_count, phone_count = await db.get_users_list(role, offset, limit)
    
    text = f"👥 Foydalanuvchilar ro'yxati (Jami: {total_count} | ✅ {phone_count}):\n\n"
    for i, u in enumerate(users, start=offset + 1):
        has_phone = bool(u.get("phone"))
        icon = "✅" if has_phone else "⚠️"
        
        name_display = u['full_name']
        if u.get('username'):
            name_display += f" (@{u['username']})"
            
        phone_display = u['phone'] if has_phone else "[Raqamsiz]"
        
        try:
            dt = u['created_at']
            date_str = dt.strftime("%d.%m.%y %H:%M")
        except:
            date_str = str(u['created_at'])[:16]

        text += f"{i}. {icon} {name_display} ({u['user_id']}) — {phone_display} — [{date_str}]\n"
        
    if not users:
        text += "Foydalanuvchilar topilmadi.\n"
        
    from app.keyboards import users_list_pager_kb
    kb = users_list_pager_kb(offset, limit, total_count)
    
    if message_id:
        await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=kb)
    else:
        await bot.send_message(chat_id, text, reply_markup=kb)

# ─── Backup & Restore ──────────────────────────────────────────────────────

@router.message(F.text == "💾 Zahira nusxa (Backup)")
async def admin_backup_start(message: types.Message, settings: Settings, db: Database) -> None:
    if not is_super_admin(settings, message.from_user.id):
        return
    
    wait_msg = await message.answer("💾 Ma'lumotlar bazasi zahiralanmoqda, iltimos kuting...")
    
    try:
        backup_data = await db.get_full_backup()
        json_str = json.dumps(backup_data, indent=2, ensure_ascii=False)
        
        bio = io.BytesIO(json_str.encode('utf-8'))
        bio.seek(0)
        
        filename = f"backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file = types.BufferedInputFile(bio.getvalue(), filename=filename)
        
        await message.answer_document(
            file, 
            caption=f"✅ Zahira nusxa tayyor!\n\n👥 Foydalanuvchilar: {len(backup_data['users'])}\n📝 Murojaatlar: {len(backup_data['murojaatlar'])}"
        )
        logger.info(f"{admin_name(message.from_user.id)} ma'lumotlar bazasini zahiraladi.")
    except Exception as e:
        logger.error(f"Backup error: {e}")
        await message.answer("⚠️ Zahira nusxa olishda xatolik yuz berdi.")
    finally:
        await wait_msg.delete()

@router.message(F.text == "📥 Ma'lumotni tiklash (Restore)")
async def admin_restore_start(message: types.Message, state: FSMContext, settings: Settings) -> None:
    if not is_super_admin(settings, message.from_user.id):
        return
        
    await message.answer(
        "📥 Ma'lumotlarni tiklash uchun avval yuklab olingan `.json` zahira faylini yuboring.\n\n"
        "⚠️ *DIQQAT:* Bu amal mavjud ma'lumotlarni yangilashi yoki to'ldirishi mumkin!",
        parse_mode="Markdown"
    )
    await state.set_state(AdminBackupStates.waiting_restore_file)

@router.message(AdminBackupStates.waiting_restore_file, F.document)
async def admin_restore_process(message: types.Message, state: FSMContext, db: Database, bot: types.Bot, settings: Settings) -> None:
    if not is_super_admin(settings, message.from_user.id) or not message.document:
        return

    if not message.document.file_name.endswith(".json"):
        await message.answer("❌ Iltimos, faqat `.json` formatidagi zahira faylini yuboring.")
        return

    wait_msg = await message.answer("⏳ Fayl yuklanmoqda va qayta ishlanmoqda...")
    
    try:
        file = await bot.get_file(message.document.file_id)
        file_path = file.file_path
        
        # Faylni xotiraga yuklash
        content = await bot.download_file(file_path)
        data = json.loads(content.read().decode('utf-8'))
        
        # Bazaga yuklash
        result = await db.restore_full_backup(data)
        
        await message.answer(
            f"✅ Ma'lumotlar muvaffaqiyatli tiklandi!\n\n"
            f"👥 Foydalanuvchilar yangilandi: {result['users']}\n"
            f"📝 Murojaatlar yangilandi: {result['murojaatlar']}",
            reply_markup=admin_menu()
        )
        logger.info(f"{admin_name(message.from_user.id)} ma'lumotlarni zahira faylidan tikladi.")
    except Exception as e:
        logger.error(f"Restore error: {e}")
        await message.answer("⚠️ Ma'lumotlarni tiklashda xatolik yuz berdi. Fayl formati noto'g'ri bo'lishi mumkin.")
    finally:
        await state.clear()
        await wait_msg.delete()
