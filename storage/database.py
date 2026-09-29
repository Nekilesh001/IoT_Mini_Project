"""
Database engine and session management using SQLAlchemy.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base()


def get_engine(database_url: str, echo: bool = False):
    """
    Construct a thread-safe SQLAlchemy engine with pooling.
    """
    connect_args = {}
    poolclass = None
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        if ":memory:" in database_url:
            from sqlalchemy.pool import StaticPool
            poolclass = StaticPool
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    kwargs = {
        "echo": echo,
        "connect_args": connect_args,
        "pool_pre_ping": True
    }
    if poolclass:
        kwargs["poolclass"] = poolclass

    return create_engine(database_url, **kwargs)


def get_session_factory(engine) -> sessionmaker:
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(engine) -> None:
    """Initialize all registered database tables."""
    Base.metadata.create_all(bind=engine)
