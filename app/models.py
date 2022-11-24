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
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    owner = relationship("User", lazy="joined")

    __mapper_args__ = {"eager_defaults": True}


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    password = Column(String(60), nullable=False)
    user_creation_time = Column(DateTime, server_default=func.now())

    __mapper_args__ = {"eager_defaults": True}
