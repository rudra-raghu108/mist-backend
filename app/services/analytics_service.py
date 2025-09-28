"""
Analytics service for SRM Guide Bot
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.database import UserAnalytics, User

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Analytics service for tracking user interactions"""
    
    def __init__(self):
        self.db = None
    
    async def track_message_interaction(
        self, 
        user_id: str, 
        message_type: str, 
        tokens_used: int = 0,
        category: str = None,
        metadata: Dict[str, Any] = None
    ):
        """Track message interaction"""
        try:
            db = next(get_db())
            
            analytics = UserAnalytics(
                user_id=user_id,
                event_type="message_interaction",
                event_data={
                    "message_type": message_type,
                    "tokens_used": tokens_used,
                    "category": category,
                    "metadata": metadata or {}
                },
                timestamp=datetime.utcnow()
            )
            
            db.add(analytics)
            db.commit()
            
            logger.info(f"Tracked message interaction for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error tracking message interaction: {str(e)}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
    
    async def track_user_login(self, user_id: str, ip_address: str = None, user_agent: str = None):
        """Track user login"""
        try:
            db = next(get_db())
            
            analytics = UserAnalytics(
                user_id=user_id,
                event_type="user_login",
                event_data={
                    "ip_address": ip_address,
                    "user_agent": user_agent
                },
                timestamp=datetime.utcnow()
            )
            
            db.add(analytics)
            db.commit()
            
            logger.info(f"Tracked login for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error tracking user login: {str(e)}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
    
    async def track_chat_created(self, user_id: str, chat_id: str):
        """Track chat creation"""
        try:
            db = next(get_db())
            
            analytics = UserAnalytics(
                user_id=user_id,
                event_type="chat_created",
                event_data={
                    "chat_id": chat_id
                },
                timestamp=datetime.utcnow()
            )
            
            db.add(analytics)
            db.commit()
            
            logger.info(f"Tracked chat creation for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error tracking chat creation: {str(e)}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
    
    async def track_ai_response_time(self, user_id: str, response_time: float, model_used: str):
        """Track AI response time"""
        try:
            db = next(get_db())
            
            analytics = UserAnalytics(
                user_id=user_id,
                event_type="ai_response_time",
                event_data={
                    "response_time": response_time,
                    "model_used": model_used
                },
                timestamp=datetime.utcnow()
            )
            
            db.add(analytics)
            db.commit()
            
            logger.info(f"Tracked AI response time for user {user_id}: {response_time}s")
            
        except Exception as e:
            logger.error(f"Error tracking AI response time: {str(e)}")
            if db:
                db.rollback()
        finally:
            if db:
                db.close()
    
    async def get_user_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user analytics for the last N days"""
        try:
            db = next(get_db())
            
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            analytics = db.query(UserAnalytics).filter(
                UserAnalytics.user_id == user_id,
                UserAnalytics.timestamp >= cutoff_date
            ).all()
            
            # Process analytics data
            total_messages = len([a for a in analytics if a.event_type == "message_interaction"])
            total_tokens = sum([
                a.event_data.get("tokens_used", 0) 
                for a in analytics 
                if a.event_type == "message_interaction"
            ])
            
            avg_response_time = 0
            response_times = [
                a.event_data.get("response_time", 0) 
                for a in analytics 
                if a.event_type == "ai_response_time"
            ]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
            
            return {
                "total_messages": total_messages,
                "total_tokens": total_tokens,
                "average_response_time": avg_response_time,
                "total_logins": len([a for a in analytics if a.event_type == "user_login"]),
                "total_chats": len([a for a in analytics if a.event_type == "chat_created"]),
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting user analytics: {str(e)}")
            return {}
        finally:
            if db:
                db.close()
    
    async def get_system_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get system-wide analytics"""
        try:
            db = next(get_db())
            
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            analytics = db.query(UserAnalytics).filter(
                UserAnalytics.timestamp >= cutoff_date
            ).all()
            
            # Process system analytics
            total_users = db.query(User).filter(
                User.created_at >= cutoff_date
            ).count()
            
            total_messages = len([a for a in analytics if a.event_type == "message_interaction"])
            total_tokens = sum([
                a.event_data.get("tokens_used", 0) 
                for a in analytics 
                if a.event_type == "message_interaction"
            ])
            
            return {
                "total_users": total_users,
                "total_messages": total_messages,
                "total_tokens": total_tokens,
                "total_logins": len([a for a in analytics if a.event_type == "user_login"]),
                "total_chats": len([a for a in analytics if a.event_type == "chat_created"]),
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error getting system analytics: {str(e)}")
            return {}
        finally:
            if db:
                db.close()


# Create singleton instance
analytics_service = AnalyticsService()
