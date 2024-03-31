import json
from folium import Map, Marker, Popup
from ftplib import FTP
import io
import os
from config import PIC_ADDR, FTP_USER, FTP_PASS, FTP_HOST, FTP_DIR
from crud import get_all_events_for_map, get_users_from_couple, get_done_tasks_for_map
from database import SessionLocal

def generate_map(couple_id: int):
    mymap = Map(location=[55.7558, 37.6173], zoom_start=5, attribution="BOLO")
    with SessionLocal() as db:
        user1, user2 = get_users_from_couple(db, couple_id)
        events = get_all_events_for_map(db, couple_id)
        tasks = get_done_tasks_for_map(db, couple_id)
        if not events:
            pass
        else:
            for event in events:
                latitude, longitude = map(float, event.Coordinates.split(','))
                popup_html = f"<b>Дата:</b> {event.Date}<br><img src='{PIC_ADDR}c{couple_id}/{event.PhotoPath}' width='200px'>"
                popup = Popup(popup_html, max_width=250)
                marker = Marker([latitude, longitude], popup=popup)
                mymap.add_child(marker)
        if tasks != False:
            for task in tasks:
                latitude, longitude = map(float, task.Coordinates.split(','))
                with open('jsons/tasks.json') as f:
                    tasks = json.load(f)
                task_title = [t['title'] for t in tasks if t['id'] == task.TaskId][0]
                popup_html = f"<b>{task_title}</b><img src='{PIC_ADDR}c{couple_id}/{task.PhotoPath}' width='200px'>"
                popup = Popup(popup_html, max_width=250)
                marker = Marker([latitude, longitude], popup=popup)
                mymap.add_child(marker)

    html_string = mymap.get_root().render()
    for user in [user1, user2]:
        with FTP(FTP_HOST, FTP_USER, FTP_PASS) as ftp:
            with io.BytesIO(html_string.encode()) as file:
                ftp.storbinary(f'STOR {os.path.join(FTP_DIR, f"{user.TelegramId}.html")}', file)