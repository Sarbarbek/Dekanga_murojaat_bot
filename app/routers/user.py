from __future__ import annotations

from aiogram import F, Router, types, html
from aiogram.fsm.context import FSMContext

from app.config import Settings
from app.db import Database
from app.keyboards import (
    admin_answer_kb,
    department_kb,
    back_kb,
    media_extra_kb,
    contact_kb,
    admin_menu,
    dekan_menu,
)
from app.states import MurojaatStates
from app.media_security import MediaSecurityChecker
from app.utils import is_admin, is_super_admin
from aiogram.filters import StateFilter
import logging

logger = logging.getLogger(__name__)

router = Router(name=__name__)

DEPARTMENTS = {
    "🌙 Kechki dekanat": "kech",
    "☀️ Kunduzgi dekanat": "kun",
    "🎓 Magistratura bo'limi": "mag",
    "🏫 Sirtqi dekanat": "sirt",
    "🩺 Tibbiyot taʼlim yoʻnalishi": "med",
}

DEPT_EXAMPLES = {
    "kun": "ISE_N-23UA",
    "kech": "RUSE_N-25UA",
    "mag": "MPFS_N-23UA",
    "sirt": "PREP_N-24UA",
    "med": "MED_N-25UA",
}


# ─── 1. Dekanat tanlash ────────────────────────────────────────────────────────


@router.message(MurojaatStates.department)
async def appeal_department(message: types.Message, state: FSMContext, bot: types.Bot) -> None:
    if message.text == "⬅️ Ortga":
        # Eski holatda Ortga tugmasi bor edi, hozir yo'q. Shunday bo'lsa ham qolishi zarar qilmaydi.
        await state.clear()
        await message.answer("Bekor qilindi. Murojaat qilmoqchi bo'lgan bo'limingizni tanlang:", reply_markup=department_kb())
        await state.set_state(MurojaatStates.department)
        return

    if message.text not in DEPARTMENTS:
        await message.answer(
            "Murojaat qilmoqchi bo'lgan bo'limingizni tanlang:",
            reply_markup=department_kb(),
        )
        return

    # department_key ni saqlab qo'yamiz
    dep_key = DEPARTMENTS[message.text]
    
    # Obunani tekshirish
    channels = {
        "kun": {"id": "@kunduzgi_kiut_nm", "url": "https://t.me/kunduzgi_kiut_nm"},
        "kech": {"id": "@eveningkiut", "url": "https://t.me/eveningkiut"},
        "mag": {"id": "@kiutmasters", "url": "https://t.me/kiutmasters"},
        "sirt": {"id": "@kiut_np", "url": "https://t.me/kiut_np"},
        "med": {"id": "@kiut_nm_medical", "url": "https://t.me/kiut_nm_medical"},
    }
    
    channel_info = channels.get(dep_key)
    if channel_info:
        try:
            member = await bot.get_chat_member(chat_id=channel_info["id"], user_id=message.from_user.id)
            if member.status in ["left", "kicked"]:
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                ikb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=channel_info["url"])],
                    [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"check_sub:{dep_key}")]
                ])
                await message.answer("Ushbu bo'limga murojaat qilishdan oldin, tegishli kanalga obuna bo'lishingiz majburiy. Iltimos, obuna bo'ling va tasdiqlash tugmasini bosing:", reply_markup=ikb)
                return
        except Exception as e:
            logger.warning(f"Obunani tekshirishda xatolik: {e}")
            pass

    await state.update_data(department=message.text, department_key=dep_key)
    logger.info(f"Foydalanuvchi {message.from_user.full_name} ({message.from_user.id}) '{message.text}' ni tanladi.")
    
    example = "ISE_N-23UA"
    if dep_key == "kech": example = "RUSE_N-25UA"
    elif dep_key == "mag": example = "MPFS_N-23UA"
    elif dep_key == "sirt": example = "PREP_N-24UA"
    elif dep_key == "med": example = "MED_N-25UA"

    await message.answer(
        f"✅ <b>{message.text}</b> tanlandi.\n\n"
        f"Guruhingizni kiriting:\n"
        f"(masalan: {example})",
        parse_mode="HTML",
        reply_markup=back_kb(),
    )
    await state.set_state(MurojaatStates.group_name)


