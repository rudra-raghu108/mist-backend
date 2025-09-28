"""
AI Database Service for SRM Guide Bot
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.orm import selectinload

from ..models.ai_models import (
    AIModel, TrainingSession, TrainingData, ModelDeployment, InferenceLog,
    ModelType, ModelStatus, TrainingStatus
)
from ..models.database import User
from ..core.database import get_async_session

logger = logging.getLogger(__name__)


class AIDatabaseService:
    """
    Service for managing AI models and training data in the database
    """
    
    def __init__(self):
        self.session: Optional[AsyncSession] = None
    
    async def __aenter__(self):
        self.session = await get_async_session().__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
    
    # AI Model Management
    async def create_model(self, model_data: Dict[str, Any], user_id: str) -> AIModel:
        """Create a new AI model record"""
        try:
            model = AIModel(
                name=model_data["name"],
                description=model_data.get("description", ""),
                model_type=ModelType(model_data["model_type"]),
                status=ModelStatus.TRAINING,
                architecture=model_data.get("architecture", {}),
                base_model=model_data.get("base_model"),
                training_data_size=model_data.get("training_data_size"),
                training_epochs=model_data.get("training_epochs"),
                tags=model_data.get("tags", []),
                created_by=user_id
            )
            
            self.session.add(model)
            await self.session.commit()
            await self.session.refresh(model)
            
            logger.info(f"Created AI model: {model.name} (ID: {model.id})")
            return model
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating AI model: {e}")
            raise
    
    async def get_model(self, model_id: str) -> Optional[AIModel]:
        """Get an AI model by ID"""
        try:
            result = await self.session.execute(
                select(AIModel).where(AIModel.id == model_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting AI model: {e}")
            return None
    
    async def get_models_by_user(self, user_id: str, status: Optional[ModelStatus] = None) -> List[AIModel]:
        """Get AI models by user ID and optionally filter by status"""
        try:
            query = select(AIModel).where(AIModel.created_by == user_id)
            
            if status:
                query = query.where(AIModel.status == status)
            
            query = query.order_by(AIModel.created_at.desc())
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting models by user: {e}")
            return []
    
    async def update_model(self, model_id: str, update_data: Dict[str, Any]) -> Optional[AIModel]:
        """Update an AI model"""
        try:
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            update_data["updated_at"] = datetime.utcnow()
            
            await self.session.execute(
                update(AIModel)
                .where(AIModel.id == model_id)
                .values(**update_data)
            )
            
            await self.session.commit()
            
            # Return updated model
            return await self.get_model(model_id)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating AI model: {e}")
            return None
    
    async def delete_model(self, model_id: str) -> bool:
        """Delete an AI model"""
        try:
            await self.session.execute(
                delete(AIModel).where(AIModel.id == model_id)
            )
            await self.session.commit()
            
            logger.info(f"Deleted AI model: {model_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting AI model: {e}")
            return False
    
    # Training Session Management
    async def create_training_session(
        self, 
        model_id: str, 
        session_data: Dict[str, Any], 
        user_id: str
    ) -> TrainingSession:
        """Create a new training session"""
        try:
            session = TrainingSession(
                model_id=model_id,
                session_name=session_data["session_name"],
                status=TrainingStatus.PENDING,
                training_config=session_data["training_config"],
                data_config=session_data["data_config"],
                total_epochs=session_data["total_epochs"],
                created_by=user_id
            )
            
            self.session.add(session)
            await self.session.commit()
            await self.session.refresh(session)
            
            logger.info(f"Created training session: {session.session_name} (ID: {session.id})")
            return session
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating training session: {e}")
            raise
    
    async def get_training_session(self, session_id: str) -> Optional[TrainingSession]:
        """Get a training session by ID"""
        try:
            result = await self.session.execute(
                select(TrainingSession)
                .options(selectinload(TrainingSession.model))
                .where(TrainingSession.id == session_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting training session: {e}")
            return None
    
    async def get_training_sessions_by_model(self, model_id: str) -> List[TrainingSession]:
        """Get all training sessions for a model"""
        try:
            result = await self.session.execute(
                select(TrainingSession)
                .where(TrainingSession.model_id == model_id)
                .order_by(TrainingSession.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting training sessions by model: {e}")
            return []
    
    async def update_training_session(
        self, 
        session_id: str, 
        update_data: Dict[str, Any]
    ) -> Optional[TrainingSession]:
        """Update a training session"""
        try:
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            update_data["updated_at"] = datetime.utcnow()
            
            await self.session.execute(
                update(TrainingSession)
                .where(TrainingSession.id == session_id)
                .values(**update_data)
            )
            
            await self.session.commit()
            
            # Return updated session
            return await self.get_training_session(session_id)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating training session: {e}")
            return None
    
    async def start_training_session(self, session_id: str) -> bool:
        """Start a training session"""
        try:
            update_data = {
                "status": TrainingStatus.RUNNING,
                "started_at": datetime.utcnow()
            }
            
            await self.update_training_session(session_id, update_data)
            
            # Update model status to training
            session = await self.get_training_session(session_id)
            if session:
                await self.update_model(session.model_id, {"status": ModelStatus.TRAINING})
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting training session: {e}")
            return False
    
    async def complete_training_session(
        self, 
        session_id: str, 
        results: Dict[str, Any]
    ) -> bool:
        """Complete a training session"""
        try:
            update_data = {
                "status": TrainingStatus.COMPLETED,
                "completed_at": datetime.utcnow(),
                "training_metrics": results.get("training_metrics", {}),
                "training_loss": results.get("final_loss"),
                "validation_loss": results.get("validation_loss")
            }
            
            # Calculate duration
            session = await self.get_training_session(session_id)
            if session and session.started_at:
                duration = int((datetime.utcnow() - session.started_at).total_seconds())
                update_data["duration"] = duration
            
            await self.update_training_session(session_id, update_data)
            
            # Update model status to trained
            if session:
                await self.update_model(session.model_id, {"status": ModelStatus.TRAINED})
            
            return True
            
        except Exception as e:
            logger.error(f"Error completing training session: {e}")
            return False
    
    # Training Data Management
    async def create_training_data(
        self, 
        data_info: Dict[str, Any], 
        user_id: str
    ) -> TrainingData:
        """Create a new training data record"""
        try:
            training_data = TrainingData(
                name=data_info["name"],
                description=data_info.get("description", ""),
                data_type=data_info["data_type"],
                format=data_info["format"],
                size=data_info.get("size"),
                record_count=data_info.get("record_count"),
                file_path=data_info.get("file_path"),
                data_hash=data_info.get("data_hash"),
                schema=data_info.get("schema"),
                sample_data=data_info.get("sample_data"),
                quality_score=data_info.get("quality_score"),
                validation_status=data_info.get("validation_status"),
                tags=data_info.get("tags", []),
                source=data_info.get("source"),
                created_by=user_id
            )
            
            self.session.add(training_data)
            await self.session.commit()
            await self.session.refresh(training_data)
            
            logger.info(f"Created training data: {training_data.name} (ID: {training_data.id})")
            return training_data
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating training data: {e}")
            raise
    
    async def get_training_data(self, data_id: str) -> Optional[TrainingData]:
        """Get training data by ID"""
        try:
            result = await self.session.execute(
                select(TrainingData).where(TrainingData.id == data_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return None
    
    async def get_training_data_by_type(self, data_type: str) -> List[TrainingData]:
        """Get training data by type"""
        try:
            result = await self.session.execute(
                select(TrainingData)
                .where(TrainingData.data_type == data_type)
                .order_by(TrainingData.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting training data by type: {e}")
            return []
    
    async def update_training_data(
        self, 
        data_id: str, 
        update_data: Dict[str, Any]
    ) -> Optional[TrainingData]:
        """Update training data"""
        try:
            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}
            update_data["updated_at"] = datetime.utcnow()
            
            await self.session.execute(
                update(TrainingData)
                .where(TrainingData.id == data_id)
                .values(**update_data)
            )
            
            await self.session.commit()
            
            # Return updated data
            return await self.get_training_data(data_id)
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating training data: {e}")
            return None
    
    # Model Deployment Management
    async def create_model_deployment(
        self, 
        deployment_data: Dict[str, Any], 
        user_id: str
    ) -> ModelDeployment:
        """Create a new model deployment"""
        try:
            deployment = ModelDeployment(
                model_id=deployment_data["model_id"],
                deployment_name=deployment_data["deployment_name"],
                environment=deployment_data["environment"],
                endpoint_url=deployment_data.get("endpoint_url"),
                api_key=deployment_data.get("api_key"),
                cpu_cores=deployment_data.get("cpu_cores"),
                memory_gb=deployment_data.get("memory_gb"),
                gpu_enabled=deployment_data.get("gpu_enabled", False),
                created_by=user_id
            )
            
            self.session.add(deployment)
            await self.session.commit()
            await self.session.refresh(deployment)
            
            logger.info(f"Created model deployment: {deployment.deployment_name} (ID: {deployment.id})")
            return deployment
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating model deployment: {e}")
            raise
    
    async def get_model_deployment(self, deployment_id: str) -> Optional[ModelDeployment]:
        """Get a model deployment by ID"""
        try:
            result = await self.session.execute(
                select(ModelDeployment)
                .options(selectinload(ModelDeployment.model))
                .where(ModelDeployment.id == deployment_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting model deployment: {e}")
            return None
    
    async def get_active_deployments(self) -> List[ModelDeployment]:
        """Get all active model deployments"""
        try:
            result = await self.session.execute(
                select(ModelDeployment)
                .options(selectinload(ModelDeployment.model))
                .where(ModelDeployment.is_active == True)
                .order_by(ModelDeployment.created_at.desc())
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting active deployments: {e}")
            return []
    
    async def update_deployment_status(
        self, 
        deployment_id: str, 
        status: str, 
        health_status: Optional[str] = None
    ) -> bool:
        """Update deployment status and health"""
        try:
            update_data = {
                "health_status": health_status,
                "last_health_check": datetime.utcnow()
            }
            
            if status == "active":
                update_data["is_active"] = True
            elif status == "inactive":
                update_data["is_active"] = False
            
            await self.session.execute(
                update(ModelDeployment)
                .where(ModelDeployment.id == deployment_id)
                .values(**update_data)
            )
            
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating deployment status: {e}")
            return False
    
    # Inference Logging
    async def log_inference(
        self, 
        inference_data: Dict[str, Any]
    ) -> InferenceLog:
        """Log an inference request"""
        try:
            inference_log = InferenceLog(
                model_id=inference_data.get("model_id"),
                deployment_id=inference_data.get("deployment_id"),
                user_id=inference_data.get("user_id"),
                input_data=inference_data["input_data"],
                output_data=inference_data.get("output_data"),
                input_tokens=inference_data.get("input_tokens"),
                output_tokens=inference_data.get("output_tokens"),
                response_time=inference_data.get("response_time"),
                processing_time=inference_data.get("processing_time"),
                status=inference_data["status"],
                error_message=inference_data.get("error_message"),
                ip_address=inference_data.get("ip_address"),
                user_agent=inference_data.get("user_agent"),
                request_id=inference_data.get("request_id"),
                response_timestamp=datetime.utcnow()
            )
            
            self.session.add(inference_log)
            await self.session.commit()
            await self.session.refresh(inference_log)
            
            return inference_log
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error logging inference: {e}")
            raise
    
    async def get_inference_logs(
        self, 
        model_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[InferenceLog]:
        """Get inference logs with optional filtering"""
        try:
            query = select(InferenceLog).order_by(InferenceLog.request_timestamp.desc())
            
            if model_id:
                query = query.where(InferenceLog.model_id == model_id)
            
            if user_id:
                query = query.where(InferenceLog.user_id == user_id)
            
            query = query.limit(limit)
            
            result = await self.session.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting inference logs: {e}")
            return []
    
    # Analytics and Statistics
    async def get_model_statistics(self, model_id: str) -> Dict[str, Any]:
        """Get comprehensive statistics for a model"""
        try:
            # Get model info
            model = await self.get_model(model_id)
            if not model:
                return {}
            
            # Get training sessions
            training_sessions = await self.get_training_sessions_by_model(model_id)
            
            # Get deployments
            deployments = await self.session.execute(
                select(ModelDeployment).where(ModelDeployment.model_id == model_id)
            )
            deployments = deployments.scalars().all()
            
            # Get inference logs
            inference_logs = await self.get_inference_logs(model_id=model_id, limit=1000)
            
            # Calculate statistics
            total_inferences = len(inference_logs)
            successful_inferences = len([log for log in inference_logs if log.status == "success"])
            error_rate = (total_inferences - successful_inferences) / total_inferences if total_inferences > 0 else 0
            
            avg_response_time = 0
            if successful_inferences > 0:
                response_times = [log.response_time for log in inference_logs if log.response_time]
                avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            return {
                "model_info": {
                    "id": model.id,
                    "name": model.name,
                    "type": model.model_type.value,
                    "status": model.status.value,
                    "created_at": model.created_at.isoformat(),
                    "accuracy": model.accuracy,
                    "loss": model.loss
                },
                "training_stats": {
                    "total_sessions": len(training_sessions),
                    "completed_sessions": len([s for s in training_sessions if s.status == TrainingStatus.COMPLETED]),
                    "failed_sessions": len([s for s in training_sessions if s.status == TrainingStatus.FAILED]),
                    "total_epochs": sum([s.total_epochs for s in training_sessions if s.total_epochs])
                },
                "deployment_stats": {
                    "total_deployments": len(deployments),
                    "active_deployments": len([d for d in deployments if d.is_active])
                },
                "inference_stats": {
                    "total_inferences": total_inferences,
                    "successful_inferences": successful_inferences,
                    "error_rate": error_rate,
                    "avg_response_time": avg_response_time
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting model statistics: {e}")
            return {}
    
    async def get_user_ai_usage(self, user_id: str) -> Dict[str, Any]:
        """Get AI usage statistics for a user"""
        try:
            # Get user's models
            models = await self.get_models_by_user(user_id)
            
            # Get user's inference logs
            inference_logs = await self.get_inference_logs(user_id=user_id, limit=10000)
            
            # Calculate usage statistics
            total_models = len(models)
            trained_models = len([m for m in models if m.status == ModelStatus.TRAINED])
            deployed_models = len([m for m in models if m.status == ModelStatus.DEPLOYED])
            
            total_inferences = len(inference_logs)
            total_tokens = sum([log.input_tokens or 0 for log in inference_logs])
            
            # Get recent activity
            recent_models = sorted(models, key=lambda x: x.updated_at, reverse=True)[:5]
            recent_inferences = sorted(inference_logs, key=lambda x: x.request_timestamp, reverse=True)[:10]
            
            return {
                "summary": {
                    "total_models": total_models,
                    "trained_models": trained_models,
                    "deployed_models": deployed_models,
                    "total_inferences": total_inferences,
                    "total_tokens": total_tokens
                },
                "recent_models": [
                    {
                        "id": m.id,
                        "name": m.name,
                        "type": m.model_type.value,
                        "status": m.status.value,
                        "updated_at": m.updated_at.isoformat()
                    } for m in recent_models
                ],
                "recent_inferences": [
                    {
                        "id": log.id,
                        "model_id": log.model_id,
                        "status": log.status,
                        "response_time": log.response_time,
                        "timestamp": log.request_timestamp.isoformat()
                    } for log in recent_inferences
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting user AI usage: {e}")
            return {}
