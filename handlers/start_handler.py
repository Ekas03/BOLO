import uuid
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from main import router
from database.database import SessionLocal
from database.crud import get_user_by_telegram_id, check_invitation_exists_by_uuid, handle_invitation_code

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
                await message.answer(f"Привет, {get_user_by_telegram_id(db, message.from_user.id)}!")

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
                await message.answer("Возникла ошибка. Пожалуйста, попробуйте еще раз.")
        else:
            await message.answer("Возникла ошибка. Пожалуйста, попробуйте еще раз.")