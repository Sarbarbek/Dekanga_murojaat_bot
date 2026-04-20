from aiogram.fsm.state import State, StatesGroup


class MurojaatStates(StatesGroup):
    department = State()    # Dekanat tanlash
    group_name = State()    # Guruh kiritish
    full_name = State()     # F.I.SH
    passport = State()      # Pasport seriya va raqami
    phone = State()         # Telefon raqami
    body = State()          # Murojaat matni yoki media
    confirm_media = State() # Mediani tasdiqlash yoki izoh yozish
    media_comment = State() # Media uchun izoh yozish holati


class AdminAnswerStates(StatesGroup):
    waiting_answer = State()


class AdminSearchStates(StatesGroup):
    waiting_query = State()


class AdminBroadcastStates(StatesGroup):
    waiting_message = State()
    confirm_broadcast = State()

class AdminBackupStates(StatesGroup):
    waiting_restore_file = State()
