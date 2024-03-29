from sqlalchemy import Column, Integer, String, Date, ForeignKey, CHAR
from database import Base, engine

class User(Base):
    __tablename__ = 'Users'

    TelegramId = Column(Integer, primary_key=True, index=True)
    FirstName = Column(String(255))
    Gender = Column(Integer)  # 1 for male, 0 for female
    CoupleId = Column(Integer, ForeignKey('Couples.Id'), nullable=True)

class Invitation(Base):
    __tablename__ = 'Invitations'

    Id = Column(CHAR(36), primary_key=True, index=True)
    OwnerId = Column(Integer, ForeignKey('Users.TelegramId'))

class Couple(Base):
    __tablename__ = 'Couples'

    Id = Column(Integer, primary_key=True, index=True)
    Created = Column(Date)
    OwnerId = Column(Integer, ForeignKey('Users.TelegramId'))
    SoulmateId = Column(Integer, ForeignKey('Users.TelegramId'))
    DelFlag = Column(Integer)

class Calendar(Base):
    __tablename__ = 'Calendar'

    Id = Column(Integer, primary_key=True, index=True)
    CoupleId = Column(Integer, ForeignKey('Couples.Id'))
    Date = Column(Date)
    Coordinates = Column(String(255))
    PhotoPath = Column(String(255))

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