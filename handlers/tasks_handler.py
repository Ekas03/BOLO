from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from main import router
import json
from database import SessionLocal
from aiogram import types
from crud import get_couple_id_by_user_id, get_done_tasks, \
    get_count_done_tasks

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

