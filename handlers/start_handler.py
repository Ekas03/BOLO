from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from main import router
from database.database import SessionLocal
from database.crud import get_user_by_telegram_id

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