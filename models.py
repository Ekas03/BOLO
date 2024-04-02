from sqlalchemy import Column, BigInteger, String, Date, ForeignKey, CHAR
from database import Base, engine

class User(Base):
    __tablename__ = 'Users'

    TelegramId = Column(BigInteger, primary_key=True, index=True)
    FirstName = Column(String(255))
    Gender = Column(BigInteger)  # 1 for male, 0 for female
    CoupleId = Column(BigInteger, ForeignKey('Couples.Id'), nullable=True)


class Invitation(Base):
    __tablename__ = 'Invitations'

    Id = Column(CHAR(36), primary_key=True, index=True)
    OwnerId = Column(BigInteger, ForeignKey('Users.TelegramId'))

class Couple(Base):
    __tablename__ = 'Couples'

    Id = Column(BigInteger, primary_key=True, index=True)
    Created = Column(Date)
    OwnerId = Column(BigInteger, ForeignKey('Users.TelegramId'))
    SoulmateId = Column(BigInteger, ForeignKey('Users.TelegramId'))
    DelFlag = Column(BigInteger)


class Calendar(Base):
    __tablename__ = 'Calendar'

    Id = Column(BigInteger, primary_key=True, index=True)
    CoupleId = Column(BigInteger, ForeignKey('Couples.Id'))
    Title = Column(String(255))
    Date = Column(Date)
    Coordinates = Column(String(255), nullable=True)
    PhotoPath = Column(String(255), nullable=True)

class Task(Base):
    __tablename__ = 'Tasks'

    Id = Column(BigInteger, primary_key=True, index=True)
    CoupleId = Column(BigInteger, ForeignKey('Couples.Id'))
    TaskId = Column(BigInteger)
    Status = Column(BigInteger)
    Coordinates = Column(String(255), nullable=True)
    PhotoPath = Column(String(255), nullable=True)

class Challenge(Base):
    __tablename__ = 'Challenges'

    Id = Column(BigInteger, primary_key=True, index=True)
    CoupleId = Column(BigInteger, ForeignKey('Couples.Id'))
    ChallengeId = Column(BigInteger)
    Streak = Column(BigInteger)
    UpdatedAt = Column(Date)

Base.metadata.create_all(engine)