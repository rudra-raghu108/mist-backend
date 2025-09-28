"""
MongoDB Database Models and Schemas
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ScrapedDataModel(BaseModel):
    """Model for scraped website data"""
    source_id: str = Field(..., description="Unique identifier for the source")
    source_name: str = Field(..., description="Human-readable name of the source")
    url: str = Field(..., description="Main URL of the source")
    status: str = Field(..., description="Scraping status (success, failed, in_progress)")
    timestamp: datetime = Field(default_factory=datetime.now, description="When data was scraped")
    depth: int = Field(..., description="Current scraping depth")
    max_depth: int = Field(..., description="Maximum allowed depth")
    max_pages: int = Field(..., description="Maximum allowed pages")
    total_pages_scraped: int = Field(default=0, description="Total pages scraped")
    content: Dict[str, Any] = Field(default_factory=dict, description="Extracted content")
    sub_pages: List[Dict[str, Any]] = Field(default_factory=list, description="Sub-page data")
    error_message: Optional[str] = Field(None, description="Error message if scraping failed")
    processing_time: Optional[float] = Field(None, description="Time taken to scrape in seconds")

class KnowledgeDatabaseModel(BaseModel):
    """Model for knowledge database entries"""
    category: str = Field(..., description="Content category (admissions, courses, research, etc.)")
    content: str = Field(..., description="The actual content text")
    source_url: str = Field(..., description="URL where this content was found")
    source_id: str = Field(..., description="ID of the source where content was found")
    keywords: List[str] = Field(default_factory=list, description="Extracted keywords")
    relevance_score: float = Field(default=1.0, description="Relevance score (0-1)")
    timestamp: datetime = Field(default_factory=datetime.now, description="When content was added")
    last_updated: datetime = Field(default_factory=datetime.now, description="When content was last updated")
    usage_count: int = Field(default=0, description="How many times this content was used")
    is_active: bool = Field(default=True, description="Whether this content is active")

class ChatHistoryModel(BaseModel):
    """Model for chat history entries"""
    user_id: str = Field(..., description="Unique identifier for the user")
    message: str = Field(..., description="The message content")
    response: str = Field(..., description="AI response to the message")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the chat occurred")
    type: str = Field(..., description="Type of message (user, assistant)")
    message_length: int = Field(..., description="Length of the message")
    response_length: int = Field(..., description="Length of the response")
    response_time: Optional[float] = Field(None, description="Time taken to generate response in ms")
    source_used: Optional[str] = Field(None, description="Source of information used (database, fallback, etc.)")
    user_rating: Optional[int] = Field(None, description="User rating of the response (1-5)")

class UserSessionModel(BaseModel):
    """Model for user sessions"""
    user_id: str = Field(..., description="Unique identifier for the user")
    session_start: datetime = Field(default_factory=datetime.now, description="When session started")
    last_active: datetime = Field(default_factory=datetime.now, description="Last activity timestamp")
    total_messages: int = Field(default=0, description="Total messages in this session")
    total_responses: int = Field(default=0, description="Total AI responses in this session")
    average_response_time: float = Field(default=0.0, description="Average response time in ms")
    preferred_topics: List[str] = Field(default_factory=list, description="Topics user frequently asks about")
    session_duration: Optional[float] = Field(None, description="Session duration in seconds")
    is_active: bool = Field(default=True, description="Whether session is currently active")

class AnalyticsModel(BaseModel):
    """Model for analytics data"""
    date: str = Field(..., description="Date of analytics (YYYY-MM-DD)")
    user_id: Optional[str] = Field(None, description="User ID for user-specific analytics")
    total_messages: int = Field(default=0, description="Total messages on this date")
    total_responses: int = Field(default=0, description="Total AI responses on this date")
    average_response_time: float = Field(default=0.0, description="Average response time in ms")
    most_asked_topics: List[str] = Field(default_factory=list, description="Most frequently asked topics")
    database_hits: int = Field(default=0, description="Times knowledge database was used")
    fallback_usage: int = Field(default=0, description="Times fallback responses were used")
    user_satisfaction: Optional[float] = Field(None, description="Average user satisfaction rating")
    peak_usage_hour: Optional[int] = Field(None, description="Hour with highest usage (0-23)")

class ScrapingLogModel(BaseModel):
    """Model for scraping operation logs"""
    source_id: str = Field(..., description="ID of the source being scraped")
    operation_type: str = Field(..., description="Type of operation (startup, periodic, manual)")
    timestamp: datetime = Field(default_factory=datetime.now, description="When operation started")
    status: str = Field(..., description="Operation status (started, completed, failed)")
    pages_scraped: int = Field(default=0, description="Number of pages scraped")
    depth_reached: int = Field(default=0, description="Maximum depth reached")
    processing_time: float = Field(default=0.0, description="Time taken in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    database_updated: bool = Field(default=False, description="Whether knowledge database was updated")
    new_items_added: int = Field(default=0, description="New items added to knowledge database")

class DatabaseStatsModel(BaseModel):
    """Model for database statistics"""
    total_sources: int = Field(..., description="Total number of sources")
    total_pages_scraped: int = Field(..., description="Total pages scraped across all sources")
    total_knowledge_items: int = Field(..., description="Total items in knowledge database")
    knowledge_by_category: Dict[str, int] = Field(..., description="Items count by category")
    total_users: int = Field(..., description="Total unique users")
    total_chat_messages: int = Field(..., description="Total chat messages")
    average_response_time: float = Field(..., description="Average AI response time in ms")
    database_hit_rate: float = Field(..., description="Percentage of queries using knowledge database")
    last_database_update: datetime = Field(..., description="When knowledge database was last updated")
    scraping_frequency: str = Field(..., description="How often scraping occurs")
    total_storage_used: Optional[str] = Field(None, description="Total storage used by database")

# Database collection names
COLLECTIONS = {
    'scraped_data': 'scraped_data',
    'knowledge_database': 'knowledge_database', 
    'chat_history': 'chat_history',
    'user_sessions': 'user_sessions',
    'analytics': 'analytics',
    'scraping_logs': 'scraping_logs',
    'database_stats': 'database_stats'
}
