import json
import os
from ftplib import FTP
import requests
from config import FTP_HOST, FTP_USER, FTP_PASS, FTP_PIC_DIR
from main import router
from database import SessionLocal
from aiogram import types
from crud import get_couple_id_by_user_id, get_tasks_for_book, get_events_for_book

import random

def generate_json(user_id):
    with SessionLocal() as db:
        couple_id = get_couple_id_by_user_id(db, user_id)

        calendar = get_events_for_book(db, couple_id)
        tasks = get_tasks_for_book(db, couple_id)

        with open('jsons/tasks.json', 'r', encoding='utf-8') as file:
            tasks_data = json.load(file)
        if not calendar and not tasks:
            return False

        new_json = []
        if calendar != None:
            for item in calendar:
                new_json.append({
                    'Title': item.Title,
                    'PhotoPath': item.PhotoPath
                })
        if tasks != None:
            for item in tasks:
                new_json.append({
                    'Title': tasks_data[item.TaskId - 1]['title'],
                    'PhotoPath': item.PhotoPath
                })
        return new_json

@router.callback_query(lambda c: c.data == "go_book")
async def callback_tasks(callback_query: types.CallbackQuery):
    new_json = generate_json(callback_query.from_user.id)
    if new_json == False:
        await callback_query.message.answer("Нет данных для создания книги.")
        return
    with SessionLocal() as db:
        couple_id = get_couple_id_by_user_id(db, callback_query.from_user.id)
    ftp = FTP(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.cwd(f'{FTP_PIC_DIR}c{couple_id}/')

    with open(f'{couple_id}.json', 'w', encoding='utf-8') as file:
        json.dump(new_json, file, indent=4, ensure_ascii=False)
    with open(f'{couple_id}.json', 'rb') as file:
        ftp.storbinary('STOR images.json', file)
    os.remove(f"./{couple_id}.json")
    response = requests.get(f'https://bolobot.xyz/src/gett.php?folder=c{couple_id}')
    if response.status_code == 200:
        response = requests.get(f'https://bolobot.xyz/src/c{couple_id}/images.pdf')
        await callback_query.message.answer(
            f"Книга успешно создана, Вы можете скачать ее [ниже](https://bolobot.xyz/src/c{couple_id}/images.pdf?v={random.randint(0, 10000)})",
            parse_mode='Markdown')