@router.callback_query(F.data.startswith("check_sub:"))
async def check_subscription_callback(call: types.CallbackQuery, state: FSMContext, bot: types.Bot) -> None:
    dep_key = call.data.split(":")[1]
    
    channels = {
        "kun": {"id": "@kunduzgi_kiut_nm", "url": "https://t.me/kunduzgi_kiut_nm"},
        "kech": {"id": "@eveningkiut", "url": "https://t.me/eveningkiut"},
        "mag": {"id": "@kiutmasters", "url": "https://t.me/kiutmasters"},
        "sirt": {"id": "@kiut_np", "url": "https://t.me/kiut_np"},
        "med": {"id": "@kiut_nm_medical", "url": "https://t.me/kiut_nm_medical"},
    }
    
    channel_info = channels.get(dep_key)
    if not channel_info:
        await call.answer("Xatolik yuz berdi.", show_alert=True)
        return
        
    try:
        member = await bot.get_chat_member(chat_id=channel_info["id"], user_id=call.from_user.id)
        if member.status in ["left", "kicked"]:
            await call.answer("Siz hali kanalga a'zo bo'lmadingiz! Iltimos, avval obuna bo'ling.", show_alert=True)
            return
    except Exception as e:
        logger.warning(f"Obunani tekshirishda xatolik: {e}")
        pass
        
    try:
        if call.message:
            await call.message.delete()
    except Exception:
        pass
            
    dep_text = None
    for k, v in DEPARTMENTS.items():
        if v == dep_key:
            dep_text = k
            break
            
    await state.update_data(department=dep_text, department_key=dep_key)
    logger.info(f"Foydalanuvchi {call.from_user.full_name} ({call.from_user.id}) '{dep_text}' bo'yicha obunani tasdiqladi.")
    
    example = "ISE_N-23UA"
    if dep_key == "kech": example = "RUSE_N-25UA"
    elif dep_key == "mag": example = "MPFS_N-23UA"
    elif dep_key == "sirt": example = "PREP_N-24UA"
    elif dep_key == "med": example = "MED_N-25UA"

    if call.message:
        await call.message.answer(
            f"✅ <b>{dep_text}</b> tanlandi.\n\n"
            f"Guruhingizni kiriting:\n"
            f"(masalan: {example})",
            parse_mode="HTML",
            reply_markup=back_kb(),
        )
    await state.set_state(MurojaatStates.group_name)
    await call.answer()


# ─── 3a. Ochiq suhbat — Ism ───────────────────────────────────────────────────

@router.message(MurojaatStates.group_name)
async def appeal_group_name(message: types.Message, state: FSMContext) -> None:
    if message.text == "⬅️ Ortga":
        await message.answer("Qaysi bo'limga murojaat qilmoqchisiz?", reply_markup=department_kb())
        await state.set_state(MurojaatStates.department)
        return

    group_input = message.text.strip().upper()
    if len(group_input) > 12:
        await message.answer("⚠️ Guruh nomi juda uzun! Iltimos, 12 belgidan oshirmasdan to'g'ri kiriting (masalan: ISE_N-23UA):")
        return

    await state.update_data(group_name=group_input)
    logger.info(f"Foydalanuvchi {message.from_user.full_name} ({message.from_user.id}) guruhini kiritdi: {group_input}")
    await message.answer(
        "Ism, familiyangizni to'liq kiriting (masalan: Akbaraliyev Sarbarbek):",
        reply_markup=back_kb(),
    )
    await state.set_state(MurojaatStates.full_name)


