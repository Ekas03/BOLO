from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
from database import SessionLocal
from aiogram import types
from crud import get_couple_id_by_user_id, get_challenge_streak, update_challenge_streak
from aiogram import Router

router = Router()

# Количество челленджей на странице
CHALLENGES_PER_PAGE = 4


# Вывод набора челленджей
def challenge_menu(page, challenges):
    start = page * CHALLENGES_PER_PAGE
    end = start + CHALLENGES_PER_PAGE
    page_challenges = challenges[start:end]

    menu = [
        [InlineKeyboardButton(text=challenge['title'], callback_data=f"view_{challenge['id']}")]
        for challenge in page_challenges
    ]

    if page > 0:
        menu.append([InlineKeyboardButton(text="⬅️", callback_data=f"prev_{page}")])

    if end < len(challenges):
        menu.append([InlineKeyboardButton(text="➡️", callback_data=f"next_{page}")])

    return InlineKeyboardMarkup(inline_keyboard=menu)


# Открытие челленджей
@router.callback_query(lambda c: c.data == "challenges")
async def callback_challenges(callback_query: types.CallbackQuery):
    with open('jsons/challenges.json') as f:
        challenges = json.load(f)

    markup = challenge_menu(0, challenges)
    await callback_query.message.answer("Челленджи:", reply_markup=markup)


# Переход по страницам
@router.callback_query(lambda c: c.data.startswith("next_") or c.data.startswith("prev_"))
async def callback_page(callback_query: types.CallbackQuery):
    page = int(callback_query.data.split("_")[1])
    if callback_query.data.startswith("next_"):
        page += 1
    else:
        page -= 1

    with open('jsons/challenges.json') as f:
        challenges = json.load(f)

    markup = challenge_menu(page, challenges)
    await callback_query.message.edit_text("Челленджи:", reply_markup=markup)


# Просмотр челленджа
@router.callback_query(lambda c: c.data.startswith("view_"))
async def callback_challenge(callback_query: types.CallbackQuery):
    challenge_id = int(callback_query.data.split("_")[1])

    with open('jsons/challenges.json') as f:
        challenges = json.load(f)

    challenge = next((c for c in challenges if c['id'] == challenge_id), None)
    if challenge is None:
        await callback_query.answer("Челлендж не найден!")
        return

    with SessionLocal() as db:
        challenge_streak = get_challenge_streak(db, challenge_id, get_couple_id_by_user_id(db, callback_query.from_user.id))

    if challenge_streak is None:
        challenge_streak = 0

    markup = generate_challenge_details_markup(challenge)
    await callback_query.message.edit_text(f"{challenge['description']}\n\nСтрик: {challenge_streak}", reply_markup=markup)


# Вспомогательное меню для челленджей
def generate_challenge_details_markup(challenge):
    keyboard = [
        [InlineKeyboardButton(text="⬅️", callback_data="back_challenges"),
         InlineKeyboardButton(text="Выполнено ✅", callback_data=f"done_{challenge['id']}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Функция для подтверждения выполнения челленджа
@router.callback_query(lambda c: c.data.startswith("done_"))
async def callback_done_challenge(callback_query: types.CallbackQuery):
    challenge_id = int(callback_query.data.split("_")[1])

    with SessionLocal() as db:
        if not update_challenge_streak(db, challenge_id, get_couple_id_by_user_id(db, callback_query.from_user.id)):
            await callback_query.answer("Возвращайтесь завтра! Вы уже выполнили сегодняшний челлендж")
            return

    await callback_query.answer("Вы выполнили челлендж! ✅")
    await callback_query.message.delete()
    await callback_challenges(callback_query)


# Функция для возврата в меню челленджей
@router.callback_query(lambda c: c.data == "back_challenges")
async def callback_back(callback_query: types.CallbackQuery):
    with open('jsons/challenges.json') as f:
        challenges = json.load(f)

    markup = challenge_menu(0, challenges)
    await callback_query.message.edit_text("Челледнжи:", reply_markup=markup)
