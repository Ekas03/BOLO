import uuid
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, Message
from main import router
import re
from sqlalchemy.orm import Session
from uuid import uuid4
from database import SessionLocal
from aiogram import types
from crud import get_user_by_telegram_id, create_user, check_user_has_couple, create_invitation, delete_invitation, \
    check_invitation_exists, get_invitation_uuid, handle_invitation_code, check_invitation_exists_by_uuid, \
    get_couple_days

class UserRegistration(StatesGroup):
    waiting_for_name = State()
    waiting_for_gender = State()

async def process_user_status(db: Session, message: Message):
    if check_user_has_couple(db, message.from_user.id):
        await couple_menu(db, message)
    else:
        if check_invitation_exists(db, message.from_user.id):
            uuid = get_invitation_uuid(db, message.from_user.id)
            revoke_button = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Отозвать", callback_data=f"revoke_{uuid}")]
            ])
            await message.answer("Привет! У вас уже есть приглашение. Вы можете отозвать его, если передумаете.", reply_markup=revoke_button)
        else:
            invitation_button = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⏩ Создать", callback_data="create_inv")]
            ])
            await message.answer("Создайте приглашение, чтобы добавить своего партнёра",
                                 reply_markup=invitation_button)

def plural_days(value: int):
    words = ['ДЕНЬ!', 'ДНЯ!', 'ДНЕЙ!']

    if all((value % 10 == 1, value % 100 != 11)):
        return words[0]
    elif all((2 <= value % 10 <= 4,
              any((value % 100 < 10, value % 100 >= 20)))):
        return words[1]
    return words[2]

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
        [InlineKeyboardButton(text='🗺 Карта отношений', web_app=WebAppInfo(url="https://bolobot.xyz/index.html"))],
        [InlineKeyboardButton(text='📅 Календарь', callback_data='calendar')],
        [InlineKeyboardButton(text='👩‍❤️‍👨 Свидания', callback_data='dates')],
        [InlineKeyboardButton(text='💪 Челленджи', callback_data='challenges')],
        [InlineKeyboardButton(text='🗄 Задания', callback_data='tasks')],
        [InlineKeyboardButton(text='🪩 Мероприятия', callback_data='events_go')],
        [InlineKeyboardButton(text='📖 Книга любви', callback_data='go_book')]
    ])

    await message.answer(f"💞 МЫ ВМЕСТЕ УЖЕ {couple_days} {plural_days(couple_days)} 💞", reply_markup=keyboard)


@router.message(Command("add"))
async def process_invitation_code(message: Message):
    _, invitation_code = message.text.split(maxsplit=1)
    try:
        uuid.UUID(invitation_code)
    except ValueError:
        await message.answer("Введите код приглашения через пробел. Пример: /add 12345678")
        return
    with SessionLocal() as db:
        if check_invitation_exists_by_uuid(db, invitation_code):
            new_couple = handle_invitation_code(db, invitation_code, message.from_user.id)
            if new_couple:
                await message.answer("Успешно! Теперь ты можешь погрузиться в мир BOLO.")
                await start(message=message)
            else:
                await message.answer("Возникла ошибка. Пожалуйста, попробуйте еще раз.")
        else:
            await message.answer("Возникла ошибка. Пожалуйста, попробуйте еще раз.")

@router.message(CommandStart())
async def start(message: Message, state: FSMContext = None):
    with SessionLocal() as db:
        if state != None:
            if get_user_by_telegram_id(db, message.from_user.id) is None:
                await message.answer("Привет! Как тебя зовут?")
                await state.set_state(UserRegistration.waiting_for_name)
            else:
                await process_user_status(db, message)
        else:
            await process_user_status(db, message)

@router.callback_query(lambda callback_query: callback_query.data.startswith("revoke_"))
async def revoke_invitation(callback_query: types.CallbackQuery):
    uuid = callback_query.data.split("_")[1]
    with SessionLocal() as db:
        delete_invitation(db, callback_query.from_user.id)
    await callback_query.answer()
    await callback_query.message.chat.delete_message(message_id=callback_query.message.message_id)
    await start(message=callback_query.message)

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
    await callback_query.message.answer(
        f"Привет! Добавь меня в BOLO по коду с помощью команды:")
    await callback_query.message.answer(
        f"/add {uuid}")

@router.message(UserRegistration.waiting_for_name)
async def process_name(message: Message, state: FSMContext):

    name = message.text
    if not re.match("^[a-zA-Zа-яА-Я]+$", name):
        await message.answer("Имя не должно содержать специальные символы или цифры. Пожалуйста, введите имя еще раз.")
        return
    await state.update_data(name=name)

    gender_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Мужчина", callback_data="1"),
            InlineKeyboardButton(text="Женщина", callback_data="0")
        ]
    ])
    await message.answer(f"Привет, {name}! Выбери свой пол:", reply_markup=gender_keyboard)
    await state.set_state(UserRegistration.waiting_for_gender)

@router.callback_query(UserRegistration.waiting_for_gender)
async def process_gender_callback(callback_query: types.CallbackQuery, state: FSMContext):
    gender = callback_query.data
    user_data = await state.get_data()
    name = user_data['name']
    callback_query.message.message_id
    if gender == "1" or gender == "0":
        await state.update_data(gender=gender)
        await callback_query.answer()
        await callback_query.message.chat.delete_message(message_id=callback_query.message.message_id)
        with SessionLocal() as db:
            create_user(db, callback_query.from_user.id, name, int(callback_query.data), None)
        await start(message=callback_query.message)

@router.callback_query(lambda c: c.data == "back_start")
async def callback_back_start(callback_query: types.CallbackQuery):
    await callback_query.message.chat.delete_message(message_id=callback_query.message.message_id)
    with SessionLocal() as db:
        await couple_menu(db, message=callback_query.message,userId=callback_query.from_user.id)
