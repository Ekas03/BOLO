import datetime
import os
import uuid
from ftplib import FTP

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import FTP_HOST, FTP_USER, FTP_PASS, FTP_PIC_DIR
from ftp_crud import delete_photo_from_ftp, create_ftp_pic_directory, upload_photo_to_ftp
from handlers.start_handler import start
from handlers.tasks_handler import handle_photo_task, generate_map, handle_geo_task
from main import router
from database import SessionLocal
from aiogram import types, F
from crud import get_ongoing_events, get_couple_id_by_user_id, get_past_events, get_all_events, create_date, \
    update_event_geoposition
from models import Calendar


EVENTS_PER_PAGE = 3


# Открытие календаря
@router.callback_query(lambda c: c.data == "calendar")
@router.callback_query(lambda c: c.data == "calendar")
async def callback_calendar(callback_query: types.CallbackQuery):
    with SessionLocal() as db:
        ongoing_events = get_ongoing_events(db, get_couple_id_by_user_id(db, callback_query.from_user.id))

        ongoing_events_str = "\n".join(f"{event.Title} - {event.Date}" for event in ongoing_events)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📝 Изменить событие', callback_data='redact_events')],
            [InlineKeyboardButton(text='📝 Показать прошедшие события', callback_data='show_last_events')],
            [InlineKeyboardButton(text='📝 Добавить событие', callback_data='new_date')],
            [InlineKeyboardButton(text='🔙 Назад', callback_data='back_start')]
        ])
        if not ongoing_events:
            await callback_query.message.edit_text(f"Будущих событий нет", reply_markup=keyboard)
        else:
            await callback_query.message.edit_text(f"Будущие события:\n{ongoing_events_str}", reply_markup=keyboard, parse_mode='HTML')


# Вывод прошедших событий
@router.callback_query(lambda c: c.data == "show_past_events")
async def callback_show_past_events(callback_query: types.CallbackQuery):
    with SessionLocal() as db:
        past_events = get_past_events(db, get_couple_id_by_user_id(db, callback_query.from_user.id))

        last_events_str = "\n".join(f"{event.Title} - {event.Date}" for event in past_events)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📝 Изменить событие', callback_data='redact_events')],
            [InlineKeyboardButton(text='📝 Показать будущие события', callback_data='calendar')],
            [InlineKeyboardButton(text='📝 Добавить событие', callback_data='new_date')],
            [InlineKeyboardButton(text='🔙 Назад', callback_data='back_start')]
        ])
        if not past_events:
            await callback_query.message.edit_text(f"Прошедших событий нет", reply_markup=keyboard)
        else:
            await callback_query.message.edit_text(f"Прошедшие события:\n{last_events_str}", reply_markup=keyboard)


@router.callback_query(lambda c: c.data.startswith("next_cal_"))
async def callback_next_page(callback_query: types.CallbackQuery):
    page = int(callback_query.data.split("_")[2]) + 1
    with SessionLocal() as db:
        events = sorted(get_all_events(db, get_couple_id_by_user_id(db, callback_query.from_user.id)), key=lambda event: event.Date)
        markup = generate_events_markup(page, events)
        await callback_query.message.edit_reply_markup(reply_markup=markup)


@router.callback_query(lambda c: c.data.startswith("prev_cal_"))
async def callback_prev_page(callback_query: types.CallbackQuery):
    page = int(callback_query.data.split("_")[2]) - 1
    with SessionLocal() as db:
        events = sorted(get_all_events(db, get_couple_id_by_user_id(db, callback_query.from_user.id)), key=lambda event: event.Date)
        markup = generate_events_markup(page, events)
        await callback_query.message.edit_reply_markup(reply_markup=markup)


def generate_events_markup(page, events):
    start = page * EVENTS_PER_PAGE
    end = start + EVENTS_PER_PAGE
    page_events = events[start:end]

    keyboard = [
        [InlineKeyboardButton(text=event.Title, callback_data=f"view_cal_{event.Id}")]
        for event in page_events
    ]
    if page > 0:
        keyboard.append([InlineKeyboardButton(text="⬅️", callback_data=f"prev_cal_{page}")])
    if end < len(events):
        keyboard.append([InlineKeyboardButton(text="➡️", callback_data=f"next_cal_{page}")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data='calendar')])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(lambda c: c.data == "redact_events")
