from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey
from database import Base
from sqlalchemy.orm import relationship

# Base is the main thing that makes your class a real table in db
class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer,primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)


class DBTask(Base):
    __tablename__ = "Tasks"
    id=Column(Integer, primary_key=True, index=True)
    title=Column(String)
    description=Column(String)
    is_completed = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
