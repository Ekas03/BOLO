import os
import uuid
from ftplib import FTP

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import FTP_HOST, FTP_USER, FTP_PASS, FTP_PIC_DIR
from ftp_crud import create_ftp_pic_directory, upload_photo_task_to_ftp
from main import router
import json
from database import SessionLocal
from aiogram import types
from crud import get_couple_id_by_user_id, get_done_tasks, \
    get_count_done_tasks, new_done_task, update_task_geoposition

TASKS_PER_PAGE = 3


def generate_challenges_markup(page, tasks):
    start = page * TASKS_PER_PAGE
    end = start + TASKS_PER_PAGE
    page_challenges = tasks[start:end]

    keyboard = [
        [InlineKeyboardButton(text=challenge['title'], callback_data=f"vt_{challenge['id']}")]
        for challenge in page_challenges
    ]

    if page > 0:
        keyboard.append([InlineKeyboardButton(text="⬅️", callback_data=f"ppt_{page}")])

    if end < len(tasks):
        keyboard.append([InlineKeyboardButton(text="➡️", callback_data=f"npt_{page}")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data='back_start')])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(lambda c: c.data == "tasks")
async def callback_tasks(callback_query: types.CallbackQuery):
    with open('jsons/tasks.json') as f:
        tasks = json.load(f)

    with SessionLocal() as db:
        done_tasks = get_done_tasks(db, get_couple_id_by_user_id(db, callback_query.from_user.id))
    done_task_ids = {done_task.TaskId for done_task in done_tasks}

    tasks = [task for task in tasks if task['id'] not in done_task_ids]

    markup = generate_challenges_markup(0, tasks)
    await callback_query.message.edit_text(f"BOLOcoins за выполненные задания: {get_count_done_tasks(db, get_couple_id_by_user_id(db, callback_query.from_user.id))}\nЗадания:", reply_markup=markup)

@router.callback_query(lambda c: c.data.startswith("npt_") or c.data.startswith("ppt_"))
async def callback_page(callback_query: types.CallbackQuery):
    page = int(callback_query.data.split("_")[1])
    if callback_query.data.startswith("npt_"):
        page += 1
    else:
        page -= 1

    with open('jsons/tasks.json') as f:
        tasks = json.load(f)
    with SessionLocal() as db:
        done_tasks = get_done_tasks(db, get_couple_id_by_user_id(db, callback_query.from_user.id))
    done_task_ids = {done_task.TaskId for done_task in done_tasks}

    tasks = [task for task in tasks if task['id'] not in done_task_ids]
    markup = generate_challenges_markup(page, tasks)
    await callback_query.message.edit_text("Задания:", reply_markup=markup)

def generate_challenge_details_markup(challenge):
    keyboard = [
        [InlineKeyboardButton(text="⬅️", callback_data="back_tasks"),
         InlineKeyboardButton(text="Выполнено ✅", callback_data=f"dt_{challenge['id']}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.callback_query(lambda c: c.data.startswith("vt_"))
async def callback_challenge(callback_query: types.CallbackQuery):
    challenge_id = int(callback_query.data.split("_")[1])

    with open('jsons/tasks.json') as f:
        challenges = json.load(f)

    challenge = next((c for c in challenges if c['id'] == challenge_id), None)
    if challenge is None:
        await callback_query.answer("Задание не найдено!")
        return


    markup = generate_challenge_details_markup(challenge)
    await callback_query.message.edit_text(f"ID: {challenge_id}\n\n{challenge['description']}\n\n", reply_markup=markup)

@router.callback_query(lambda c: c.data == "back_tasks")
async def callback_back(callback_query: types.CallbackQuery):
    with open('jsons/tasks.json') as f:
        challenges = json.load(f)

    markup = generate_challenges_markup(0, challenges)
    await callback_query.message.edit_text("Задания:", reply_markup=markup)

@router.callback_query(lambda c: c.data.startswith("dt_"))
async def callback_done_task(callback_query: types.CallbackQuery, state: FSMContext):
    task_id = int(callback_query.data.split("_")[1])
    with SessionLocal() as db:
        new_done_task(db, get_couple_id_by_user_id(db, callback_query.from_user.id), task_id)
    await callback_query.answer("Вы выполнили задание! ✅ Теперь отправьте фото.")
    await state.update_data(task_id=task_id)
    await state.set_state(TaskDone.waiting_for_photo.state)

class TaskDone(StatesGroup):
    waiting_for_photo = State()
    waiting_for_location = State()

async def handle_photo_task(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id

    data = await state.get_data()
    task_id = data.get("task_id")
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

    upload_photo_task_to_ftp(local_file_path, couple_id, db, task_id)
    os.remove(local_file_path)
    await message.answer("Теперь отправьте геопозицию.")
    await state.set_state(TaskDone.waiting_for_location.state)


def generate_map(couple_id):
    pass


async def handle_geo_task(message: types.Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude
    geoposition = f"{latitude},{longitude}"
    data = await state.get_data()
    task_id = data.get('task_id')
    with SessionLocal() as db:
        couple_id = get_couple_id_by_user_id(db, message.from_user.id)
        update_task_geoposition(db, couple_id, task_id, geoposition)
    await message.answer("Геопозиция обновлена", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data='tasks')]
    ]))
    generate_map(couple_id)
