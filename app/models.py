from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Advertisement(Base):
    __tablename__ = "advertisements"

    id = Column(Integer, primary_key=True)
    title = Column(String(50), index=True, nullable=False)
    description = Column(String(300), nullable=False)
    creation_date = Column(DateTime, server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    password = Column(String(60), nullable=False)
    user_creation_time = Column(DateTime, server_default=func.now())
    advertisement_id = Column(Integer, ForeignKey("advertisements.id", ondelete="CASCADE"))
    advertisement = relationship("Advertisement", lazy="joined")


class Token(Base):
    __tablename__ = "tokens"

    id = Column(UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    user = relationship("User", lazy="joined")
    token_creation_time = Column(DateTime, server_default=func.now())
