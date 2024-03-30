from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from main import router
from database import SessionLocal
from aiogram import types
from crud import get_ongoing_events, get_couple_id_by_user_id, get_past_events
from models import Calendar

# Открытие календаря
@router.callback_query(lambda c: c.data == "calendar")
async def callback_calendar(callback_query: types.CallbackQuery):
    await callback_query.message.chat.delete_message(message_id=callback_query.message.message_id)
    with SessionLocal() as db:
        ongoing_events = get_ongoing_events(db, get_couple_id_by_user_id(db, callback_query.from_user.id))
        ongoing_events_str = "\n".join(f"{event}" for event in ongoing_events)

        menu = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🔙', callback_data='back_start')],
            [InlineKeyboardButton(text='📝 Показать прошедшие события', callback_data='show_past_events')]
        ])

        if not ongoing_events:
            await callback_query.message.answer(f"Предстоящих событий нет", reply_markup=menu)
        else:
            await callback_query.message.answer(f"Предстоящие события:\n{ongoing_events_str}", reply_markup=menu)


# Вывод прошедших событий
@router.callback_query(lambda c: c.data == "show_past_events")
async def callback_show_past_events(callback_query: types.CallbackQuery):
    await callback_query.message.chat.delete_message(message_id=callback_query.message.message_id)
    with SessionLocal() as db:
        past_events = get_past_events(db, get_couple_id_by_user_id(db, callback_query.from_user.id))
        past_events_str = "\n".join(f"{event}" for event in past_events)

        menu = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='🔙 Back', callback_data='back_start')],
            [InlineKeyboardButton(text='📝 Показать будущие события', callback_data='calendar')]
        ])

        if not past_events:
            await callback_query.message.answer(f"Прошедших событий нет", reply_markup=menu)
        else:
            await callback_query.message.answer(f"Прошедшие события:\n{past_events_str}", reply_markup=menu)

# Возврат назад в свиданиях
@router.callback_query(lambda c: c.data == "dates")
async def callback_dates(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='👩‍❤️‍👨 Назначить свидание', callback_data='new_date')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_start')]
    ])
    await callback_query.message.edit_text(f"Свидания", reply_markup=keyboard)

class NewDate(StatesGroup):
    Title = State()
    Date = State()


@router.callback_query(lambda c: c.data == "new_date")
async def callback_new_date(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите название (максимум 15 символов):")
    await state.set_state(NewDate.Title)

@router.message(NewDate.Title)
async def process_title(message: types.Message, state: FSMContext):
    title = message.text
    if len(title) > 15:
        await message.answer("Название слишком длинное. Пожалуйста, введите название (максимум 15 символов):")
        return
    await state.update_data(title=title)
    await message.answer("Введите дату (в формате ГГГГ-ММ-ДД):")
    await state.set_state(NewDate.Date)

@router.callback_query(lambda c: c.data.startswith("del_cal_"))
async def callback_del_event(callback_query: types.CallbackQuery):
    event_id = int(callback_query.data.split("_")[2])

    with SessionLocal() as db:
        event = db.query(Calendar).filter(Calendar.Id == event_id).first()
        if event is not None:
            db.delete(event)
            db.commit()
    await callback_query.message.chat.delete_message(message_id=callback_query.message.message_id)
    await callback_query.message.answer("Событие удалено", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data='redact_events')]
    ]))