async def callback_redact_events(callback_query: types.CallbackQuery):
    await callback_query.message.chat.delete_message(message_id=callback_query.message.message_id)
    with SessionLocal() as db:
        events = sorted(get_all_events(db, get_couple_id_by_user_id(db, callback_query.from_user.id)), key=lambda event: event.Date)
        markup = generate_events_markup(0, events)
        await callback_query.message.answer("Изменить события", reply_markup=markup)


@router.callback_query(lambda c: c.data.startswith("view_cal_"))
async def callback_event(callback_query: types.CallbackQuery):
    event_id = int(callback_query.data.split("_")[2 ])

    with SessionLocal() as db:
        event = next((e for e in get_all_events(db, get_couple_id_by_user_id(db, callback_query.from_user.id)) if e.Id == event_id), None)
        if event is None:
            await callback_query.answer("Событие не найдено!")
            return

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Загрузить фото", callback_data=f"upload_{event_id}")],
        [InlineKeyboardButton(text="Отправить геопозицию", callback_data=f"geo_{event_id}")],
        [InlineKeyboardButton(text="Событие не состоялось!", callback_data=f"del_cal_{event_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data='redact_events')]
    ])
    await callback_query.message.edit_text(f"Название: {event.Title}\nДата: {event.Date}", reply_markup=markup)


@router.callback_query(lambda c: c.data.startswith("geo_"))
async def callback_geo(callback_query: types.CallbackQuery, state: FSMContext):
    event_id = int(callback_query.data.split("_")[1])
    await state.update_data(event_id=event_id)
    await callback_query.message.answer("Пожалуйста пришлите свою геолокацию.")

class PhotoUpload(StatesGroup):
    waiting_for_photo = State()

@router.callback_query(lambda c: c.data.startswith("upload_"))
async def callback_upload(callback_query: types.CallbackQuery, state: FSMContext):
    event_id = int(callback_query.data.split("_")[1])
    await state.update_data(event_id=event_id)
    await callback_query.message.answer("Пожалуйста пришлите фотографию, которую Вы хотите загрузить.")
    await state.set_state(PhotoUpload.waiting_for_photo.state)


@router.message(F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    event_id = data.get("event_id")
    await message.answer("Фото загружается...")
    if event_id is None:
        await handle_photo_task(message, state)
        return
    with SessionLocal() as db:
        delete_photo_from_ftp(get_couple_id_by_user_id(db, message.from_user.id), db, event_id)
    photo = message.photo[-1]
    file_id = photo.file_id

    ftp = FTP(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASS)

    with SessionLocal() as db:
        couple_id = get_couple_id_by_user_id(db, message.from_user.id)

    directory = os.path.join(FTP_PIC_DIR, f"c{str(couple_id)}")
    create_ftp_pic_directory(directory)

    filename = f"{uuid.uuid4()}.jpg"
    ftp_path = os.path.join(directory, filename)

    local_file_path = f"./{filename}"
    await message.bot.download(file_id, destination=local_file_path)

    upload_photo_to_ftp(local_file_path, couple_id, db, event_id)
    os.remove(local_file_path)
    await message.delete()
    await message.answer("Фото загружено успешно!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data='calendar')]
    ]))
    generate_map(couple_id)

@router.message(F.location)
async def process_geoposition(message: types.Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude
    geoposition = f"{latitude},{longitude}"
    data = await state.get_data()
    event_id = data.get("event_id")
    if event_id is None:
        await handle_geo_task(message, state)
        return
    with SessionLocal() as db:
        update_event_geoposition(db, event_id, geoposition)
        couple_id = get_couple_id_by_user_id(db, message.from_user.id)
    await message.answer("Геопозиция обновлена", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data='redact_events')]
    ]))
    generate_map(couple_id)

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


@router.message(NewDate.Date)
async def process_date(message: types.Message, state: FSMContext):
    date_text = message.text
    try:
        date = datetime.datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer("Неверный формат. Пожалуйста, введите дату (в формате ГГГГ-ММ-ДД):")
        return
    data = await state.get_data()
    title = data.get("title")
    with SessionLocal() as db:
        create_date(db, get_couple_id_by_user_id(db, message.from_user.id), title, date)
    await message.answer(f"Событие '{title}' - {date_text} успешно создано.")
    await start(message=message)