@router.message(MurojaatStates.full_name)
async def appeal_full_name(message: types.Message, state: FSMContext) -> None:
    if message.text == "⬅️ Ortga":
        data = await state.get_data()
        dep_key = data.get("department_key", "kun")
        example = DEPT_EXAMPLES.get(dep_key, "masalan: ISE_N-23UA")
        await message.answer(f"Guruhingizni kiriting:\n({example})", reply_markup=back_kb())
        await state.set_state(MurojaatStates.group_name)
        return

    await state.update_data(full_name=message.text.strip())
    logger.info(f"Foydalanuvchi ({message.from_user.id}) ism-sharifini kiritdi: {message.text.strip()}")
    await message.answer(
        "Rasmiy murojaat qilish uchun pasport seriya va raqamingizni yuboring (masalan: AA1234567):",
        reply_markup=back_kb(),
    )
    await state.set_state(MurojaatStates.passport)


@router.message(MurojaatStates.passport)
async def appeal_passport(message: types.Message, state: FSMContext) -> None:
    if message.text == "⬅️ Ortga":
        await message.answer("Ism, familiyangizni to'liq kiriting:", reply_markup=back_kb())
        await state.set_state(MurojaatStates.full_name)
        return

    import re
    text = (message.text or "").strip()
    # Remove all whitespace and convert to upper
    text = re.sub(r'\s+', '', text).upper()
    if not re.match(r'^[A-Z]{2}\d{7}$', text):
        await message.answer("Iltimos, pasport seriya va raqamini to'g'ri kiriting (masalan: AA1234567):")
        return

    await state.update_data(passport=text)
    logger.info(f"Foydalanuvchi ({message.from_user.id}) pasport ma'lumotlarini kiritdi: {text}")
    await message.answer(
        "Murojatingiz rasmiy va Siz bilan bog'lanishimiz uchun telefon raqamingizni yuboring\n(masalan: 91 123 45 67):",
        reply_markup=contact_kb(),
    )
    await state.set_state(MurojaatStates.phone)


@router.message(MurojaatStates.phone)
async def appeal_phone(message: types.Message, state: FSMContext) -> None:
    if message.text == "⬅️ Ortga":
        await message.answer("Pasport seriya va raqamingizni yuboring:", reply_markup=back_kb())
        await state.set_state(MurojaatStates.passport)
        return

    phone = ""
    if message.contact:
        phone = message.contact.phone_number
        if not phone.startswith('+'):
            phone = '+' + phone
    else:
        text_phone = (message.text or "").strip()
        import re
        text_phone = re.sub(r'\D', '', text_phone)
        if len(text_phone) == 9:
            phone = f"+998{text_phone}"
        elif len(text_phone) == 12 and text_phone.startswith("998"):
            phone = f"+{text_phone}"
        else:
            await message.answer("Iltimos, telefon raqamini 9 ta raqam shaklida kiriting\n(masalan: 91 123 45 67) yoki pastdagi tugmadan foydalaning:")
            return

    if not phone:
        await message.answer("Iltimos, telefon raqamingizni yuboring.")
        return

    await state.update_data(phone=phone)
    logger.info(f"Foydalanuvchi ({message.from_user.id}) telefon raqamini kiritdi: {phone}")
    await message.answer(
        "Murojaatingizni yozib yuboring (yoki kerakli fayl va media yuboring):",
        reply_markup=back_kb(),
    )
    await state.set_state(MurojaatStates.body)


# ─── 4. Murojaat matni ────────────────────────────────────────────────────────

