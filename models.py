from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import *


engine = create_engine("sqlite:///./database.sqlite3")
Base = declarative_base()

Session = sessionmaker(engine)
session = Session()

def create_session():
    return sessionmaker(engine)()

def drop_all():
    Base.metadata.drop_all(engine)

def create_all():
    Base.metadata.create_all(engine)

def reset():
    drop_all()
    create_all()

def add(_object, session=session):
    session.add(_object)

def commit(session=session):
    session.commit()

def save(_object,session=session):
    session.add(_object)
    session.commit()

def get_all(_object,session=session):
    return session.query(_object).all()

def filter(condition,*fields_or_class,session=session):
    return session.query(*fields_or_class).filter(condition)

#Create your models here
class User(Base):
    __tablename__ = "users"
   
    id = Column(Integer(), primary_key=True)
    user_id = Column(Integer(), nullable=False, unique=True)
    cash = Column(Integer(), nullable=False)
    bank = Column(Integer(), nullable=False)
    inventory = Column(JSON())
    actions = Column(JSON())

    def __str__(self):
        return self.user_id

class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer(), primary_key = True)
    name = Column(String(),nullable = False, unique = True)
    price = Column(Integer(),nullable=  False)
    description = Column(Text(),nullable = False)
    is_role = Column(BOOLEAN(), nullable = False)
    role_id = Column(Integer(), nullable = True, unique = True)
    
    def __str__(self):
        return f"[{self.id}] - ({self.name})"

