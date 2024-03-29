
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from main import router
from database.database import SessionLocal
from aiogram import types
from database.crud import get_ongoing_events, get_couple_id_by_user_id, get_past_events


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
