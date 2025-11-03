"""Unified database utilities for SQLAlchemy and MongoDB."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Generator, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


# SQLAlchemy globals
engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker[Session]] = None
async_engine: Optional[AsyncEngine] = None
async_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def _create_engine() -> Engine:
    """Create the synchronous SQLAlchemy engine."""

    from sqlalchemy.pool import NullPool

    global engine, SessionLocal

    if engine is not None and SessionLocal is not None:
        return engine

    connect_args = {}
    url = settings.SQL_DATABASE_URL
    engine_kwargs = {"echo": settings.SQL_ECHO, "future": True, "connect_args": connect_args}

    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        engine_kwargs["poolclass"] = NullPool
    else:
        engine_kwargs["pool_pre_ping"] = True

    engine = create_engine(url, **engine_kwargs)

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    return engine


def get_engine() -> Engine:
    """Return the synchronous SQLAlchemy engine."""

    return _create_engine()


def get_session_factory() -> sessionmaker[Session]:
    """Return the configured session factory."""

    if SessionLocal is None:
        _create_engine()
    assert SessionLocal is not None  # for mypy/static checking
    return SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a SQLAlchemy session."""

    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def _derive_async_url(sync_url: str) -> str:
    """Derive an async database URL from a synchronous one."""

    if sync_url.startswith("sqlite+"):
        return sync_url.replace("sqlite+", "sqlite+aiosqlite+")
    if sync_url.startswith("sqlite"):
        return sync_url.replace("sqlite", "sqlite+aiosqlite", 1)
    if sync_url.startswith("postgresql+psycopg2"):
        return sync_url.replace("postgresql+psycopg2", "postgresql+asyncpg", 1)
    if sync_url.startswith("postgresql"):
        return sync_url.replace("postgresql", "postgresql+asyncpg", 1)
    if sync_url.startswith("mysql+mysqlconnector"):
        return sync_url.replace("mysql+mysqlconnector", "mysql+aiomysql", 1)
    if sync_url.startswith("mysql+pymysql"):
        return sync_url.replace("mysql+pymysql", "mysql+aiomysql", 1)
    return sync_url


