import datetime
from sqlalchemy.orm import Session
from models import User, Invitation, Couple, Calendar, Challenge


# Создание нового пользователя
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


# Создание приглашения
def create_invitation(db: Session, id: str, owner_id: int):
    new_invitation = Invitation(Id=id, OwnerId=owner_id)
    db.add(new_invitation)
    db.commit()
    db.refresh(new_invitation)
    return new_invitation


# Удаления приглашения
def delete_invitation(db: Session, owner_id: int):
    db.query(Invitation).filter(Invitation.OwnerId == owner_id).delete()
    db.commit()


# Проверка существования приглашения по пользователю
def check_invitation_exists(db: Session, owner_id: int):
    return db.query(Invitation).filter(Invitation.OwnerId == owner_id).first() is not None


# Проверка существования приглашения по uuid
def check_invitation_exists_by_uuid(db: Session, invitation_id: str):
    return db.query(Invitation).filter(Invitation.Id == invitation_id).first() is not None


# uuid приглашение
def get_invitation_uuid(db: Session, owner_id: int):
    invitation = db.query(Invitation).filter(Invitation.OwnerId == owner_id).first()
    return invitation.Id if invitation else None


# Пользователь по ID Телеграма
def get_user_by_telegram_id(db: Session, telegram_id: int):
    return db.query(User).filter(User.TelegramId == telegram_id).first()


# Проверка существования пользователя
def check_user_exists(db: Session, telegram_id: int):
    return db.query(User).filter(User.TelegramId == telegram_id).first() is not None


# Проверка наличия пары у пользователя
def check_user_has_couple(db: Session, telegram_id: int):
    user = db.query(User).filter(User.TelegramId == telegram_id).first()
    if user is None:
        return False
    return user.CoupleId is not None


# Удаление приглашения по ID Телеграма
def delete_invitation_by_user(db: Session, telegram_id: int):
    invitation = db.query(Invitation).filter(Invitation.OwnerId == telegram_id).first()
    if invitation:
        db.delete(invitation)
        db.commit()


# Создание пары пользователей
def handle_invitation_code(db: Session, invitation_id: str, telegram_id: int):
    invitation = db.query(Invitation).filter(Invitation.Id == invitation_id).first()
    if invitation:
        if invitation.OwnerId == telegram_id:
            return None
        db.delete(invitation)
        db.commit()
        delete_invitation_by_user(db, telegram_id)

        today = datetime.date.today()
        new_couple = Couple(Created=today,OwnerId=invitation.OwnerId, SoulmateId=telegram_id, DelFlag=0)
        db.add(new_couple)
        db.commit()
        db.refresh(new_couple)

        owner_user = db.query(User).filter(User.TelegramId == invitation.OwnerId).first()
        owner_user.CoupleId = new_couple.Id
        invited_user = db.query(User).filter(User.TelegramId == telegram_id).first()
        invited_user.CoupleId = new_couple.Id
        db.commit()

        return new_couple
    else:
        return None


# Счетчик дней
def get_couple_days(db: Session, couple_id: int):
    couple = db.query(Couple).filter(Couple.Id == couple_id).first()
    if couple:
        return (datetime.date.today() - couple.Created).days
    return None


# Текущие события
def get_ongoing_events(db: Session, couple_id: int):
    events = db.query(Calendar).filter(Calendar.CoupleId == couple_id, Calendar.Date >= datetime.date.today()).all()
    return events


# ID пары по пользователю
def get_couple_id_by_user_id(db: Session, user_id: int):
    user = db.query(User).filter(User.TelegramId == user_id).first()
    return user.CoupleId if user else None


# История событий
def get_past_events(db: Session, couple_id: int):
    events = db.query(Calendar).filter(Calendar.CoupleId == couple_id, Calendar.Date < datetime.date.today()).all()
    return events


# Продолжительность 'стрик'
def get_challenge_streak(db: Session, challenge_id: int, couple_id: int):
    challenge = db.query(Challenge).filter(Challenge.ChallengeId == challenge_id, Challenge.CoupleId == couple_id).first()
    if challenge is not None:
        return challenge.Streak
    else:
        return None


# Обновить продолжительность 'стрика'
def update_challenge_streak(db: Session, challenge_id: int, couple_id: int):
    challenge = db.query(Challenge).filter(Challenge.ChallengeId == challenge_id, Challenge.CoupleId == couple_id).first()
    if challenge is not None:
        if datetime.date.today() != challenge.UpdatedAt + datetime.timedelta(days=1):
            challenge.Streak = 0
            challenge.UpdatedAt = datetime.date.today()
            return False
        else:
            challenge.Streak += 1
            challenge.UpdatedAt = datetime.date.today()
    else:
        challenge = Challenge(ChallengeId=challenge_id, CoupleId=couple_id, Streak=1, UpdatedAt=datetime.date.today())
        db.add(challenge)

    db.commit()
    return True
