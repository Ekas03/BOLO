import requests
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from main import router
import json
import time
from aiogram import types

@router.callback_query(lambda c: c.data == "events_go")
async def events_go(callback_query: types.CallbackQuery):
    with open('jsons/cities.json', 'r') as f:
        cities = json.load(f)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for city in cities:
        button = InlineKeyboardButton(text=city['name'], callback_data=city['slug'])
        keyboard.inline_keyboard.append([button])

    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data='back_start')])
    await callback_query.message.edit_text("Выберите город:", reply_markup=keyboard)

@router.callback_query(lambda c: c.data in ["spb", "msk", "ekb", "nnv", "kzn"])
async def get_events(callback_query: types.CallbackQuery, page=1, city=None):
    await callback_query.message.delete()
    if page == 1:
        city = callback_query.data
    url = f'https://kudago.com/public-api/v1.2/events/?location={city}&actual_since={int(time.time())}&text_format=plain&categories=theater,recreation,quest,photo,party,holiday,exhibition,entertainment,concert,cinema&fields=id,title,description,site_url&page_size=5&page={page}'

    response = requests.get(url)
    events = response.json()

    events_text = ""
    for event in events['results']:
        title = event['title'].capitalize()
        events_text += f"[{title}]({event['site_url']}):\n{event['description']}\n\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    if page > 1:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"pr_{city}_eve_{page-1}")])
    if events['next']:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="➡️ Вперед", callback_data=f"ne_{city}_eve_{page+1}")])

    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад в меню", callback_data='events_go')])
    await callback_query.message.answer(events_text, reply_markup=keyboard, parse_mode='Markdown')

@router.callback_query(lambda c: c.data.startswith("pr_") or c.data.startswith("ne_"))
async def callback_page(callback_query: types.CallbackQuery):
    data = callback_query.data.split("_")
    city = data[1]
    page = int(data[3])
    if data[0] == "ne":
        page += 1
    else:
        page -= 1

    await get_events(callback_query, page, city)
