"""
Database models for SRM Guide Bot
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    Float, JSON, ForeignKey, Enum, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    """User roles"""
    STUDENT = "student"
    FACULTY = "faculty"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class Gender(str, enum.Enum):
    """Gender options"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class MessageRole(str, enum.Enum):
    """Message roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class FeedbackType(str, enum.Enum):
    """Feedback types"""
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    GENERAL = "general"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"


class NotificationType(str, enum.Enum):
    """Notification types"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SYSTEM = "system"


class PaymentStatus(str, enum.Enum):
    """Payment statuses"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class SubscriptionStatus(str, enum.Enum):
    """Subscription statuses"""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIAL = "trial"


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    full_name: Mapped[Optional[str]] = mapped_column(String(200))
    avatar: Mapped[Optional[str]] = mapped_column(String(500))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime)
    gender: Mapped[Optional[Gender]] = mapped_column(Enum(Gender))
    campus: Mapped[Optional[str]] = mapped_column(String(100))  # SRM campus preference
    focus: Mapped[Optional[str]] = mapped_column(String(100))   # Academic focus area
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.STUDENT)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    login_count: Mapped[int] = mapped_column(Integer, default=0)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(500))
    email_verification_token: Mapped[Optional[str]] = mapped_column(String(255))
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(255))
    password_reset_expires: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    chats: Mapped[List["Chat"]] = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="user", cascade="all, delete-orphan")
    analytics: Mapped[List["UserAnalytics"]] = relationship("UserAnalytics", back_populates="user", cascade="all, delete-orphan")
    feedback: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    subscriptions: Mapped[List["Subscription"]] = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_username', 'username'),
        Index('idx_user_google_id', 'google_id'),
        Index('idx_user_campus', 'campus'),
        Index('idx_user_role', 'role'),
        Index('idx_user_created_at', 'created_at'),
    )


class Chat(Base):
    """Chat model"""
    __tablename__ = "chats"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[Optional[str]] = mapped_column(String(255))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="chats")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_chat_user_id', 'user_id'),
        Index('idx_chat_created_at', 'created_at'),
        Index('idx_chat_active', 'is_active'),
    )


class Message(Base):
    """Message model"""
    __tablename__ = "messages"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole), nullable=False)
    chat_id: Mapped[str] = mapped_column(String(36), ForeignKey("chats.id"), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"))
    metadata: Mapped[Optional[dict]] = mapped_column(JSON)  # Store additional data like tokens used, model used, etc.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="messages")
    
    __table_args__ = (
        Index('idx_message_chat_id', 'chat_id'),
        Index('idx_message_user_id', 'user_id'),
        Index('idx_message_role', 'role'),
        Index('idx_message_created_at', 'created_at'),
    )


class UserAnalytics(Base):
    """User analytics model"""
    __tablename__ = "user_analytics"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    messages_sent: Mapped[int] = mapped_column(Integer, default=0)
    messages_received: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    session_duration: Mapped[Optional[int]] = mapped_column(Integer)  # in seconds
    features_used: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))  # Array of features used
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="analytics")
    
    __table_args__ = (
        Index('idx_analytics_user_id', 'user_id'),
        Index('idx_analytics_date', 'date'),
        Index('idx_analytics_created_at', 'created_at'),
    )


class Feedback(Base):
    """Feedback model"""
    __tablename__ = "feedback"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    type: Mapped[FeedbackType] = mapped_column(Enum(FeedbackType), nullable=False)
    rating: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5 rating
    comment: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(100))  # e.g., "admissions", "courses", "general"
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="feedback")
    
    __table_args__ = (
        Index('idx_feedback_user_id', 'user_id'),
        Index('idx_feedback_type', 'type'),
        Index('idx_feedback_category', 'category'),
        Index('idx_feedback_resolved', 'is_resolved'),
        Index('idx_feedback_created_at', 'created_at'),
    )


class Notification(Base):
    """Notification model"""
    __tablename__ = "notifications"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")
    
    __table_args__ = (
        Index('idx_notification_user_id', 'user_id'),
        Index('idx_notification_type', 'type'),
        Index('idx_notification_read', 'is_read'),
        Index('idx_notification_created_at', 'created_at'),
    )


class Session(Base):
    """Session model"""
    __tablename__ = "sessions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")
    
    __table_args__ = (
        Index('idx_session_user_id', 'user_id'),
        Index('idx_session_token', 'token'),
        Index('idx_session_expires_at', 'expires_at'),
        Index('idx_session_active', 'is_active'),
    )


class Payment(Base):
    """Payment model"""
    __tablename__ = "payments"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_method: Mapped[Optional[str]] = mapped_column(String(100))
    stripe_payment_id: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(500))
    metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="payments")
    
    __table_args__ = (
        Index('idx_payment_user_id', 'user_id'),
        Index('idx_payment_status', 'status'),
        Index('idx_payment_stripe_id', 'stripe_payment_id'),
        Index('idx_payment_created_at', 'created_at'),
    )


class Subscription(Base):
    """Subscription model"""
    __tablename__ = "subscriptions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    plan_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    current_period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255))
    metadata: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscriptions")
    
    __table_args__ = (
        Index('idx_subscription_user_id', 'user_id'),
        Index('idx_subscription_status', 'status'),
        Index('idx_subscription_stripe_id', 'stripe_subscription_id'),
        Index('idx_subscription_period_end', 'current_period_end'),
    )


class SystemConfig(Base):
    """System configuration model"""
    __tablename__ = "system_configs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_config_key', 'key'),
        Index('idx_config_active', 'is_active'),
    )


class AuditLog(Base):
    """Audit log model"""
    __tablename__ = "audit_logs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource: Mapped[Optional[str]] = mapped_column(String(100))
    resource_id: Mapped[Optional[str]] = mapped_column(String(36))
    details: Mapped[Optional[dict]] = mapped_column(JSON)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_audit_user_id', 'user_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_resource', 'resource'),
        Index('idx_audit_created_at', 'created_at'),
    )
