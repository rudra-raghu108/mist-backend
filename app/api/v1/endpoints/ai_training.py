"""
AI Training and Model Management API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional, Any
import json
import asyncio
import logging
from datetime import datetime

from ....schemas.auth import User
from ....services.ai_database_service import AIDatabaseService
from ....services.langflow_service import LangflowService
from ....services.custom_ai_models import CustomAITrainer
from ....core.auth import get_current_user
from ....core.database import get_async_session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/models/create")
async def create_ai_model(
    model_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Create a new AI model"""
    try:
        async with AIDatabaseService() as db_service:
            model = await db_service.create_model(model_data, current_user.id)
            
            return {
                "success": True,
                "message": "AI model created successfully",
                "model": {
                    "id": model.id,
                    "name": model.name,
                    "type": model.model_type.value,
                    "status": model.status.value,
                    "created_at": model.created_at.isoformat()
                }
            }
    except Exception as e:
        logger.error(f"Error creating AI model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create AI model: {str(e)}")


@router.get("/models")
async def get_user_models(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get user's AI models"""
    try:
        async with AIDatabaseService() as db_service:
            models = await db_service.get_models_by_user(
                current_user.id, 
                ModelStatus(status) if status else None
            )
            
            return {
                "success": True,
                "models": [
                    {
                        "id": model.id,
                        "name": model.name,
                        "description": model.description,
                        "type": model.model_type.value,
                        "status": model.status.value,
                        "accuracy": model.accuracy,
                        "loss": model.loss,
                        "created_at": model.created_at.isoformat(),
                        "updated_at": model.updated_at.isoformat()
                    } for model in models
                ]
            }
    except Exception as e:
        logger.error(f"Error getting user models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")


@router.get("/models/{model_id}")
async def get_model_details(
    model_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific model"""
    try:
        async with AIDatabaseService() as db_service:
            model = await db_service.get_model(model_id)
            
            if not model:
                raise HTTPException(status_code=404, detail="Model not found")
            
            if model.created_by != current_user.id:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Get model statistics
            stats = await db_service.get_model_statistics(model_id)
            
            return {
                "success": True,
                "model": {
                    "id": model.id,
                    "name": model.name,
                    "description": model.description,
                    "type": model.model_type.value,
                    "status": model.status.value,
                    "architecture": model.architecture,
                    "base_model": model.base_model,
                    "accuracy": model.accuracy,
                    "loss": model.loss,
                    "validation_metrics": model.validation_metrics,
                    "training_data_size": model.training_data_size,
                    "training_epochs": model.training_epochs,
                    "tags": model.tags,
                    "created_at": model.created_at.isoformat(),
                    "updated_at": model.updated_at.isoformat()
                },
                "statistics": stats
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model details: {str(e)}")


@router.post("/models/{model_id}/train")
async def start_model_training(
    model_id: str,
    training_config: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Start training a model"""
    try:
        async with AIDatabaseService() as db_service:
            # Verify model exists and belongs to user
            model = await db_service.get_model(model_id)
            if not model:
                raise HTTPException(status_code=404, detail="Model not found")
            
            if model.created_by != current_user.id:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Create training session
            session_data = {
                "session_name": f"Training_{model.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "training_config": training_config,
                "data_config": training_config.get("data_config", {}),
                "total_epochs": training_config.get("num_epochs", 3)
            }
            
            training_session = await db_service.create_training_session(
                model_id, session_data, current_user.id
            )
            
            # Start training in background
            background_tasks.add_task(
                run_training_background,
                model_id,
                training_session.id,
                training_config,
                current_user.id
            )
            
            return {
                "success": True,
                "message": "Training started successfully",
                "training_session": {
                    "id": training_session.id,
                    "name": training_session.session_name,
                    "status": training_session.status.value,
                    "created_at": training_session.created_at.isoformat()
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting model training: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start training: {str(e)}")


@router.get("/models/{model_id}/training-sessions")
async def get_model_training_sessions(
    model_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get training sessions for a model"""
    try:
        async with AIDatabaseService() as db_service:
            # Verify model exists and belongs to user
            model = await db_service.get_model(model_id)
            if not model:
                raise HTTPException(status_code=404, detail="Model not found")
            
            if model.created_by != current_user.id:
                raise HTTPException(status_code=403, detail="Access denied")
            
            sessions = await db_service.get_training_sessions_by_model(model_id)
            
            return {
                "success": True,
                "training_sessions": [
                    {
                        "id": session.id,
                        "name": session.session_name,
                        "status": session.status.value,
                        "current_epoch": session.current_epoch,
                        "total_epochs": session.total_epochs,
                        "training_loss": session.training_loss,
                        "validation_loss": session.validation_loss,
                        "started_at": session.started_at.isoformat() if session.started_at else None,
                        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
                        "duration": session.duration,
                        "created_at": session.created_at.isoformat()
                    } for session in sessions
                ]
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting training sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get training sessions: {str(e)}")


@router.post("/models/{model_id}/deploy")
async def deploy_model(
    model_id: str,
    deployment_config: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Deploy a trained model"""
    try:
        async with AIDatabaseService() as db_service:
            # Verify model exists and belongs to user
            model = await db_service.get_model(model_id)
            if not model:
                raise HTTPException(status_code=404, detail="Model not found")
            
            if model.created_by != current_user.id:
                raise HTTPException(status_code=403, detail="Access denied")
            
            if model.status != ModelStatus.TRAINED:
                raise HTTPException(status_code=400, detail="Model must be trained before deployment")
            
            # Create deployment
            deployment_data = {
                "model_id": model_id,
                "deployment_name": deployment_config.get("deployment_name", f"Deployment_{model.name}"),
                "environment": deployment_config.get("environment", "dev"),
                "endpoint_url": deployment_config.get("endpoint_url"),
                "cpu_cores": deployment_config.get("cpu_cores", 2),
                "memory_gb": deployment_config.get("memory_gb", 4),
                "gpu_enabled": deployment_config.get("gpu_enabled", False)
            }
            
            deployment = await db_service.create_model_deployment(deployment_data, current_user.id)
            
            # Update model status
            await db_service.update_model(model_id, {"status": ModelStatus.DEPLOYED})
            
            return {
                "success": True,
                "message": "Model deployed successfully",
                "deployment": {
                    "id": deployment.id,
                    "name": deployment.deployment_name,
                    "environment": deployment.environment,
                    "endpoint_url": deployment.endpoint_url,
                    "status": "active",
                    "created_at": deployment.created_at.isoformat()
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deploying model: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to deploy model: {str(e)}")


@router.post("/models/{model_id}/predict")
async def predict_with_model(
    model_id: str,
    prediction_request: Dict[str, Any],
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Make predictions using a deployed model"""
    try:
        async with AIDatabaseService() as db_service:
            # Verify model exists and belongs to user
            model = await db_service.get_model(model_id)
            if not model:
                raise HTTPException(status_code=404, detail="Model not found")
            
            if model.created_by != current_user.id:
                raise HTTPException(status_code=403, detail="Access denied")
            
            if model.status != ModelStatus.DEPLOYED:
                raise HTTPException(status_code=400, detail="Model must be deployed for inference")
            
            # Get active deployment
            deployments = await db_service.get_active_deployments()
            model_deployment = next((d for d in deployments if d.model_id == model_id), None)
            
            if not model_deployment:
                raise HTTPException(status_code=400, detail="No active deployment found for model")
            
            # Load model and make prediction
            start_time = datetime.utcnow()
            
            try:
                # Load the trained model
                model_config = {
                    "model_type": model.model_type.value,
                    "architecture": model.architecture or {}
                }
                
                trainer = CustomAITrainer(model_config)
                loaded_model = trainer.load_pretrained_model(
                    model.model_path, 
                    model.model_type.value
                )
                
                # Make prediction
                input_text = prediction_request.get("input_text", "")
                if not input_text:
                    raise HTTPException(status_code=400, detail="Input text is required")
                
                predictions = trainer.predict([input_text])
                
                end_time = datetime.utcnow()
                response_time = (end_time - start_time).total_seconds()
                
                # Log inference
                inference_data = {
                    "model_id": model_id,
                    "deployment_id": model_deployment.id,
                    "user_id": current_user.id,
                    "input_data": {"input_text": input_text},
                    "output_data": {"predictions": predictions},
                    "status": "success",
                    "response_time": response_time,
                    "ip_address": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                    "request_id": prediction_request.get("request_id")
                }
                
                await db_service.log_inference(inference_data)
                
                return {
                    "success": True,
                    "predictions": predictions,
                    "model_info": {
                        "id": model.id,
                        "name": model.name,
                        "type": model.model_type.value
                    },
                    "deployment_info": {
                        "id": model_deployment.id,
                        "name": model_deployment.deployment_name
                    },
                    "response_time": response_time,
                    "timestamp": end_time.isoformat()
                }
                
            except Exception as e:
                # Log failed inference
                end_time = datetime.utcnow()
                response_time = (end_time - start_time).total_seconds()
                
                inference_data = {
                    "model_id": model_id,
                    "deployment_id": model_deployment.id,
                    "user_id": current_user.id,
                    "input_data": {"input_text": prediction_request.get("input_text", "")},
                    "status": "error",
                    "error_message": str(e),
                    "response_time": response_time,
                    "ip_address": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                    "request_id": prediction_request.get("request_id")
                }
                
                await db_service.log_inference(inference_data)
                raise
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error making prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to make prediction: {str(e)}")


@router.post("/training-data/upload")
async def upload_training_data(
    data_info: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Upload training data"""
    try:
        async with AIDatabaseService() as db_service:
            training_data = await db_service.create_training_data(data_info, current_user.id)
            
            return {
                "success": True,
                "message": "Training data uploaded successfully",
                "data": {
                    "id": training_data.id,
                    "name": training_data.name,
                    "type": training_data.data_type,
                    "format": training_data.format,
                    "size": training_data.size,
                    "record_count": training_data.record_count,
                    "created_at": training_data.created_at.isoformat()
                }
            }
    except Exception as e:
        logger.error(f"Error uploading training data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload training data: {str(e)}")


@router.get("/training-data")
async def get_training_data(
    data_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get training data"""
    try:
        async with AIDatabaseService() as db_service:
            if data_type:
                data_list = await db_service.get_training_data_by_type(data_type)
            else:
                # Get all training data (you might want to add pagination)
                data_list = []
            
            return {
                "success": True,
                "training_data": [
                    {
                        "id": data.id,
                        "name": data.name,
                        "description": data.description,
                        "type": data.data_type,
                        "format": data.format,
                        "size": data.size,
                        "record_count": data.record_count,
                        "quality_score": data.quality_score,
                        "created_at": data.created_at.isoformat()
                    } for data in data_list
                ]
            }
    except Exception as e:
        logger.error(f"Error getting training data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get training data: {str(e)}")


@router.get("/workflows")
async def get_workflows(current_user: User = Depends(get_current_user)):
    """Get available Langflow workflows"""
    try:
        langflow_service = LangflowService()
        workflows = await langflow_service.list_workflows()
        
        return {
            "success": True,
            "workflows": workflows
        }
    except Exception as e:
        logger.error(f"Error getting workflows: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflows: {str(e)}")


@router.post("/workflows/create-training")
async def create_training_workflow(
    model_config: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Create a training workflow"""
    try:
        langflow_service = LangflowService()
        workflow_path = await langflow_service.create_training_workflow(model_config)
        
        return {
            "success": True,
            "message": "Training workflow created successfully",
            "workflow_path": workflow_path
        }
    except Exception as e:
        logger.error(f"Error creating training workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


@router.post("/workflows/{workflow_name}/execute")
async def execute_workflow(
    workflow_name: str,
    input_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Execute a workflow"""
    try:
        langflow_service = LangflowService()
        result = await langflow_service.execute_workflow(workflow_name, input_data)
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}")


@router.get("/analytics/usage")
async def get_user_ai_usage(current_user: User = Depends(get_current_user)):
    """Get user's AI usage statistics"""
    try:
        async with AIDatabaseService() as db_service:
            usage_stats = await db_service.get_user_ai_usage(current_user.id)
            
            return {
                "success": True,
                "usage_statistics": usage_stats
            }
    except Exception as e:
        logger.error(f"Error getting user AI usage: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get usage statistics: {str(e)}")


# Background task for training
async def run_training_background(
    model_id: str,
    session_id: str,
    training_config: Dict[str, Any],
    user_id: str
):
    """Background task to run model training"""
    try:
        async with AIDatabaseService() as db_service:
            # Start training session
            await db_service.start_training_session(session_id)
            
            # Get model details
            model = await db_service.get_model(model_id)
            if not model:
                logger.error(f"Model {model_id} not found for training")
                return
            
            # Get training data from database
            # This is a simplified example - you'd need to implement data loading logic
            training_data = []  # Load from your database
            validation_data = []  # Load from your database
            
            # Extract texts and labels
            train_texts = [item["text"] for item in training_data]
            train_labels = [item["label"] for item in training_data]
            
            val_texts = None
            val_labels = None
            if validation_data:
                val_texts = [item["text"] for item in validation_data]
                val_labels = [item["label"] for item in validation_data]
            
            # Create trainer and train model
            model_config = {
                "model_type": model.model_type.value,
                "architecture": model.architecture or {}
            }
            
            trainer = CustomAITrainer(model_config)
            loaded_model = trainer.create_model(model.model_type.value)
            
            # Train the model
            training_history = trainer.train(
                train_texts=train_texts,
                train_labels=train_labels,
                val_texts=val_texts,
                val_labels=val_labels,
                training_args=training_config
            )
            
            # Save the trained model
            save_path = f"models/{model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pth"
            trainer.save_model(save_path)
            
            # Update model with results
            update_data = {
                "status": ModelStatus.TRAINED,
                "model_path": save_path,
                "config_path": save_path.replace('.pth', '_config.json'),
                "tokenizer_path": save_path.replace('.pth', '_tokenizer'),
                "accuracy": training_history.get("train_loss", 0),  # You'd calculate actual accuracy
                "loss": training_history.get("train_loss", 0),
                "training_data_size": len(training_data)
            }
            
            await db_service.update_model(model_id, update_data)
            
            # Complete training session
            session_results = {
                "final_loss": training_history.get("train_loss", 0),
                "validation_loss": training_history.get("val_loss", 0),
                "training_metrics": training_history
            }
            
            await db_service.complete_training_session(session_id, session_results)
            
            logger.info(f"Training completed successfully for model {model_id}")
            
    except Exception as e:
        logger.error(f"Error in background training: {e}")
        
        # Update training session as failed
        try:
            async with AIDatabaseService() as db_service:
                await db_service.update_training_session(session_id, {
                    "status": TrainingStatus.FAILED,
                    "error_message": str(e),
                    "stack_trace": str(e)
                })
        except Exception as update_error:
            logger.error(f"Error updating failed training session: {update_error}")


# Import the missing classes
from ....models.ai_models import ModelStatus, TrainingStatus
