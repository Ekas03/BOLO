import uuid
from sqlalchemy.orm import Session
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message,InlineKeyboardMarkup, InlineKeyboardButton
from main import router
from database.database import SessionLocal
from database.crud import (get_user_by_telegram_id, check_invitation_exists_by_uuid, handle_invitation_code,
                           check_user_has_couple, check_invitation_exists, get_invitation_uuid, get_couple_days)

# Класс регистрации
class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_gender = State()


# Обработка команды /start
@router.message(CommandStart())
async def start(message: Message, state: FSMContext = None):
    with SessionLocal() as db:
        if state != None:
            if get_user_by_telegram_id(db, message.from_user.id) is None:
                await message.answer("👋 Привет! Как тебя зовут?")
                await state.set_state(Registration.waiting_for_name)
            else:
                await message.answer(f"Привет, {get_user_by_telegram_id(db, message.from_user.id)}!")


# Функция для проверки состояния пользователя
async def process_user_status(db: Session, message: Message):
    if check_user_has_couple(db, message.from_user.id):
        await couple_menu(db, message)
    else:
        if check_invitation_exists(db, message.from_user.id):
            uuid = get_invitation_uuid(db, message.from_user.id)
            revoke_button = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌Отозвать приглашение", callback_data=f"revoke_{uuid}")]
            ])
            await message.answer("Привет! У Вас уже есть приглашение. Если хотите, можете отозвать его.", reply_markup=revoke_button)
        else:
            invitation_button = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Создать", callback_data="create_inv")]
            ])
            await message.answer("Создайте приглашение, чтобы добавить своего партнёра",
                                 reply_markup=invitation_button)


# Основное меню функций бота
async def couple_menu(db: Session, message: Message = None, userId = None):
    if userId != None:
        user = get_user_by_telegram_id(db, userId)
    else:
        user = get_user_by_telegram_id(db, message.from_user.id)
    if user and user.CoupleId:
        couple_days = get_couple_days(db, user.CoupleId)
    else:
        couple_days = "unknown"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📅 Календарь', callback_data='calendar')],
        [InlineKeyboardButton(text='✅ Челленджи', callback_data='challenges')],
        [InlineKeyboardButton(text='💞 Задания', callback_data='tasks')],
        [InlineKeyboardButton(text='Книга любви')],
        [InlineKeyboardButton(text='🗺 Карта отношений')]
    ])

    await message.answer(f"💕 МЫ ВМЕСТЕ УЖЕ {couple_days} {plural_days(couple_days)}!!! 💕", reply_markup=keyboard)


# Построение правильного окончания в зависимости от числа
def plural_days(value: int):
    days = ['день', 'дня', 'дней']

    if value % 10 == 1 and value % 100 != 11:
        return days[0]
    elif 2 <= value % 10 <= 4 and (value % 100 < 10 or value % 100 >= 20):
        return days[1]
    return days[2]


# Обработка кода приглашения
@router.message(Command("add"))
async def process_invitation_code(message: Message):
    _, invitation_code = message.text.split(maxsplit=1)
    try:
        uuid.UUID(invitation_code)
    except ValueError:
        await message.answer("Введите код приглашения через пробел.\nПример: /add 12345678")
        return
    with SessionLocal() as db:
        if check_invitation_exists_by_uuid(db, invitation_code):
            new_couple = handle_invitation_code(db, invitation_code, message.from_user.id)
            if new_couple:
                await message.answer("Успешное подключение! Теперь вы можете погрузиться в мир BOLO!")
                await start(message=message)
            else:
                await message.answer("⛔Возникла ошибка. Пожалуйста, попробуйте еще раз.")
        else:
            await message.answer("⛔Возникла ошибка. Пожалуйста, попробуйте еще раз.")