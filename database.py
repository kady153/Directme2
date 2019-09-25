import sys
import os
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from datetime import datetime
from sqlalchemy import desc

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(String(500), primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(500))
    country=Column(String(250), nullable=True)
    city=Column(String(250), nullable=True)
    user_type=Column(String(250),nullable=True)


class msg_history(Base):
    __tablename__ = 'msg_history'

    id = Column(Integer, primary_key=True)
    msg = Column(String(5000), nullable=False)
    created_at=Column(String(50), default=(datetime.utcnow().strftime('%Y-%m-%d %H:%M')))
    room=Column(String(5000), nullable=False)
    msg_from=Column(String(2000), nullable=False)


engine = create_engine(
  'sqlite:///site.dp')
Base.metadata.create_all(engine)