from sqlalchemy.orm import Session
from models import User

# Создание нового юзера
def create_user(db: Session, telegram_id: int, first_name: str, gender: int, couple_id: int = None):
    new_user = User(TelegramId=telegram_id, FirstName=first_name, Gender=gender, CoupleId=couple_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Удаление пользователя
def delete_user(db: Session, user_id: int):
    db.query(User).filter(User.Id == user_id).delete()
    db.commit()