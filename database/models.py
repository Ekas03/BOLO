from sqlalchemy import Column, Integer, String, Date, ForeignKey, CHAR
from sqlalchemy.orm import relationship
from database import Base, engine

class Invitation(Base):
    __tablename__ = 'Invitations'

    Id = Column(CHAR(36), primary_key=True, index=True)
    OwnerId = Column(Integer, ForeignKey('Users.TelegramId'))

class Couple(Base):
    __tablename__ = 'Couples'

    Id = Column(Integer, primary_key=True, index=True)
    Created = Column(Date)
    OwnerId = Column(Integer, ForeignKey('Users.TelegramId'))
    PartnerId = Column(Integer, ForeignKey('Users.TelegramId'))
    DelStatus = Column(Integer)


class Calendar(Base):
    __tablename__ = 'Calendar'

    Id = Column(Integer, primary_key=True, index=True)
    CoupleId = Column(Integer, ForeignKey('Couples.Id'))
    Date = Column(Date)
    Coordinates = Column(String(512))
    PhotoPath = Column(String(512))

class Task(Base):
    __tablename__ = 'Tasks'

    Id = Column(Integer, primary_key=True, index=True)
    CoupleId = Column(Integer, ForeignKey('Couples.Id'))
    TaskId = Column(Integer)

class Challenge(Base):
    __tablename__ = 'Challenges'

    Id = Column(Integer, primary_key=True, index=True)
    CoupleId = Column(Integer, ForeignKey('Couples.Id'))
    ChallengeId = Column(Integer)
    Streak = Column(Integer)
    UpdatedAt = Column(Date)


Base.metadata.create_all(engine)
