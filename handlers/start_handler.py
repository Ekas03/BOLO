import re
from aiogram import types
import uuid
from uuid import uuid4
from sqlalchemy.orm import Session
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message,InlineKeyboardMarkup, InlineKeyboardButton
from main import router
from database.database import SessionLocal
from database.crud import (get_user_by_telegram_id, check_invitation_exists_by_uuid, handle_invitation_code,
                           check_user_has_couple, check_invitation_exists, get_invitation_uuid, get_couple_days,
                           create_user, delete_invitation, create_invitation)

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
                await message.answer("Привет! Как тебя зовут?")
                await state.set_state(Registration.waiting_for_name)
            else:
                await process_user_status(db, message)
        else:
            await process_user_status(db, message)


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


# Создание личного приглашения
@router.callback_query(lambda c: c.data == "create_inv")
async def callback_create_invitation(callback_query: types.CallbackQuery):
    uuid = str(uuid4())
    with SessionLocal() as db:
        create_invitation(db, uuid, callback_query.from_user.id)
    revoke_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отозвать", callback_data=f"revoke_{uuid}")]
    ])
    await callback_query.message.edit_text("Приглашение создано! Ты можешь отозвать его в любой момент. Отправь этот код своему партнёру:",
                                           reply_markup=revoke_button)
    await callback_query.message.answer("Привет! Добавь меня в BOLO по коду с помощью команды:")
    await callback_query.message.answer(f"/add {uuid}")


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


# Функция для отозвания приглашения
@router.callback_query(lambda callback_query: callback_query.data.startswith("revoke_"))
async def revoke_invitation(callback_query: types.CallbackQuery):
    uuid = callback_query.data.split("_")[1]
    with SessionLocal() as db:
        delete_invitation(db, callback_query.from_user.id)
    await callback_query.answer()
    await callback_query.message.chat.delete_message(message_id=callback_query.message.message_id)
    await start(message=callback_query.message)

# Проверка имени, указание пола
@router.message(Registration.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    name = message.text
    if not re.match("^[a-zA-Zа-яА-Я]+$", name):
        await message.answer("Имя не должно содержать специальные символы или цифры. Пожалуйста, введите имя еще раз.")
        return
    await state.update_data(name=name)
    gender_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Женщина 👸", callback_data="0"),
            InlineKeyboardButton(text="Мужчина 🤴", callback_data="1")
        ]
    ])
    await message.answer(f"Привет, {name}! Выбери свой пол:", reply_markup=gender_keyboard)
    await state.set_state(Registration.waiting_for_gender)

# Установка пола
@router.callback_query(Registration.waiting_for_gender)
async def process_gender_callback(callback_query: types.CallbackQuery, state: FSMContext):
    gender = callback_query.data
    user_data = await state.get_data()
    name = user_data['name']
    if gender == "1" or gender == "0":
        await state.update_data(gender=gender)
        await callback_query.answer()
        await callback_query.message.chat.delete_message(message_id=callback_query.message.message_id)
        with SessionLocal() as db:
            create_user(db, callback_query.from_user.id, name, int(callback_query.data), None)
        await start(message=callback_query.message)


# Возврат обратно в меню
@router.callback_query(lambda c: c.data == "back_start")
async def callback_back_start(callback_query: types.CallbackQuery):
    await callback_query.message.chat.delete_message(message_id=callback_query.message.message_id)
    with SessionLocal() as db:
        await couple_menu(db, message=callback_query.message, userId=callback_query.from_user.id)
