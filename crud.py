import datetime
from sqlalchemy.orm import Session
from models import User, Invitation, Couple, Calendar, Task, Challenge

def create_user(db: Session, telegram_id: int, first_name: str, gender: int, couple_id: int = None):
    new_user = User(TelegramId=telegram_id, FirstName=first_name, Gender=gender, CoupleId=couple_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def create_invitation(db: Session, id: str, owner_id: int):
    new_invitation = Invitation(Id=id, OwnerId=owner_id)
    db.add(new_invitation)
    db.commit()
    db.refresh(new_invitation)
    return new_invitation

def delete_invitation(db: Session, owner_id: int):
    db.query(Invitation).filter(Invitation.OwnerId == owner_id).delete()
    db.commit()

def check_invitation_exists(db: Session, owner_id: int):
    return db.query(Invitation).filter(Invitation.OwnerId == owner_id).first() is not None

def check_invitation_exists_by_uuid(db: Session, invitation_id: str):
    return db.query(Invitation).filter(Invitation.Id == invitation_id).first() is not None

def get_invitation_uuid(db: Session, owner_id: int):
    invitation = db.query(Invitation).filter(Invitation.OwnerId == owner_id).first()
    return invitation.Id if invitation else None
def get_user_by_telegram_id(db: Session, telegram_id: int):
    return db.query(User).filter(User.TelegramId == telegram_id).first()

def check_user_exists(db: Session, telegram_id: int):
    return db.query(User).filter(User.TelegramId == telegram_id).first() is not None

def check_user_has_couple(db: Session, telegram_id: int):
    user = db.query(User).filter(User.TelegramId == telegram_id).first()
    if user is None:
        return False
    return user.CoupleId is not None

def delete_invitation_by_user(db: Session, telegram_id: int):
    invitation = db.query(Invitation).filter(Invitation.OwnerId == telegram_id).first()
    if invitation:
        db.delete(invitation)
        db.commit()

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

def delete_user(db: Session, user_id: int):
    db.query(User).filter(User.Id == user_id).delete()
    db.commit()

def get_couple_days(db: Session, couple_id: int):
    couple = db.query(Couple).filter(Couple.Id == couple_id).first()
    if couple:
        return (datetime.date.today() - couple.Created).days
    return None

def get_ongoing_events(db: Session, couple_id: int):
    events = db.query(Calendar).filter(Calendar.CoupleId == couple_id, Calendar.Date >= datetime.date.today()).all()
    return events

def get_couple_id_by_user_id(db: Session, user_id: int):
    user = db.query(User).filter(User.TelegramId == user_id).first()
    return user.CoupleId if user else None

def get_last_events(db: Session, couple_id: int):
    events = db.query(Calendar).filter(Calendar.CoupleId == couple_id, Calendar.Date < datetime.date.today()).all()
    return events

def get_challenge_streak(db: Session, challenge_id: int, couple_id: int):
    challenge = db.query(Challenge).filter(Challenge.ChallengeId == challenge_id, Challenge.CoupleId == couple_id).first()
    if challenge is not None:
        return challenge.Streak
    else:
        return None

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

def create_date(db: Session, couple_id: int, title: str, date: datetime.date, coordinates: str = None,
                photo_path: str = None):
    new_date = Calendar(CoupleId=couple_id, Title=title, Date=date, Coordinates=coordinates, PhotoPath=photo_path)
    db.add(new_date)
    db.commit()
    db.refresh(new_date)
    return new_date

def get_all_events(db: Session, couple_id: int):
    return db.query(Calendar).filter(Calendar.CoupleId == couple_id).all()


def update_event_photo(db: Session, event_id: int, photo_id: str):
    event = db.query(Calendar).filter(Calendar.Id == event_id).first()
    if event is not None:
        event.PhotoId = photo_id
        db.commit()

def update_event_geoposition(db: Session, event_id: int, geoposition: str):
    event = db.query(Calendar).filter(Calendar.Id == event_id).first()
    if event is not None:
        event.Coordinates = geoposition
        db.commit()

def get_all_events_for_map(db: Session, couple_id: int):
    events = db.query(Calendar).filter(Calendar.CoupleId == couple_id).filter(Calendar.Coordinates != None).filter(Calendar.PhotoPath != None).all()
    return events

def get_users_from_couple(db: Session, couple_id: int):
    user1 = db.query(User).filter(User.CoupleId == couple_id).first()
    user2 = db.query(User).filter(User.CoupleId == couple_id).filter(User.TelegramId != user1.TelegramId).first()

    return user1, user2

def get_done_tasks(db: Session, couple_id: int):
    return db.query(Task).filter(Task.CoupleId == couple_id, Task.Status == 1).all()

def get_done_tasks_for_map(db: Session, couple_id: int):
    tasks = db.query(Task).filter(Task.CoupleId == couple_id, Task.Coordinates != None, Task.PhotoPath != None, Task.Status == 1).all()
    return tasks if tasks else False

def get_count_done_tasks(db: Session, couple_id: int):
    return db.query(Task).filter(Task.CoupleId == couple_id, Task.Status == 1).count()

def new_done_task(db: Session, couple_id: int, task_id: int):
    new_task = Task(CoupleId=couple_id, TaskId=task_id, Status=1)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task

def update_task_geoposition(db: Session, couple_id: int,task_id: int, geoposition: str):
    task = db.query(Task).filter(Task.CoupleId == couple_id, Task.TaskId == task_id).first()
    if task is not None:
        task.Coordinates = geoposition
        db.commit()

def get_tasks_for_book(db: Session, couple_id: int):
    return db.query(Task).filter(Task.CoupleId == couple_id, Task.PhotoPath != None).all()

def get_events_for_book(db: Session, couple_id: int):
    return db.query(Calendar).filter(Calendar.CoupleId == couple_id, Calendar.PhotoPath != None).all()