"""
Database Service Layer for MongoDB Operations
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from bson import ObjectId

from mongodb_config import mongodb_config
from database_models import (
    ScrapedDataModel, KnowledgeDatabaseModel, ChatHistoryModel,
    UserSessionModel, AnalyticsModel, ScrapingLogModel, DatabaseStatsModel
)

class DatabaseService:
    """Service layer for all database operations"""
    
    def __init__(self):
        self.mongodb = mongodb_config
        self.mongodb.connect_sync()
        self.mongodb.create_indexes()
    
    # ==================== SCRAPED DATA OPERATIONS ====================
    
    async def save_scraped_data(self, source_id: str, data: Dict[str, Any]) -> bool:
        """Save scraped data to MongoDB"""
        try:
            collection = self.mongodb.get_collection('scraped_data')
            
            # Update existing or insert new
            result = collection.update_one(
                {"source_id": source_id},
                {"$set": data},
                upsert=True
            )
            
            return result.acknowledged
            
        except Exception as e:
            print(f"❌ Failed to save scraped data: {str(e)}")
            return False
    
    async def get_scraped_data(self, source_id: str = None) -> Dict[str, Any]:
        """Get scraped data from MongoDB"""
        try:
            collection = self.mongodb.get_collection('scraped_data')
            
            if source_id:
                data = collection.find_one({"source_id": source_id})
                return data if data else {}
            else:
                data = list(collection.find({}))
                return {item["source_id"]: item for item in data}
                
        except Exception as e:
            print(f"❌ Failed to get scraped data: {str(e)}")
            return {}
    
    async def get_scraped_data_summary(self) -> Dict[str, Any]:
        """Get summary of all scraped data"""
        try:
            collection = self.mongodb.get_collection('scraped_data')
            
            summary = {}
            for doc in collection.find({}):
                source_id = doc.get("source_id")
                status = doc.get("status", "unknown")
                sub_pages = len(doc.get("sub_pages", []))
                summary[source_id] = {
                    "status": status,
                    "sub_pages": sub_pages,
                    "timestamp": doc.get("timestamp"),
                    "total_pages": sub_pages + 1
                }
            
            return summary
            
        except Exception as e:
            print(f"❌ Failed to get scraped data summary: {str(e)}")
            return {}
    
    # ==================== KNOWLEDGE DATABASE OPERATIONS ====================
    
    async def save_knowledge_item(self, category: str, content: str, source_url: str, source_id: str) -> bool:
        """Save a knowledge database item"""
        try:
            collection = self.mongodb.get_collection('knowledge_database')
            
            # Check if item already exists
            existing = collection.find_one({
                "category": category,
                "content": content,
                "source_id": source_id
            })
            
            if existing:
                # Update existing item
                result = collection.update_one(
                    {"_id": existing["_id"]},
                    {
                        "$set": {
                            "last_updated": datetime.now(),
                            "usage_count": existing.get("usage_count", 0) + 1
                        }
                    }
                )
            else:
                # Insert new item
                item = KnowledgeDatabaseModel(
                    category=category,
                    content=content,
                    source_url=source_url,
                    source_id=source_id,
                    keywords=self._extract_keywords(content),
                    relevance_score=self._calculate_relevance_score(content, category)
                )
                
                result = collection.insert_one(item.dict())
            
            return result.acknowledged
            
        except Exception as e:
            print(f"❌ Failed to save knowledge item: {str(e)}")
            return False
    
    async def get_knowledge_items(self, category: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get knowledge database items"""
        try:
            collection = self.mongodb.get_collection('knowledge_database')
            
            query = {"is_active": True}
            if category:
                query["category"] = category
            
            cursor = collection.find(query).sort("relevance_score", -1).limit(limit)
            return list(cursor)
            
        except Exception as e:
            print(f"❌ Failed to get knowledge items: {str(e)}")
            return []
    
    async def search_knowledge_database(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search knowledge database for relevant content"""
        try:
            collection = self.mongodb.get_collection('knowledge_database')
            
            # Text search using MongoDB text index
            result = collection.find(
                {"$text": {"$search": query}, "is_active": True},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(limit)
            
            return list(result)
            
        except Exception as e:
            print(f"❌ Failed to search knowledge database: {str(e)}")
            return []
    
    async def update_knowledge_database(self, scraped_data: Dict[str, Any]) -> bool:
        """Update knowledge database from scraped data"""
        try:
            success_count = 0
            
            for source_id, source_data in scraped_data.items():
                if source_data.get("status") != "success":
                    continue
                
                # Process main content
                content = source_data.get("content", {})
                
                # Process admissions
                if "admission_info" in content:
                    for item in content["admission_info"]:
                        if await self.save_knowledge_item("admissions", item, source_data["url"], source_id):
                            success_count += 1
                
                # Process courses
                if "course_info" in content:
                    for item in content["course_info"]:
                        if await self.save_knowledge_item("courses", item, source_data["url"], source_id):
                            success_count += 1
                
                # Process research
                if "research_info" in content:
                    for item in content["research_info"]:
                        if await self.save_knowledge_item("research", item, source_data["url"], source_id):
                            success_count += 1
                
                # Process sub-pages
                for sub_page in source_data.get("sub_pages", []):
                    sub_content = sub_page.get("content", {})
                    
                    if "admission_info" in sub_content:
                        for item in sub_content["admission_info"]:
                            if await self.save_knowledge_item("admissions", item, sub_page["url"], source_id):
                                success_count += 1
                    
                    if "course_info" in sub_content:
                        for item in sub_content["course_info"]:
                            if await self.save_knowledge_item("courses", item, sub_page["url"], source_id):
                                success_count += 1
                    
                    if "research_info" in sub_content:
                        for item in sub_content["research_info"]:
                            if await self.save_knowledge_item("research", item, sub_page["url"], source_id):
                                success_count += 1
            
            print(f"✅ Knowledge database updated with {success_count} new items")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update knowledge database: {str(e)}")
            return False
    
    # ==================== CHAT HISTORY OPERATIONS ====================
    
    async def save_chat_message(self, user_id: str, message: str, response: str, 
                               response_time: float = None, source_used: str = None) -> bool:
        """Save chat message to MongoDB"""
        try:
            collection = self.mongodb.get_collection('chat_history')
            
            # Save user message
            user_message = ChatHistoryModel(
                user_id=user_id,
                message=message,
                response="",  # User messages don't have responses
                type="user",
                message_length=len(message),
                response_length=0
            )
            
            # Save AI response
            ai_response = ChatHistoryModel(
                user_id=user_id,
                message="",  # AI responses don't have user messages
                response=response,
                type="assistant",
                message_length=0,
                response_length=len(response),
                response_time=response_time,
                source_used=source_used
            )
            
            # Insert both messages
            result1 = collection.insert_one(user_message.dict())
            result2 = collection.insert_one(ai_response.dict())
            
            return result1.acknowledged and result2.acknowledged
            
        except Exception as e:
            print(f"❌ Failed to save chat message: {str(e)}")
            return False
    
    async def get_chat_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get chat history for a user"""
        try:
            collection = self.mongodb.get_collection('chat_history')
            
            cursor = collection.find({"user_id": user_id}).sort("timestamp", -1).limit(limit)
            return list(cursor)
            
        except Exception as e:
            print(f"❌ Failed to get chat history: {str(e)}")
            return []
    
    # ==================== USER SESSION OPERATIONS ====================
    
    async def update_user_session(self, user_id: str, message_count: int = 1, 
                                response_time: float = None) -> bool:
        """Update or create user session"""
        try:
            collection = self.mongodb.get_collection('user_sessions')
            
            # Get existing session
            existing = collection.find_one({"user_id": user_id})
            
            if existing:
                # Update existing session
                update_data = {
                    "last_active": datetime.now(),
                    "total_messages": existing.get("total_messages", 0) + message_count,
                    "total_responses": existing.get("total_responses", 0) + message_count
                }
                
                if response_time:
                    current_avg = existing.get("average_response_time", 0)
                    total_responses = existing.get("total_responses", 0)
                    new_avg = ((current_avg * total_responses) + response_time) / (total_responses + 1)
                    update_data["average_response_time"] = new_avg
                
                result = collection.update_one(
                    {"user_id": user_id},
                    {"$set": update_data}
                )
            else:
                # Create new session
                session = UserSessionModel(
                    user_id=user_id,
                    total_messages=message_count,
                    total_responses=message_count,
                    average_response_time=response_time or 0.0
                )
                
                result = collection.insert_one(session.dict())
            
            return result.acknowledged
            
        except Exception as e:
            print(f"❌ Failed to update user session: {str(e)}")
            return False
    
    # ==================== ANALYTICS OPERATIONS ====================
    
    async def update_analytics(self, user_id: str, response_time: float, 
                             source_used: str, topic: str = None) -> bool:
        """Update analytics data"""
        try:
            collection = self.mongodb.get_collection('analytics')
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Get existing analytics for today
            existing = collection.find_one({"date": today, "user_id": user_id})
            
            if existing:
                # Update existing analytics
                update_data = {
                    "total_messages": existing.get("total_messages", 0) + 1,
                    "total_responses": existing.get("total_responses", 0) + 1,
                    "database_hits": existing.get("database_hits", 0) + (1 if source_used == "database" else 0),
                    "fallback_usage": existing.get("fallback_usage", 0) + (1 if source_used == "fallback" else 0)
                }
                
                # Update average response time
                current_avg = existing.get("average_response_time", 0)
                total_responses = existing.get("total_responses", 0)
                new_avg = ((current_avg * (total_responses - 1)) + response_time) / total_responses
                update_data["average_response_time"] = new_avg
                
                # Update topics
                topics = existing.get("most_asked_topics", [])
                if topic and topic not in topics:
                    topics.append(topic)
                update_data["most_asked_topics"] = topics[:10]  # Keep top 10
                
                result = collection.update_one(
                    {"date": today, "user_id": user_id},
                    {"$set": update_data}
                )
            else:
                # Create new analytics entry
                analytics = AnalyticsModel(
                    date=today,
                    user_id=user_id,
                    total_messages=1,
                    total_responses=1,
                    average_response_time=response_time,
                    database_hits=1 if source_used == "database" else 0,
                    fallback_usage=1 if source_used == "fallback" else 0,
                    most_asked_topics=[topic] if topic else []
                )
                
                result = collection.insert_one(analytics.dict())
            
            return result.acknowledged
            
        except Exception as e:
            print(f"❌ Failed to update analytics: {str(e)}")
            return False
    
    # ==================== SCRAPING LOGS OPERATIONS ====================
    
    async def log_scraping_operation(self, source_id: str, operation_type: str, 
                                   status: str, pages_scraped: int = 0, 
                                   depth_reached: int = 0, processing_time: float = 0,
                                   error_message: str = None, database_updated: bool = False,
                                   new_items_added: int = 0) -> bool:
        """Log scraping operation details"""
        try:
            collection = self.mongodb.get_collection('scraping_logs')
            
            log_entry = ScrapingLogModel(
                source_id=source_id,
                operation_type=operation_type,
                status=status,
                pages_scraped=pages_scraped,
                depth_reached=depth_reached,
                processing_time=processing_time,
                error_message=error_message,
                database_updated=database_updated,
                new_items_added=new_items_added
            )
            
            result = collection.insert_one(log_entry.dict())
            return result.acknowledged
            
        except Exception as e:
            print(f"❌ Failed to log scraping operation: {str(e)}")
            return False
    
    # ==================== DATABASE STATISTICS OPERATIONS ====================
    
    async def update_database_stats(self) -> bool:
        """Update database statistics"""
        try:
            collection = self.mongodb.get_collection('database_stats')
            
            # Calculate statistics
            scraped_collection = self.mongodb.get_collection('scraped_data')
            knowledge_collection = self.mongodb.get_collection('knowledge_database')
            chat_collection = self.mongodb.get_collection('chat_history')
            users_collection = self.mongodb.get_collection('user_sessions')
            
            total_sources = scraped_collection.count_documents({})
            total_pages_scraped = sum(
                len(doc.get("sub_pages", [])) + 1 
                for doc in scraped_collection.find({})
            )
            
            total_knowledge_items = knowledge_collection.count_documents({"is_active": True})
            knowledge_by_category = {}
            for doc in knowledge_collection.find({"is_active": True}):
                category = doc.get("category", "unknown")
                knowledge_by_category[category] = knowledge_by_category.get(category, 0) + 1
            
            total_users = users_collection.count_documents({})
            total_chat_messages = chat_collection.count_documents({})
            
            # Calculate average response time
            response_times = [
                doc.get("response_time", 0) 
                for doc in chat_collection.find({"type": "assistant", "response_time": {"$exists": True}})
            ]
            average_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Calculate database hit rate
            database_hits = chat_collection.count_documents({"source_used": "database"})
            total_responses = chat_collection.count_documents({"type": "assistant"})
            database_hit_rate = (database_hits / total_responses * 100) if total_responses > 0 else 0
            
            stats = DatabaseStatsModel(
                total_sources=total_sources,
                total_pages_scraped=total_pages_scraped,
                total_knowledge_items=total_knowledge_items,
                knowledge_by_category=knowledge_by_category,
                total_users=total_users,
                total_chat_messages=total_chat_messages,
                average_response_time=average_response_time,
                database_hit_rate=database_hit_rate,
                last_database_update=datetime.now(),
                scraping_frequency="Every 15 minutes",
                total_storage_used=self._calculate_storage_usage()
            )
            
            # Update or insert stats
            result = collection.update_one(
                {"_id": "current_stats"},
                {"$set": stats.dict()},
                upsert=True
            )
            
            return result.acknowledged
            
        except Exception as e:
            print(f"❌ Failed to update database stats: {str(e)}")
            return False
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get current database statistics"""
        try:
            collection = self.mongodb.get_collection('database_stats')
            stats = collection.find_one({"_id": "current_stats"})
            return stats if stats else {}
            
        except Exception as e:
            print(f"❌ Failed to get database stats: {str(e)}")
            return {}
    
    # ==================== UTILITY METHODS ====================
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content"""
        # Simple keyword extraction - can be enhanced with NLP
        keywords = []
        content_lower = content.lower()
        
        # Common SRM-related keywords
        srm_keywords = [
            'admission', 'course', 'engineering', 'research', 'campus', 'facility',
            'srm', 'university', 'btech', 'mtech', 'phd', 'srmjee', 'neet'
        ]
        
        for keyword in srm_keywords:
            if keyword in content_lower:
                keywords.append(keyword)
        
        return keywords[:10]  # Limit to 10 keywords
    
    def _calculate_relevance_score(self, content: str, category: str) -> float:
        """Calculate relevance score for content"""
        base_score = 0.5
        
        # Boost score based on content length (not too short, not too long)
        if 50 <= len(content) <= 500:
            base_score += 0.2
        
        # Boost score based on category relevance
        category_boost = {
            'admissions': 0.3,
            'courses': 0.3,
            'research': 0.2,
            'events': 0.1,
            'facilities': 0.1,
            'general': 0.1
        }
        
        base_score += category_boost.get(category, 0.1)
        
        # Ensure score is between 0 and 1
        return min(max(base_score, 0.0), 1.0)
    
    def _calculate_storage_usage(self) -> str:
        """Calculate approximate storage usage"""
        try:
            # This is a rough estimate - in production you'd get actual storage stats
            total_docs = 0
            for collection_name in self.mongodb.collections.values():
                collection = self.mongodb.get_collection(collection_name)
                total_docs += collection.count_documents({})
            
            # Rough estimate: 1KB per document
            estimated_bytes = total_docs * 1024
            
            if estimated_bytes < 1024 * 1024:  # Less than 1MB
                return f"{estimated_bytes / 1024:.1f} KB"
            else:
                return f"{estimated_bytes / (1024 * 1024):.1f} MB"
                
        except Exception:
            return "Unknown"
    
    def close_connections(self):
        """Close all database connections"""
        self.mongodb.close_connections()

# Global database service instance
db_service = DatabaseService()
