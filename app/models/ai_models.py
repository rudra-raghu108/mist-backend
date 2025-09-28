"""
AI Models and Training Data Models for SRM Guide Bot
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, 
    Float, JSON, ForeignKey, Enum, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped, mapped_column
import uuid
import enum

Base = declarative_base()


class ModelType(str, enum.Enum):
    """AI Model Types"""
    TRANSFORMER = "transformer"
    LSTM = "lstm"
    GRU = "gru"
    CNN = "cnn"
    CUSTOM = "custom"


class ModelStatus(str, enum.Enum):
    """Model Status"""
    TRAINING = "training"
    TRAINED = "trained"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ARCHIVED = "archived"


class TrainingStatus(str, enum.Enum):
    """Training Status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AIModel(Base):
    """AI Model Storage"""
    __tablename__ = "ai_models"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    model_type: Mapped[ModelType] = mapped_column(Enum(ModelType), nullable=False)
    status: Mapped[ModelStatus] = mapped_column(Enum(ModelStatus), default=ModelStatus.TRAINING)
    
    # Model files and metadata
    model_path: Mapped[Optional[str]] = mapped_column(String(500))  # Path to saved model
    config_path: Mapped[Optional[str]] = mapped_column(String(500))  # Path to model config
    tokenizer_path: Mapped[Optional[str]] = mapped_column(String(500))  # Path to tokenizer
    
    # Model specifications
    model_size: Mapped[Optional[int]] = mapped_column(Integer)  # Model size in MB
    parameters: Mapped[Optional[int]] = mapped_column(Integer)  # Number of parameters
    architecture: Mapped[Optional[dict]] = mapped_column(JSON)  # Model architecture details
    
    # Performance metrics
    accuracy: Mapped[Optional[float]] = mapped_column(Float)
    loss: Mapped[Optional[float]] = mapped_column(Float)
    validation_metrics: Mapped[Optional[dict]] = mapped_column(JSON)
    
    # Training info
    base_model: Mapped[Optional[str]] = mapped_column(String(255))  # Base model used for fine-tuning
    training_data_size: Mapped[Optional[int]] = mapped_column(Integer)
    training_epochs: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON)  # Model tags for categorization
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    training_sessions: Mapped[List["TrainingSession"]] = relationship("TrainingSession", back_populates="model", cascade="all, delete-orphan")
    deployments: Mapped[List["ModelDeployment"]] = relationship("ModelDeployment", back_populates="model", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_model_name', 'name'),
        Index('idx_model_type', 'model_type'),
        Index('idx_model_status', 'status'),
        Index('idx_model_created_at', 'created_at'),
    )


class TrainingSession(Base):
    """Training Session Records"""
    __tablename__ = "training_sessions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_models.id"), nullable=False)
    session_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[TrainingStatus] = mapped_column(Enum(TrainingStatus), default=TrainingStatus.PENDING)
    
    # Training configuration
    training_config: Mapped[dict] = mapped_column(JSON, nullable=False)  # Training hyperparameters
    data_config: Mapped[dict] = mapped_column(JSON, nullable=False)  # Data loading configuration
    
    # Training progress
    current_epoch: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    total_epochs: Mapped[int] = mapped_column(Integer, nullable=False)
    current_step: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    total_steps: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Training metrics
    training_loss: Mapped[Optional[float]] = mapped_column(Float)
    validation_loss: Mapped[Optional[float]] = mapped_column(Float)
    learning_rate: Mapped[Optional[float]] = mapped_column(Float)
    training_metrics: Mapped[Optional[dict]] = mapped_column(JSON)  # Detailed metrics
    
    # Logs and artifacts
    logs_path: Mapped[Optional[str]] = mapped_column(String(500))  # Path to training logs
    checkpoints_path: Mapped[Optional[str]] = mapped_column(String(500))  # Path to model checkpoints
    tensorboard_path: Mapped[Optional[str]] = mapped_column(String(500))  # Path to tensorboard logs
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    duration: Mapped[Optional[int]] = mapped_column(Integer)  # Duration in seconds
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    stack_trace: Mapped[Optional[str]] = mapped_column(Text)
    
    # Metadata
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    model: Mapped["AIModel"] = relationship("AIModel", back_populates="training_sessions")
    
    __table_args__ = (
        Index('idx_training_model_id', 'model_id'),
        Index('idx_training_status', 'status'),
        Index('idx_training_created_at', 'created_at'),
    )


class TrainingData(Base):
    """Training Data Storage"""
    __tablename__ = "training_data"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Data specifications
    data_type: Mapped[str] = mapped_column(String(100), nullable=False)  # text, conversation, qa, etc.
    format: Mapped[str] = mapped_column(String(50), nullable=False)  # json, csv, txt, etc.
    size: Mapped[Optional[int]] = mapped_column(Integer)  # Size in MB
    record_count: Mapped[Optional[int]] = mapped_column(Integer)  # Number of records
    
    # Data storage
    file_path: Mapped[Optional[str]] = mapped_column(String(500))  # Path to data file
    data_hash: Mapped[Optional[str]] = mapped_column(String(64))  # SHA256 hash of data
    
    # Data schema
    schema: Mapped[Optional[dict]] = mapped_column(JSON)  # Data structure definition
    sample_data: Mapped[Optional[dict]] = mapped_column(JSON)  # Sample records
    
    # Quality metrics
    quality_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-1 quality score
    validation_status: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON)
    source: Mapped[Optional[str]] = mapped_column(String(255))  # Data source
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_data_name', 'name'),
        Index('idx_data_type', 'data_type'),
        Index('idx_data_created_at', 'created_at'),
    )


class ModelDeployment(Base):
    """Model Deployment Records"""
    __tablename__ = "model_deployments"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id: Mapped[str] = mapped_column(String(36), ForeignKey("ai_models.id"), nullable=False)
    deployment_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Deployment configuration
    environment: Mapped[str] = mapped_column(String(100), nullable=False)  # dev, staging, prod
    endpoint_url: Mapped[Optional[str]] = mapped_column(String(500))
    api_key: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Resource allocation
    cpu_cores: Mapped[Optional[int]] = mapped_column(Integer)
    memory_gb: Mapped[Optional[int]] = mapped_column(Integer)
    gpu_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Status and health
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    health_status: Mapped[Optional[str]] = mapped_column(String(50))
    last_health_check: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Performance metrics
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_response_time: Mapped[Optional[float]] = mapped_column(Float)
    error_rate: Mapped[Optional[float]] = mapped_column(Float)
    
    # Metadata
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    model: Mapped["AIModel"] = relationship("AIModel", back_populates="deployments")
    
    __table_args__ = (
        Index('idx_deployment_model_id', 'model_id'),
        Index('idx_deployment_environment', 'environment'),
        Index('idx_deployment_active', 'is_active'),
    )


class InferenceLog(Base):
    """Model Inference Logs"""
    __tablename__ = "inference_logs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("ai_models.id"))
    deployment_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("model_deployments.id"))
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"))
    
    # Request details
    input_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Performance metrics
    response_time: Mapped[Optional[float]] = mapped_column(Float)  # Response time in seconds
    processing_time: Mapped[Optional[float]] = mapped_column(Float)  # Model processing time
    
    # Status and errors
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # success, error, timeout
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    # Request metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    request_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Timestamps
    request_timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    response_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    __table_args__ = (
        Index('idx_inference_model_id', 'model_id'),
        Index('idx_inference_user_id', 'user_id'),
        Index('idx_inference_status', 'status'),
        Index('idx_inference_timestamp', 'request_timestamp'),
    )
