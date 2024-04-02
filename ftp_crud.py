import os
import uuid
from ftplib import FTP
from sqlalchemy.orm import Session
from config import FTP_HOST, FTP_USER, FTP_PASS, FTP_PIC_DIR
from database import SessionLocal
from models import Calendar, Task

def create_ftp_pic_directory(directory):
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)

        if directory not in ftp.nlst():
            ftp.mkd(directory)

    except Exception as e:
        pass
    finally:
        if ftp:
            ftp.quit()


def upload_photo_to_ftp(file_path: str, user_id: str, db: Session, event_id: int):
    try:
        filename = f"{uuid.uuid4()}.jpg"
        directory = FTP_PIC_DIR + "c"+ str(user_id)

        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)

        ftp_path = os.path.join(directory, filename)

        with open(file_path, 'rb') as file:
            ftp.storbinary(f'STOR {ftp_path}', file)

        with SessionLocal() as db:
            event = db.query(Calendar).filter(Calendar.Id == event_id).first()
            if event is not None:
                event.PhotoPath = filename
                db.commit()

    finally:
        if ftp:
            ftp.quit()


def upload_photo_task_to_ftp(file_path: str, user_id: str, db: Session, task_id: int):
    try:
        filename = f"{uuid.uuid4()}.jpg"
        directory = FTP_PIC_DIR + "c"+ str(user_id)

        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)

        ftp_path = os.path.join(directory, filename)

        with open(file_path, 'rb') as file:
            ftp.storbinary(f'STOR {ftp_path}', file)

        with SessionLocal() as db:
            event = db.query(Task).filter(Task.CoupleId == user_id, Task.TaskId == task_id).first()
            if event is not None:
                event.PhotoPath = filename
                db.commit()

    finally:
        if ftp:
            ftp.quit()


def delete_photo_from_ftp(user_id: str, db: Session, event_id: int):
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)

        with SessionLocal() as db:
            event = db.query(Calendar).filter(Calendar.Id == event_id).first()
            if event is not None:
                directory = FTP_PIC_DIR + "c"+ str(user_id)
                ftp.delete(os.path.join(directory, event.PhotoPath))
                event.PhotoPath = None
                db.commit()

    finally:
        if ftp:
            ftp.quit()


def delete_photo_task_from_ftp(user_id: str, db: Session, task_id: int):
    try:
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)

        with SessionLocal() as db:
            task = db.query(Task).filter(Task.CoupleId == user_id, Task.TaskId == task_id).first()
            if task is not None:
                directory = FTP_PIC_DIR + "c"+ str(user_id)
                ftp.delete(os.path.join(directory, task.PhotoPath))
                task.PhotoPath = None
                db.commit()
    finally:
        if ftp:
            ftp.quit()