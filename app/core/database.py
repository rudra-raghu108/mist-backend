"""
MongoDB configuration and session management
"""

import logging
from typing import Optional
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

logger = logging.getLogger(__name__)

# MongoDB connection objects
sync_client: Optional[MongoClient] = None
async_client: Optional[AsyncIOMotorClient] = None
database = None
async_database = None


def get_mongodb_client() -> MongoClient:
    """Get synchronous MongoDB client"""
    global sync_client
    if sync_client is None:
        sync_client = MongoClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
    return sync_client


def get_mongodb_database():
    """Get synchronous MongoDB database"""
    global database
    if database is None:
        client = get_mongodb_client()
        database = client[settings.MONGO_DB_NAME]
    return database


async def get_async_mongodb_client() -> AsyncIOMotorClient:
    """Get asynchronous MongoDB client"""
    global async_client
    if async_client is None:
        async_client = AsyncIOMotorClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
    return async_client


async def get_async_mongodb_database():
    """Get asynchronous MongoDB database"""
    global async_database
    if async_database is None:
        client = await get_async_mongodb_client()
        async_database = client[settings.MONGO_DB_NAME]
    return async_database


async def init_db():
    """Initialize MongoDB database"""
    try:
        # Test connection
        client = get_mongodb_client()
        client.admin.command('ping')
        logger.info(f"✅ MongoDB connected successfully to: {settings.MONGO_DB_NAME}")
        
        # Create indexes
        await create_indexes()
        logger.info("✅ MongoDB indexes created successfully")
        
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {str(e)}")
        raise


async def create_indexes():
    """Create MongoDB indexes for performance"""
    try:
        db = get_mongodb_database()
        
        # Create text search index for knowledge database
        db.knowledge_database.create_index([("content", "text")])
        
        # Create indexes for common queries
        db.chat_history.create_index([("user_id", 1), ("created_at", -1)])
        db.user_sessions.create_index([("user_id", 1)])
        db.scraped_data.create_index([("source_id", 1)])
        
        logger.info("✅ MongoDB indexes created")
        
    except Exception as e:
        logger.error(f"❌ Failed to create indexes: {str(e)}")


async def close_db():
    """Close MongoDB connections"""
    try:
        global sync_client, async_client
        if sync_client:
            sync_client.close()
        if async_client:
            async_client.close()
        logger.info("✅ MongoDB connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing MongoDB connections: {str(e)}")


def get_collection(collection_name: str):
    """Get MongoDB collection"""
    db = get_mongodb_database()
    return db[collection_name]


async def get_async_collection(collection_name: str):
    """Get asynchronous MongoDB collection"""
    db = await get_async_mongodb_database()
    return db[collection_name]