@router.message(MurojaatStates.body)
async def appeal_body(message: types.Message, state: FSMContext, db: Database, bot: types.Bot, settings: Settings) -> None:
    if message.text == "⬅️ Ortga":
        await message.answer("Siz bilan bog'lanishimiz uchun telefon raqamingizni yuboring:", reply_markup=contact_kb())
        await state.set_state(MurojaatStates.phone)
        return

    # Faqat matnli xabarda link borligini tekshirish
    if message.text:
        has_link = any(entity.type in ["url", "text_link"] for entity in (message.entities or []))
        if has_link:
            await message.answer("⚠️ Murojaat matnida linklardan foydalanish taqiqlangan. Iltimos, faqat matn yuboring.")
            return

    # ── Media xavfsizligi tekshiruvi ─────────────────────────────────────
    checker = MediaSecurityChecker()
    file_id = None
    file_type = "text"

    if message.photo:
        photo = message.photo[-1]

        # Rasm o'lchamini tekshirish
        result = checker.check_photo(photo.file_size)
        if not result.is_safe:
            logger.warning(f"[XAVFSIZLIK] Foydalanuvchi {message.from_user.id} xavfli rasm yubordi: {result.reason}")
            await message.answer(f"⚠️ {result.reason}\n\nIltimos, boshqa rasm yuboring.")
            return

        # Rasm izohidagi link va xavfli kontentni tekshirish
        caption_result = checker.check_caption(message.caption, message.caption_entities)
        if not caption_result.is_safe:
            logger.warning(f"[XAVFSIZLIK] Foydalanuvchi {message.from_user.id} xavfli izoh yubordi: {caption_result.reason}")
            await message.answer(f"⚠️ {caption_result.reason}")
            return

        file_id = photo.file_id
        file_type = "photo"

    elif message.video:
        video = message.video

        # Video o'lchami va uzunligini tekshirish
        result = checker.check_video(video.file_size, video.duration)
        if not result.is_safe:
            logger.warning(f"[XAVFSIZLIK] Foydalanuvchi {message.from_user.id} xavfli video yubordi: {result.reason}")
            await message.answer(f"⚠️ {result.reason}\n\nIltimos, boshqa video yuboring.")
            return

        # Video izohini tekshirish
        caption_result = checker.check_caption(message.caption, message.caption_entities)
        if not caption_result.is_safe:
            logger.warning(f"[XAVFSIZLIK] Foydalanuvchi {message.from_user.id} xavfli izoh yubordi: {caption_result.reason}")
            await message.answer(f"⚠️ {caption_result.reason}")
            return

        file_id = video.file_id
        file_type = "video"

    elif message.document:
        doc = message.document

        # Hujjat kengaytmasi, o'lchami va MIME turini tekshirish
        result = checker.check_document(doc.file_name, doc.file_size, doc.mime_type)
        if not result.is_safe:
            logger.warning(f"[XAVFSIZLIK] Foydalanuvchi {message.from_user.id} xavfli hujjat yubordi: {doc.file_name} — {result.reason}")
            await message.answer(f"⚠️ {result.reason}")
            return

        # Hujjat izohini tekshirish
        caption_result = checker.check_caption(message.caption, message.caption_entities)
        if not caption_result.is_safe:
            logger.warning(f"[XAVFSIZLIK] Foydalanuvchi {message.from_user.id} xavfli izoh yubordi: {caption_result.reason}")
            await message.answer(f"⚠️ {caption_result.reason}")
            return

        file_id = doc.file_id
        file_type = "document"

    elif message.audio:
        audio = message.audio

        # Audio o'lchamini tekshirish
        result = checker.check_audio(audio.file_size)
        if not result.is_safe:
            logger.warning(f"[XAVFSIZLIK] Foydalanuvchi {message.from_user.id} xavfli audio yubordi: {result.reason}")
            await message.answer(f"⚠️ {result.reason}")
            return

        file_id = audio.file_id
        file_type = "audio"

    elif message.voice:
        voice = message.voice

        # Ovozli xabar o'lchamini tekshirish
        result = checker.check_voice(voice.file_size)
        if not result.is_safe:
            logger.warning(f"[XAVFSIZLIK] Foydalanuvchi {message.from_user.id} xavfli voice yubordi: {result.reason}")
            await message.answer(f"⚠️ {result.reason}")
            return

        file_id = voice.file_id
        file_type = "voice"

    elif any([message.video_note, message.sticker, message.animation]):
        await message.answer("⚠️ Kechirasiz, murojaat uchun ushbu turdagi fayllar qabul qilinmaydi.")
        return

    if file_id:
        await state.update_data(file_id=file_id, file_type=file_type, temp_body=message.caption or "")
        await message.answer(
            "Media qabul qilindi. Qo'shimcha izoh yozasizmi yoki shundayligicha yuborasizmi?",
            reply_markup=media_extra_kb()
        )
        await state.set_state(MurojaatStates.confirm_media)
    else:
        if not message.text:
            await message.answer("Iltimos, murojaat matnini yozing yoki rasm yuboring.")
            return
        await state.update_data(body_text=message.text.strip())
        await _finish_appeal(message, state, db, bot, settings)


