"""
Langflow Integration Service for SRM Guide Bot
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import asyncio
import subprocess
import requests
from pathlib import Path

logger = logging.getLogger(__name__)


class LangflowService:
    """
    Service for managing Langflow workflows and AI training pipelines
    """
    
    def __init__(self, base_url: str = "http://localhost:7860", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.workflows_dir = Path("workflows")
        self.workflows_dir.mkdir(exist_ok=True)
        
    async def start_langflow_server(self, port: int = 7860) -> bool:
        """Start Langflow server"""
        try:
            # Check if server is already running
            if await self._check_server_health():
                logger.info(f"Langflow server already running on port {port}")
                return True
            
            # Start server in background
            cmd = f"langflow run --host 0.0.0.0 --port {port}"
            process = subprocess.Popen(
                cmd.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            # Wait for server to start
            await asyncio.sleep(5)
            
            # Check if server started successfully
            if await self._check_server_health():
                logger.info(f"Langflow server started successfully on port {port}")
                return True
            else:
                logger.error("Failed to start Langflow server")
                return False
                
        except Exception as e:
            logger.error(f"Error starting Langflow server: {e}")
            return False
    
    async def _check_server_health(self) -> bool:
        """Check if Langflow server is healthy"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    async def create_workflow(self, workflow_name: str, workflow_config: Dict[str, Any]) -> str:
        """Create a new Langflow workflow"""
        try:
            workflow_file = self.workflows_dir / f"{workflow_name}.json"
            
            # Create workflow configuration
            workflow_data = {
                "name": workflow_name,
                "description": workflow_config.get("description", ""),
                "created_at": datetime.utcnow().isoformat(),
                "config": workflow_config,
                "nodes": workflow_config.get("nodes", []),
                "edges": workflow_config.get("edges", [])
            }
            
            # Save workflow to file
            with open(workflow_file, 'w') as f:
                json.dump(workflow_data, f, indent=2)
            
            logger.info(f"Workflow '{workflow_name}' created successfully")
            return str(workflow_file)
            
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            raise
    
    async def load_workflow(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """Load a workflow from file"""
        try:
            workflow_file = self.workflows_dir / f"{workflow_name}.json"
            
            if not workflow_file.exists():
                logger.warning(f"Workflow file '{workflow_name}.json' not found")
                return None
            
            with open(workflow_file, 'r') as f:
                workflow_data = json.load(f)
            
            return workflow_data
            
        except Exception as e:
            logger.error(f"Error loading workflow: {e}")
            return None
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all available workflows"""
        workflows = []
        
        try:
            for workflow_file in self.workflows_dir.glob("*.json"):
                try:
                    with open(workflow_file, 'r') as f:
                        workflow_data = json.load(f)
                        workflows.append({
                            "name": workflow_data.get("name", workflow_file.stem),
                            "description": workflow_data.get("description", ""),
                            "created_at": workflow_data.get("created_at", ""),
                            "file_path": str(workflow_file)
                        })
                except Exception as e:
                    logger.warning(f"Error reading workflow file {workflow_file}: {e}")
                    continue
            
            return workflows
            
        except Exception as e:
            logger.error(f"Error listing workflows: {e}")
            return []
    
    async def create_training_workflow(self, model_config: Dict[str, Any]) -> str:
        """Create a training workflow for custom AI models"""
        
        # Define training workflow nodes
        training_nodes = [
            {
                "id": "data_loader",
                "type": "DataLoaderNode",
                "position": {"x": 100, "y": 100},
                "data": {
                    "label": "Training Data Loader",
                    "config": {
                        "data_source": "database",
                        "batch_size": model_config.get("batch_size", 16),
                        "max_length": model_config.get("max_length", 512)
                    }
                }
            },
            {
                "id": "model_creator",
                "type": "ModelCreatorNode",
                "position": {"x": 300, "y": 100},
                "data": {
                    "label": "Model Creator",
                    "config": {
                        "model_type": model_config.get("model_type", "transformer"),
                        "architecture": model_config.get("architecture", {}),
                        "device": model_config.get("device", "auto")
                    }
                }
            },
            {
                "id": "trainer",
                "type": "TrainerNode",
                "position": {"x": 500, "y": 100},
                "data": {
                    "label": "Model Trainer",
                    "config": {
                        "learning_rate": model_config.get("learning_rate", 2e-5),
                        "num_epochs": model_config.get("num_epochs", 3),
                        "validation_split": model_config.get("validation_split", 0.2),
                        "checkpoint_dir": model_config.get("checkpoint_dir", "checkpoints")
                    }
                }
            },
            {
                "id": "evaluator",
                "type": "EvaluatorNode",
                "position": {"x": 700, "y": 100},
                "data": {
                    "label": "Model Evaluator",
                    "config": {
                        "metrics": ["accuracy", "loss", "f1_score"],
                        "test_data_source": "validation_split"
                    }
                }
            },
            {
                "id": "model_saver",
                "type": "ModelSaverNode",
                "position": {"x": 900, "y": 100},
                "data": {
                    "label": "Model Saver",
                    "config": {
                        "save_path": model_config.get("save_path", "models"),
                        "save_format": "pytorch",
                        "include_tokenizer": True
                    }
                }
            }
        ]
        
        # Define workflow edges
        training_edges = [
            {
                "id": "edge_1",
                "source": "data_loader",
                "target": "model_creator",
                "sourceHandle": "data_output",
                "targetHandle": "data_input"
            },
            {
                "id": "edge_2",
                "source": "model_creator",
                "target": "trainer",
                "sourceHandle": "model_output",
                "targetHandle": "model_input"
            },
            {
                "id": "edge_3",
                "source": "trainer",
                "target": "evaluator",
                "sourceHandle": "trained_model",
                "targetHandle": "model_input"
            },
            {
                "id": "edge_4",
                "source": "evaluator",
                "target": "model_saver",
                "sourceHandle": "evaluation_results",
                "targetHandle": "evaluation_input"
            }
        ]
        
        workflow_config = {
            "description": f"Training workflow for {model_config.get('model_type', 'custom')} model",
            "nodes": training_nodes,
            "edges": training_edges,
            "model_config": model_config
        }
        
        workflow_name = f"training_{model_config.get('model_type', 'custom')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return await self.create_workflow(workflow_name, workflow_config)
    
    async def create_inference_workflow(self, model_path: str, model_type: str = "transformer") -> str:
        """Create an inference workflow for trained models"""
        
        inference_nodes = [
            {
                "id": "input_processor",
                "type": "InputProcessorNode",
                "position": {"x": 100, "y": 100},
                "data": {
                    "label": "Input Processor",
                    "config": {
                        "tokenizer_path": f"{model_path}_tokenizer",
                        "max_length": 512,
                        "truncation": True,
                        "padding": True
                    }
                }
            },
            {
                "id": "model_loader",
                "type": "ModelLoaderNode",
                "position": {"x": 300, "y": 100},
                "data": {
                    "label": "Model Loader",
                    "config": {
                        "model_path": model_path,
                        "model_type": model_type,
                        "device": "auto"
                    }
                }
            },
            {
                "id": "inference_engine",
                "type": "InferenceEngineNode",
                "position": {"x": 500, "y": 100},
                "data": {
                    "label": "Inference Engine",
                    "config": {
                        "batch_size": 32,
                        "temperature": 0.7,
                        "max_length": 100
                    }
                }
            },
            {
                "id": "output_processor",
                "type": "OutputProcessorNode",
                "position": {"x": 700, "y": 100},
                "data": {
                    "label": "Output Processor",
                    "config": {
                        "format": "json",
                        "include_confidence": True,
                        "include_tokens": False
                    }
                }
            }
        ]
        
        inference_edges = [
            {
                "id": "edge_1",
                "source": "input_processor",
                "target": "model_loader",
                "sourceHandle": "processed_input",
                "targetHandle": "input_data"
            },
            {
                "id": "edge_2",
                "source": "model_loader",
                "target": "inference_engine",
                "sourceHandle": "model_output",
                "targetHandle": "model_input"
            },
            {
                "id": "edge_3",
                "source": "inference_engine",
                "target": "output_processor",
                "sourceHandle": "inference_output",
                "targetHandle": "raw_output"
            }
        ]
        
        workflow_config = {
            "description": f"Inference workflow for {model_type} model",
            "nodes": inference_nodes,
            "edges": inference_edges,
            "model_path": model_path,
            "model_type": model_type
        }
        
        workflow_name = f"inference_{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return await self.create_workflow(workflow_name, workflow_config)
    
    async def execute_workflow(self, workflow_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow with input data"""
        try:
            # Load workflow
            workflow = await self.load_workflow(workflow_name)
            if not workflow:
                raise ValueError(f"Workflow '{workflow_name}' not found")
            
            # Execute workflow nodes in order
            results = {}
            current_data = input_data.copy()
            
            # Sort nodes by position for execution order
            nodes = sorted(workflow["nodes"], key=lambda x: x["position"]["x"])
            
            for node in nodes:
                node_id = node["id"]
                node_type = node["type"]
                node_config = node["data"]["config"]
                
                logger.info(f"Executing node: {node_id} ({node_type})")
                
                # Execute node based on type
                if node_type == "DataLoaderNode":
                    results[node_id] = await self._execute_data_loader(current_data, node_config)
                elif node_type == "ModelCreatorNode":
                    results[node_id] = await self._execute_model_creator(current_data, node_config)
                elif node_type == "TrainerNode":
                    results[node_id] = await self._execute_trainer(current_data, node_config)
                elif node_type == "EvaluatorNode":
                    results[node_id] = await self._execute_evaluator(current_data, node_config)
                elif node_type == "ModelSaverNode":
                    results[node_id] = await self._execute_model_saver(current_data, node_config)
                elif node_type == "InputProcessorNode":
                    results[node_id] = await self._execute_input_processor(current_data, node_config)
                elif node_type == "ModelLoaderNode":
                    results[node_id] = await self._execute_model_loader(current_data, node_config)
                elif node_type == "InferenceEngineNode":
                    results[node_id] = await self._execute_inference_engine(current_data, node_config)
                elif node_type == "OutputProcessorNode":
                    results[node_id] = await self._execute_output_processor(current_data, node_config)
                else:
                    logger.warning(f"Unknown node type: {node_type}")
                    results[node_id] = {"status": "skipped", "reason": "unknown_node_type"}
                
                # Update current data for next node
                if node_id in results:
                    current_data.update(results[node_id])
            
            return {
                "workflow_name": workflow_name,
                "status": "completed",
                "results": results,
                "final_output": current_data
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            return {
                "workflow_name": workflow_name,
                "status": "failed",
                "error": str(e)
            }
    
    async def _execute_data_loader(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data loader node"""
        # This would integrate with your database to load training data
        return {
            "training_data": input_data.get("training_data", []),
            "validation_data": input_data.get("validation_data", []),
            "data_stats": {
                "total_samples": len(input_data.get("training_data", [])),
                "validation_samples": len(input_data.get("validation_data", []))
            }
        }
    
    async def _execute_model_creator(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute model creator node"""
        from .custom_ai_models import CustomAITrainer
        
        trainer = CustomAITrainer(config)
        model = trainer.create_model(config["model_type"])
        
        return {
            "model": model,
            "model_config": config,
            "trainer": trainer
        }
    
    async def _execute_trainer(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trainer node"""
        trainer = input_data.get("trainer")
        if not trainer:
            return {"status": "failed", "reason": "No trainer found"}
        
        training_data = input_data.get("training_data", [])
        validation_data = input_data.get("validation_data", [])
        
        # Extract texts and labels
        train_texts = [item["text"] for item in training_data]
        train_labels = [item["label"] for item in training_data]
        
        val_texts = None
        val_labels = None
        if validation_data:
            val_texts = [item["text"] for item in validation_data]
            val_labels = [item["label"] for item in validation_data]
        
        # Train the model
        training_history = trainer.train(
            train_texts=train_texts,
            train_labels=train_labels,
            val_texts=val_texts,
            val_labels=val_labels,
            training_args=config
        )
        
        return {
            "training_history": training_history,
            "trained_model": trainer.model,
            "trainer": trainer
        }
    
    async def _execute_evaluator(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute evaluator node"""
        # This would evaluate the trained model
        return {
            "evaluation_results": {
                "accuracy": 0.85,
                "loss": 0.15,
                "f1_score": 0.83
            }
        }
    
    async def _execute_model_saver(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute model saver node"""
        trainer = input_data.get("trainer")
        if not trainer:
            return {"status": "failed", "reason": "No trainer found"}
        
        save_path = config["save_path"]
        trainer.save_model(save_path)
        
        return {
            "saved_model_path": save_path,
            "status": "success"
        }
    
    async def _execute_input_processor(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute input processor node"""
        # This would process input text using the tokenizer
        return {
            "processed_input": input_data.get("input_text", ""),
            "tokenizer_config": config
        }
    
    async def _execute_model_loader(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute model loader node"""
        from .custom_ai_models import CustomAITrainer
        
        trainer = CustomAITrainer(config)
        model = trainer.load_pretrained_model(config["model_path"], config["model_type"])
        
        return {
            "loaded_model": model,
            "trainer": trainer
        }
    
    async def _execute_inference_engine(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute inference engine node"""
        trainer = input_data.get("trainer")
        if not trainer:
            return {"status": "failed", "reason": "No trainer found"}
        
        input_text = input_data.get("processed_input", "")
        predictions = trainer.predict([input_text], config["batch_size"])
        
        return {
            "predictions": predictions,
            "input_text": input_text
        }
    
    async def _execute_output_processor(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute output processor node"""
        predictions = input_data.get("predictions", [])
        
        output = {
            "predictions": predictions,
            "confidence": 0.95,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if config["format"] == "json":
            return {"processed_output": json.dumps(output, indent=2)}
        else:
            return {"processed_output": str(output)}
    
    async def get_workflow_status(self, workflow_name: str) -> Dict[str, Any]:
        """Get the status of a workflow"""
        try:
            workflow = await self.load_workflow(workflow_name)
            if not workflow:
                return {"status": "not_found"}
            
            return {
                "name": workflow["name"],
                "description": workflow["description"],
                "created_at": workflow["created_at"],
                "node_count": len(workflow["nodes"]),
                "edge_count": len(workflow["edges"]),
                "status": "ready"
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            return {"status": "error", "error": str(e)}
    
    async def delete_workflow(self, workflow_name: str) -> bool:
        """Delete a workflow"""
        try:
            workflow_file = self.workflows_dir / f"{workflow_name}.json"
            
            if workflow_file.exists():
                workflow_file.unlink()
                logger.info(f"Workflow '{workflow_name}' deleted successfully")
                return True
            else:
                logger.warning(f"Workflow file '{workflow_name}.json' not found")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting workflow: {e}")
            return False
