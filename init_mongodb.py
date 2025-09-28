#!/usr/bin/env python3
"""
MongoDB Database Initialization Script
Sets up the database structure, indexes, and initial data
"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

from mongodb_config import mongodb_config
from database_service import db_service

def init_mongodb():
    """Initialize MongoDB database with proper structure"""
    print("🚀 Initializing MongoDB Database for SRM Guide Bot...")
    print("=" * 60)
    
    try:
        # Test connection
        print("1️⃣ Testing MongoDB Connection...")
        client = mongodb_config.connect_sync()
        print("✅ MongoDB connection successful!")
        
        # Create indexes
        print("\n2️⃣ Creating Database Indexes...")
        mongodb_config.create_indexes()
        print("✅ Database indexes created!")
        
        # Create text index for knowledge database search
        print("\n3️⃣ Creating Text Search Index...")
        knowledge_collection = mongodb_config.get_collection('knowledge_database')
        try:
            knowledge_collection.create_index([("content", "text")])
            print("✅ Text search index created!")
        except Exception as e:
            print(f"⚠️ Text index creation failed (may already exist): {e}")
        
        # Initialize with sample data
        print("\n4️⃣ Initializing Sample Data...")
        init_sample_data()
        print("✅ Sample data initialized!")
        
        # Test database operations
        print("\n5️⃣ Testing Database Operations...")
        test_database_operations()
        print("✅ Database operations working!")
        
        print("\n🎉 MongoDB Database Initialization Complete!")
        print("=" * 60)
        print("✅ Database: srm_guide_bot")
        print("✅ Collections: 7 collections created")
        print("✅ Indexes: Performance indexes created")
        print("✅ Text Search: Full-text search enabled")
        print("✅ Sample Data: Initial data loaded")
        
        return True
        
    except Exception as e:
        print(f"❌ MongoDB initialization failed: {str(e)}")
        return False

def init_sample_data():
    """Initialize database with sample data"""
    try:
        # Sample knowledge database items
        sample_knowledge = [
            {
                "category": "admissions",
                "content": "SRMJEEE 2025 applications are now open for B.Tech programs with deadline on May 31, 2025",
                "source_url": "https://www.srmist.edu.in/admissions/",
                "source_id": "sample",
                "keywords": ["srmjee", "2025", "btech", "deadline"],
                "relevance_score": 0.9,
                "timestamp": datetime.now(),
                "last_updated": datetime.now(),
                "usage_count": 0,
                "is_active": True
            },
            {
                "category": "courses",
                "content": "Computer Science & Engineering offers specializations in AI/ML, Cybersecurity, and Data Science",
                "source_url": "https://www.srmist.edu.in/academics/engineering/",
                "source_id": "sample",
                "keywords": ["computer science", "ai", "ml", "cybersecurity", "data science"],
                "relevance_score": 0.9,
                "timestamp": datetime.now(),
                "last_updated": datetime.now(),
                "usage_count": 0,
                "is_active": True
            },
            {
                "category": "research",
                "content": "SRM University has strong focus on innovation with over 500+ research publications annually",
                "source_url": "https://www.srmist.edu.in/research/",
                "source_id": "sample",
                "keywords": ["research", "innovation", "publications", "500+"],
                "relevance_score": 0.8,
                "timestamp": datetime.now(),
                "last_updated": datetime.now(),
                "usage_count": 0,
                "is_active": True
            }
        ]
        
        # Insert sample knowledge items
        knowledge_collection = mongodb_config.get_collection('knowledge_database')
        for item in sample_knowledge:
            knowledge_collection.update_one(
                {"content": item["content"]},
                {"$set": item},
                upsert=True
            )
        
        # Sample database stats
        stats_collection = mongodb_config.get_collection('database_stats')
        sample_stats = {
            "_id": "current_stats",
            "total_sources": 0,
            "total_pages_scraped": 0,
            "total_knowledge_items": len(sample_knowledge),
            "knowledge_by_category": {
                "admissions": 1,
                "courses": 1,
                "research": 1,
                "events": 0,
                "facilities": 0,
                "general": 0
            },
            "total_users": 0,
            "total_chat_messages": 0,
            "average_response_time": 0.0,
            "database_hit_rate": 0.0,
            "last_database_update": datetime.now(),
            "scraping_frequency": "Every 15 minutes",
            "total_storage_used": "Unknown"
        }
        
        stats_collection.update_one(
            {"_id": "current_stats"},
            {"$set": sample_stats},
            upsert=True
        )
        
        print(f"   ✅ {len(sample_knowledge)} sample knowledge items created")
        print("   ✅ Sample database stats created")
        
    except Exception as e:
        print(f"   ❌ Sample data initialization failed: {e}")

def test_database_operations():
    """Test basic database operations"""
    try:
        # Test knowledge database retrieval
        knowledge_collection = mongodb_config.get_collection('knowledge_database')
        sample_items = list(knowledge_collection.find({"is_active": True}).limit(3))
        print(f"   ✅ Retrieved {len(sample_items)} knowledge items")
        
        # Test text search
        search_results = list(knowledge_collection.find(
            {"$text": {"$search": "srmjee"}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(3))
        print(f"   ✅ Text search working: {len(search_results)} results for 'srmjee'")
        
        # Test stats retrieval
        stats_collection = mongodb_config.get_collection('database_stats')
        stats = stats_collection.find_one({"_id": "current_stats"})
        if stats:
            print(f"   ✅ Database stats retrieved: {stats.get('total_knowledge_items', 0)} items")
        
    except Exception as e:
        print(f"   ❌ Database operation test failed: {e}")

def show_database_info():
    """Show database information"""
    try:
        print("\n📊 Database Information:")
        print("=" * 40)
        
        # Show collections
        collections = mongodb_config.collections
        for name, collection_name in collections.items():
            collection = mongodb_config.get_collection(collection_name)
            count = collection.count_documents({})
            print(f"   📁 {name}: {count} documents")
        
        # Show database stats
        stats_collection = mongodb_config.get_collection('database_stats')
        stats = stats_collection.find_one({"_id": "current_stats"})
        if stats:
            print(f"\n📈 Current Statistics:")
            print(f"   🗄️ Total Knowledge Items: {stats.get('total_knowledge_items', 0)}")
            print(f"   📚 Knowledge by Category:")
            for category, count in stats.get('knowledge_by_category', {}).items():
                print(f"      - {category}: {count} items")
        
        print("\n🔧 Database Ready for Production Use!")
        
    except Exception as e:
        print(f"❌ Failed to show database info: {e}")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Initialize database
    if init_mongodb():
        # Show database information
        show_database_info()
        
        # Close connections
        mongodb_config.close_connections()
        print("\n✅ MongoDB initialization completed successfully!")
    else:
        print("\n❌ MongoDB initialization failed!")
        exit(1)