@router.message(MurojaatStates.confirm_media)
async def appeal_confirm_media(message: types.Message, state: FSMContext, db: Database, bot: types.Bot, settings: Settings) -> None:
    if message.text == "⬅️ Ortga":
        await message.answer("Murojaat matnini yozing yoki media yuboring:", reply_markup=back_kb())
        await state.set_state(MurojaatStates.body)
        return

    if message.text == "🔄 Qayta boshlash":
        await state.clear()
        await message.answer("Qaysi bo'limga murojaat qilmoqchisiz?", reply_markup=department_kb())
        await state.set_state(MurojaatStates.department)
        return

    data = await state.get_data()
    
    if message.text == "✅ Shart emas, yuborish":
        temp_body = data.get("temp_body", "")
        body_text = temp_body or f"{data.get('file_type', 'fayl').capitalize()} yuborildi."
        await state.update_data(body_text=body_text)
        await _finish_appeal(message, state, db, bot, settings)
    elif message.text == "✍️ Izoh yozish":
        await message.answer("Media uchun izohingizni kiriting:", reply_markup=back_kb())
        await state.set_state(MurojaatStates.media_comment)
    else:
        await message.answer("Iltimos, tugmalardan birini tanlang:", reply_markup=media_extra_kb())


@router.message(MurojaatStates.media_comment)
async def appeal_media_comment(message: types.Message, state: FSMContext, db: Database, bot: types.Bot, settings: Settings) -> None:
    if message.text == "⬅️ Ortga":
        await message.answer("Media qabul qilindi. Qo'shimcha izoh yozasizmi?", reply_markup=media_extra_kb())
        await state.set_state(MurojaatStates.confirm_media)
        return

    if message.text == "🔄 Qayta boshlash":
        await state.clear()
        await message.answer("Qaysi bo'limga murojaat qilmoqchisiz?", reply_markup=department_kb())
        await state.set_state(MurojaatStates.department)
        return

    if not message.text:
        await message.answer("Iltimos, izoh matnini yozing.")
        return

    data = await state.get_data()
    temp_body = data.get("temp_body", "")
    extra_comment = message.text.strip()
    
    # Caption va yangi izohni birlashtirish
    combined_body = f"{temp_body}\n\nIzoh: {extra_comment}" if temp_body else extra_comment
    
    await state.update_data(body_text=combined_body)
    await _finish_appeal(message, state, db, bot, settings)


