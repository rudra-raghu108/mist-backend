"""
MongoDB Configuration and Database Connection
"""

import os
from typing import Optional
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MongoDBConfig:
    """MongoDB configuration and connection management"""
    
    def __init__(self):
        # MongoDB connection settings
        self.mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
        self.database_name = os.getenv('MONGO_DB_NAME', 'srm_guide_bot')
        self.username = os.getenv('MONGO_USERNAME')
        self.password = os.getenv('MONGO_PASSWORD')
        
        # Build connection string
        if self.username and self.password:
            # Parse URI to add authentication
            if 'mongodb://' in self.mongo_uri:
                self.mongo_uri = self.mongo_uri.replace('mongodb://', f'mongodb://{self.username}:{self.password}@')
            elif 'mongodb+srv://' in self.mongo_uri:
                self.mongo_uri = self.mongo_uri.replace('mongodb+srv://', f'mongodb+srv://{self.username}:{self.password}@')
        
        # Collections
        self.collections = {
            'scraped_data': 'scraped_data',
            'knowledge_database': 'knowledge_database',
            'chat_history': 'chat_history',
            'user_sessions': 'user_sessions',
            'analytics': 'analytics',
            'scraping_logs': 'scraping_logs'
        }
        
        # Connection objects
        self.sync_client: Optional[MongoClient] = None
        self.async_client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.async_database = None
    
    def connect_sync(self) -> MongoClient:
        """Create synchronous MongoDB connection"""
        try:
            self.sync_client = MongoClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            
            # Test connection
            self.sync_client.admin.command('ping')
            print(f"✅ MongoDB connected successfully to: {self.database_name}")
            
            self.database = self.sync_client[self.database_name]
            return self.sync_client
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {str(e)}")
            raise
    
    def connect_async(self) -> AsyncIOMotorClient:
        """Create asynchronous MongoDB connection"""
        try:
            self.async_client = AsyncIOMotorClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000
            )
            
            # Test connection
            self.async_database = self.async_client[self.database_name]
            print(f"✅ Async MongoDB connected successfully to: {self.database_name}")
            
            return self.async_client
            
        except Exception as e:
            print(f"❌ Async MongoDB connection failed: {str(e)}")
            raise
    
    def get_collection(self, collection_name: str):
        """Get synchronous collection"""
        if not self.database:
            self.connect_sync()
        return self.database[self.collections[collection_name]]
    
    def get_async_collection(self, collection_name: str):
        """Get asynchronous collection"""
        if not self.async_database:
            self.connect_async()
        return self.async_database[self.collections[collection_name]]
    
    def close_connections(self):
        """Close all database connections"""
        if self.sync_client:
            self.sync_client.close()
            print("✅ Sync MongoDB connection closed")
        
        if self.async_client:
            self.async_client.close()
            print("✅ Async MongoDB connection closed")
    
    def create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            # Scraped data indexes
            scraped_collection = self.get_collection('scraped_data')
            scraped_collection.create_index([("source_id", 1)])
            scraped_collection.create_index([("timestamp", -1)])
            scraped_collection.create_index([("status", 1)])
            
            # Knowledge database indexes
            knowledge_collection = self.get_collection('knowledge_database')
            knowledge_collection.create_index([("category", 1)])
            knowledge_collection.create_index([("last_updated", -1)])
            
            # Chat history indexes
            chat_collection = self.get_collection('chat_history')
            chat_collection.create_index([("user_id", 1)])
            chat_collection.create_index([("timestamp", -1)])
            chat_collection.create_index([("type", 1)])
            
            # User sessions indexes
            sessions_collection = self.get_collection('user_sessions')
            sessions_collection.create_index([("user_id", 1)], unique=True)
            sessions_collection.create_index([("last_active", -1)])
            
            # Analytics indexes
            analytics_collection = self.get_collection('analytics')
            analytics_collection.create_index([("date", -1)])
            analytics_collection.create_index([("user_id", 1)])
            
            # Scraping logs indexes
            logs_collection = self.get_collection('scraping_logs')
            logs_collection.create_index([("timestamp", -1)])
            logs_collection.create_index([("source_id", 1)])
            logs_collection.create_index([("status", 1)])
            
            print("✅ MongoDB indexes created successfully")
            
        except Exception as e:
            print(f"❌ Failed to create indexes: {str(e)}")

# Global MongoDB configuration instance
mongodb_config = MongoDBConfig()