def _create_async_engine() -> AsyncEngine:
    """Create the asynchronous SQLAlchemy engine."""

    global async_engine, async_session_factory

    if async_engine is not None and async_session_factory is not None:
        return async_engine

    async_url = settings.SQL_DATABASE_URL_ASYNC or _derive_async_url(settings.SQL_DATABASE_URL)
    connect_args = {}

    if async_url.startswith("sqlite+aiosqlite"):
        connect_args["check_same_thread"] = False

    async_engine = create_async_engine(
        async_url,
        echo=settings.SQL_ECHO,
        future=True,
        connect_args=connect_args,
    )

    async_session_factory = async_sessionmaker(
        bind=async_engine,
        autoflush=False,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    return async_engine


def get_async_engine() -> AsyncEngine:
    """Return the asynchronous SQLAlchemy engine."""

    return _create_async_engine()


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the configured async session factory."""

    if async_session_factory is None:
        _create_async_engine()
    assert async_session_factory is not None
    return async_session_factory


@asynccontextmanager
async def get_async_session() -> AsyncIterator[AsyncSession]:
    """Async context manager that yields an SQLAlchemy AsyncSession."""

    session_factory = get_async_session_factory()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def create_tables() -> None:
    """Create SQL tables if they do not exist."""

    engine = get_engine()
    # Import models inside the function to avoid circular imports
    from app.models import ai_models, database as database_models  # noqa: F401

    Base.metadata.create_all(bind=engine)


DEFAULT_FAQ_ENTRIES = [
    {
        "question": "What is SRM Institute of Science and Technology?",
        "answer": (
            "SRM Institute of Science and Technology (SRMIST) is a leading private university in India known for its "
            "comprehensive range of undergraduate, postgraduate, and doctoral programs across engineering, medicine, "
            "management, and humanities."
        ),
        "category": "general",
        "tags": ["overview", "srmist", "university"],
        "source_url": "https://www.srmist.edu.in/about/",
        "source_name": "SRMIST - About",
    },
    {
        "question": "How can I apply for undergraduate admissions at SRMIST?",
        "answer": (
            "Prospective students can apply for undergraduate programs through the SRMJEEE application portal. "
            "The process involves registering online, completing the application form, paying the application fee, "
            "and scheduling the SRMJEEE examination."
        ),
        "category": "admissions",
        "tags": ["admissions", "undergraduate", "srmjeee"],
        "source_url": "https://www.srmist.edu.in/admission/undergraduate/",
        "source_name": "SRMIST Admissions",
    },
    {
        "question": "Does SRMIST offer scholarships for students?",
        "answer": (
            "Yes, SRMIST offers merit-based scholarships, sports scholarships, and scholarships for socio-economic "
            "support through schemes like the SRM Founder’s Scholarship and SRM Achiever’s Scholarship."
        ),
        "category": "scholarships",
        "tags": ["financial aid", "merit", "scholarship"],
        "source_url": "https://www.srmist.edu.in/admission/scholarships/",
        "source_name": "SRMIST Scholarships",
    },
    {
        "question": "What placement support does SRMIST provide?",
        "answer": (
            "SRMIST has a dedicated Career Centre that conducts regular placement training, hosts corporate connect "
            "events, and facilitates campus recruitment drives with leading national and international companies."
        ),
        "category": "placements",
        "tags": ["placements", "career", "jobs"],
        "source_url": "https://www.srmist.edu.in/placements/",
        "source_name": "SRMIST Placements",
    },
    {
        "question": "What facilities are available on the SRMIST Kattankulathur campus?",
        "answer": (
            "The Kattankulathur campus offers modern laboratories, smart classrooms, libraries, hostels, sports "
            "complexes, medical facilities, and a variety of student clubs to support academic and extracurricular "
            "activities."
        ),
        "category": "campus",
        "tags": ["campus", "facilities", "kattankulathur"],
        "source_url": "https://www.srmist.edu.in/campus-life/",
        "source_name": "SRMIST Campus Life",
    },
]


def seed_sql_data() -> None:
    """Seed the SQL database with baseline data if required."""

    session_factory = get_session_factory()
    session = session_factory()

    try:
        from app.models.database import FaqCategory, FaqEntry

        has_entries = session.query(FaqEntry).count() > 0
        if has_entries:
            return

        for entry in DEFAULT_FAQ_ENTRIES:
            session.add(
                FaqEntry(
                    question=entry["question"],
                    answer=entry["answer"],
                    category=FaqCategory(entry["category"]),
                    tags=entry["tags"],
                    source_url=entry["source_url"],
                    source_name=entry["source_name"],
                )
            )

        session.commit()
        logger.info("✅ Seeded default FAQ entries into the SQL database")

    except SQLAlchemyError as exc:
        session.rollback()
        logger.error("❌ Failed to seed SQL database: %s", exc)
        raise
    finally:
        session.close()


async def init_sql_database() -> None:
    """Ensure the SQL database is ready for use."""

    try:
        await asyncio.to_thread(create_tables)
        await asyncio.to_thread(seed_sql_data)
        logger.info("✅ SQL database initialized")
    except Exception as exc:  # pragma: no cover - safety net for startup logging
        logger.error("❌ SQL database initialization failed: %s", exc)
        raise


# MongoDB globals
sync_client: Optional[MongoClient] = None
async_client: Optional[AsyncIOMotorClient] = None
mongodb: Optional[MongoClient] = None
async_mongodb = None


def get_mongodb_client() -> MongoClient:
    """Get synchronous MongoDB client."""

    global sync_client
    if sync_client is None:
        sync_client = MongoClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
        )
    return sync_client


def get_mongodb_database():
    """Get synchronous MongoDB database."""

    global mongodb
    if mongodb is None:
        client = get_mongodb_client()
        mongodb = client[settings.MONGO_DB_NAME]
    return mongodb


async def get_async_mongodb_client() -> AsyncIOMotorClient:
    """Get asynchronous MongoDB client."""

    global async_client
    if async_client is None:
        async_client = AsyncIOMotorClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
        )
    return async_client


async def get_async_mongodb_database():
    """Get asynchronous MongoDB database."""

    global async_mongodb
    if async_mongodb is None:
        client = await get_async_mongodb_client()
        async_mongodb = client[settings.MONGO_DB_NAME]
    return async_mongodb


async def init_mongodb() -> None:
    """Initialize MongoDB by validating the connection and indexes."""

    try:
        client = get_mongodb_client()
        client.admin.command("ping")
        logger.info("✅ MongoDB connected successfully to: %s", settings.MONGO_DB_NAME)

        await create_indexes()
        logger.info("✅ MongoDB indexes created successfully")

    except Exception as exc:  # pragma: no cover - startup logging
        logger.error("❌ MongoDB initialization failed: %s", exc)
        raise


async def create_indexes() -> None:
    """Create MongoDB indexes for performance."""

    try:
        db = get_mongodb_database()

        db.knowledge_database.create_index([("content", "text")])
        db.chat_history.create_index([("user_id", 1), ("created_at", -1)])
        db.user_sessions.create_index([("user_id", 1)])
        db.scraped_data.create_index([("source_id", 1)])

        logger.info("✅ MongoDB indexes ensured")

    except Exception as exc:  # pragma: no cover - operational logging
        logger.error("❌ Failed to create MongoDB indexes: %s", exc)
        raise


async def init_db() -> None:
    """Initialize both SQL and MongoDB resources."""

    await init_sql_database()
    await init_mongodb()


async def close_db() -> None:
    """Close database connections for SQLAlchemy and MongoDB."""

    global engine, SessionLocal, async_engine, async_session_factory, sync_client, async_client, mongodb, async_mongodb

    try:
        if async_engine is not None:
            await async_engine.dispose()
            async_engine = None
        async_session_factory = None

        if engine is not None:
            engine.dispose()
            engine = None
        SessionLocal = None

        if sync_client is not None:
            sync_client.close()
            sync_client = None
        if async_client is not None:
            async_client.close()
            async_client = None

        mongodb = None
        async_mongodb = None

        logger.info("✅ Database connections closed")

    except Exception as exc:  # pragma: no cover - shutdown logging
        logger.error("❌ Error closing database connections: %s", exc)


def get_collection(collection_name: str):
    """Get MongoDB collection synchronously."""

    db = get_mongodb_database()
    return db[collection_name]


async def get_async_collection(collection_name: str):
    """Get MongoDB collection asynchronously."""

    db = await get_async_mongodb_database()
    return db[collection_name]


__all__ = [
    "Base",
    "create_tables",
    "get_db",
    "get_async_session",
    "get_engine",
    "get_async_engine",
    "init_db",
    "close_db",
    "get_collection",
    "get_async_collection",
]