async def _finish_appeal(message: types.Message, state: FSMContext, db: Database, bot: types.Bot, settings: Settings) -> None:
    data = await state.get_data()

    full_name = data.get("full_name", "Noma'lum").upper()
    passport = data.get("passport", "Noma'lum").upper()
    phone = data.get("phone", "Noma'lum").upper()
    group_name = data.get("group_name", "Noma'lum").upper()
    dep_key = data.get("department_key", "kun")
    dep_name = list(DEPARTMENTS.keys())[list(DEPARTMENTS.values()).index(dep_key)] if dep_key in DEPARTMENTS.values() else dep_key
    dep_name = dep_name.upper()

    file_id = data.get("file_id")
    file_type = data.get("file_type", "text")
    body_text = data.get("body_text", "").upper()

    # Save to database
    appeal_id = await db.create_murojaat(
        user_id=message.from_user.id,
        full_name=full_name,
        passport=passport,
        phone=phone,
        group_name=group_name,
        department_key=dep_key,
        body_text=body_text if body_text else None,
        file_id=file_id,
        file_type=file_type,
    )
    logger.info(f"Foydalanuvchi {full_name} ({message.from_user.id}) yangi murojaat qoldirdi. (Murojaat ID: {appeal_id}, Bo'lim: {dep_name})")

    admin_text = (
        f"📩 <b>YANGI MUROJAAT</b>\n\n"
        f"👤 <b>F. I. SH:</b> {html.quote(full_name)}\n"
        f"🆔 <b>PASPORT:</b> {html.quote(passport)}\n"
        f"📞 <b>TEL:</b> {html.quote(phone)}\n"
        f"👥 <b>GURUH:</b> {html.quote(group_name)}\n"
        f"🏫 <b>BO'LIM:</b> {html.quote(dep_name)}\n\n"
        f"📝 <b>MATN:</b> {html.quote(body_text) if body_text else '(MEDIA)'}"
    )

    # Adminlarni aniqlash
    target_dekan_ids = []
    if dep_key == "kun": target_dekan_ids = settings.kun_dekan_ids
    elif dep_key == "kech": target_dekan_ids = settings.kech_dekan_ids
    elif dep_key == "mag": target_dekan_ids = settings.mag_dekan_ids
    elif dep_key == "sirt": target_dekan_ids = settings.sirt_dekan_ids
    elif dep_key == "med": target_dekan_ids = settings.med_dekan_ids

    super_admin_ids = [aid for aid in settings.admin_ids if aid not in (settings.kun_dekan_ids + settings.kech_dekan_ids + settings.mag_dekan_ids + settings.sirt_dekan_ids + settings.med_dekan_ids)]
    admins_to_notify = list(set(super_admin_ids + target_dekan_ids))

    for admin_id in admins_to_notify:
        try:
            if file_id:
                if file_type == "photo":
                    await bot.send_photo(admin_id, file_id, caption=admin_text, parse_mode="HTML", reply_markup=admin_answer_kb(appeal_id))
                elif file_type == "video":
                    await bot.send_video(admin_id, file_id, caption=admin_text, parse_mode="HTML", reply_markup=admin_answer_kb(appeal_id))
                elif file_type == "document":
                    await bot.send_document(admin_id, file_id, caption=admin_text, parse_mode="HTML", reply_markup=admin_answer_kb(appeal_id))
                elif file_type == "audio":
                    await bot.send_audio(admin_id, file_id, caption=admin_text, parse_mode="HTML", reply_markup=admin_answer_kb(appeal_id))
                elif file_type == "voice":
                    await bot.send_voice(admin_id, file_id, caption=admin_text, parse_mode="HTML", reply_markup=admin_answer_kb(appeal_id))
            else:
                await bot.send_message(admin_id, admin_text, parse_mode="HTML", reply_markup=admin_answer_kb(appeal_id))
        except Exception:
            pass

    await message.answer(
        "✅ Murojaatingiz qabul qilindi. Sizning murojaatingiz 3 ish kunida javobsiz qolmaydi.\n"
        "Javob shu bot orqali yuboriladi.",
        reply_markup=department_kb(),
    )
    await state.clear()
    await state.set_state(MurojaatStates.department)

@router.message(StateFilter("*"))
async def catch_all_handler(message: types.Message, state: FSMContext, settings: Settings) -> None:
    """Noma'lum xabarlarni tutib qoluvchi handler."""
    if is_admin(settings, message.from_user.id):
        menu = admin_menu() if is_super_admin(settings, message.from_user.id) else dekan_menu()
        await message.answer("Noma'lum buyruq. Iltimos, menyudan foydalaning:", reply_markup=menu)
    else:
        # Oddiy foydalanuvchi bo'lsa, bo'lim tanlashga yo'naltiramiz
        await state.clear()
        await state.set_state(MurojaatStates.department)
        await message.answer(
            "Tushunarsiz xabar. Iltimos, murojaat qilish uchun quyidagi bo'limlardan birini tanlang:",
            reply_markup=department_kb()
        )
