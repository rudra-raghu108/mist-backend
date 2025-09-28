#!/usr/bin/env python3
"""
AI Model Training Script for SRM Guide Bot
This script demonstrates how to train custom AI models using your database
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import torch
import numpy as np
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent))

from app.services.custom_ai_models import CustomAITrainer, SRMTransformerModel, SRMLSTMModel
from app.services.ai_database_service import AIDatabaseService
from app.services.langflow_service import LangflowService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AITrainingPipeline:
    """
    Complete AI training pipeline for SRM Guide Bot
    """
    
    def __init__(self, config_path: str = "training_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.trainer = None
        self.langflow_service = LangflowService()
        
    def load_config(self) -> Dict[str, Any]:
        """Load training configuration"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        else:
            # Default configuration
            return {
                "model_type": "transformer",
                "model_config": {
                    "vocab_size": 30522,
                    "hidden_size": 768,
                    "num_hidden_layers": 6,  # Reduced for faster training
                    "num_attention_heads": 12,
                    "intermediate_size": 3072,
                    "max_position_embeddings": 512,
                    "dropout": 0.1,
                    "num_labels": 2
                },
                "training_config": {
                    "learning_rate": 2e-5,
                    "num_epochs": 3,
                    "batch_size": 16,
                    "warmup_steps": 100,
                    "weight_decay": 0.01,
                    "validation_split": 0.2,
                    "checkpoint_dir": "checkpoints",
                    "save_path": "models"
                },
                "data_config": {
                    "data_source": "database",
                    "data_type": "conversation",
                    "max_length": 512,
                    "text_column": "content",
                    "label_column": "role"
                }
            }
    
    def save_config(self):
        """Save current configuration"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    async def prepare_training_data(self) -> tuple[List[str], List[int], List[str], List[int]]:
        """
        Prepare training and validation data from your database
        This is where you'd integrate with your existing database
        """
        logger.info("Preparing training data from database...")
        
        # Example: Load data from your existing Message table
        # You'll need to adapt this to your actual database schema
        try:
            async with AIDatabaseService() as db_service:
                # This is a placeholder - you'll need to implement actual data loading
                # based on your database structure
                
                # Example: Load conversation data
                # messages = await db_service.get_messages_for_training(
                #     data_type=self.config["data_config"]["data_type"]
                # )
                
                # For now, let's create some sample data
                sample_data = self.create_sample_training_data()
                
                # Split into training and validation
                split_idx = int(len(sample_data) * (1 - self.config["training_config"]["validation_split"]))
                train_data = sample_data[:split_idx]
                val_data = sample_data[split_idx:]
                
                # Extract texts and labels
                train_texts = [item["text"] for item in train_data]
                train_labels = [item["label"] for item in train_data]
                val_texts = [item["text"] for item in val_data]
                val_labels = [item["label"] for item in val_data]
                
                logger.info(f"Prepared {len(train_texts)} training samples and {len(val_texts)} validation samples")
                
                return train_texts, train_labels, val_texts, val_labels
                
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            # Fallback to sample data
            sample_data = self.create_sample_training_data()
            split_idx = int(len(sample_data) * (1 - self.config["training_config"]["validation_split"]))
            train_data = sample_data[:split_idx]
            val_data = sample_data[split_idx:]
            
            train_texts = [item["text"] for item in train_data]
            train_labels = [item["label"] for item in train_data]
            val_texts = [item["text"] for item in val_data]
            val_labels = [item["label"] for item in val_data]
            
            return train_texts, train_labels, val_texts, val_labels
    
    def create_sample_training_data(self) -> List[Dict[str, Any]]:
        """Create sample training data for demonstration"""
        sample_data = [
            # Student questions about admissions
            {"text": "What are the admission requirements for Computer Science?", "label": 0},
            {"text": "How do I apply for SRM University?", "label": 0},
            {"text": "What documents do I need for admission?", "label": 0},
            {"text": "What is the cutoff for B.Tech?", "label": 0},
            {"text": "How much is the application fee?", "label": 0},
            
            # Faculty and staff responses
            {"text": "The admission requirements include 12th standard completion with 60% marks.", "label": 1},
            {"text": "You can apply online through our website or visit the admission office.", "label": 1},
            {"text": "Required documents: 10th and 12th mark sheets, transfer certificate, and ID proof.", "label": 1},
            {"text": "The cutoff varies by year and program. Please check our website for current details.", "label": 1},
            {"text": "The application fee is Rs. 1000 for domestic students.", "label": 1},
            
            # Course-related questions
            {"text": "What courses are available in Computer Science?", "label": 0},
            {"text": "How many semesters are there in B.Tech?", "label": 0},
            {"text": "What are the elective subjects?", "label": 0},
            {"text": "Is there an internship program?", "label": 0},
            {"text": "What are the lab requirements?", "label": 0},
            
            # Course-related answers
            {"text": "We offer B.Tech, M.Tech, and PhD programs in Computer Science.", "label": 1},
            {"text": "B.Tech is an 8-semester program spanning 4 years.", "label": 1},
            {"text": "Elective subjects include AI, Machine Learning, and Data Science.", "label": 1},
            {"text": "Yes, we have a mandatory 6-month internship program.", "label": 1},
            {"text": "Students must complete 4 lab courses with hands-on projects.", "label": 1},
            
            # Campus life questions
            {"text": "What are the hostel facilities like?", "label": 0},
            {"text": "Are there sports facilities?", "label": 0},
            {"text": "What about transportation?", "label": 0},
            {"text": "Are there student clubs?", "label": 0},
            {"text": "What about food options?", "label": 0},
            
            # Campus life answers
            {"text": "We have modern hostel facilities with AC rooms and Wi-Fi.", "label": 1},
            {"text": "Yes, we have a sports complex with indoor and outdoor facilities.", "label": 1},
            {"text": "We provide shuttle services and have good public transport connectivity.", "label": 1},
            {"text": "There are over 50 student clubs covering various interests.", "label": 1},
            {"text": "We have multiple food courts and canteens with diverse cuisines.", "label": 1}
        ]
        
        # Duplicate and vary the data to create more training samples
        expanded_data = []
        for item in sample_data:
            expanded_data.append(item)
            # Create variations
            if "admission" in item["text"].lower():
                expanded_data.append({
                    "text": f"Can you tell me about {item['text'].lower()}?",
                    "label": item["label"]
                })
            elif "course" in item["text"].lower():
                expanded_data.append({
                    "text": f"I want to know about {item['text'].lower()}",
                    "label": item["label"]
                })
        
        return expanded_data
    
    async def create_ai_model(self, user_id: str = "demo_user") -> str:
        """Create a new AI model in the database"""
        try:
            async with AIDatabaseService() as db_service:
                model_data = {
                    "name": f"SRM_Guide_{self.config['model_type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "description": f"Custom {self.config['model_type']} model for SRM Guide Bot",
                    "model_type": self.config["model_type"],
                    "architecture": self.config["model_config"],
                    "tags": ["srm-guide", "custom-ai", self.config["model_type"]]
                }
                
                model = await db_service.create_model(model_data, user_id)
                logger.info(f"Created AI model: {model.name} (ID: {model.id})")
                return model.id
                
        except Exception as e:
            logger.error(f"Error creating AI model: {e}")
            raise
    
    async def train_model(self, model_id: str, user_id: str = "demo_user"):
        """Train the AI model"""
        try:
            logger.info(f"Starting training for model {model_id}")
            
            # Prepare training data
            train_texts, train_labels, val_texts, val_labels = await self.prepare_training_data()
            
            # Create trainer
            self.trainer = CustomAITrainer(self.config["model_config"])
            
            # Create and train model
            logger.info("Creating model architecture...")
            model = self.trainer.create_model(self.config["model_type"])
            
            logger.info("Starting training...")
            training_history = self.trainer.train(
                train_texts=train_texts,
                train_labels=train_labels,
                val_texts=val_texts,
                val_labels=val_labels,
                training_args=self.config["training_config"]
            )
            
            # Save the trained model
            save_path = os.path.join(
                self.config["training_config"]["save_path"],
                f"{model_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pth"
            )
            
            logger.info(f"Saving model to {save_path}")
            self.trainer.save_model(save_path)
            
            # Update model in database
            async with AIDatabaseService() as db_service:
                update_data = {
                    "status": "trained",
                    "model_path": save_path,
                    "config_path": save_path.replace('.pth', '_config.json'),
                    "tokenizer_path": save_path.replace('.pth', '_tokenizer'),
                    "accuracy": 0.85,  # You'd calculate actual accuracy
                    "loss": training_history.get("train_loss", [0])[-1] if training_history.get("train_loss") else 0,
                    "training_data_size": len(train_texts)
                }
                
                await db_service.update_model(model_id, update_data)
            
            logger.info("Training completed successfully!")
            return training_history
            
        except Exception as e:
            logger.error(f"Error during training: {e}")
            raise
    
    async def create_training_workflow(self, model_config: Dict[str, Any]):
        """Create a Langflow training workflow"""
        try:
            workflow_path = await self.langflow_service.create_training_workflow(model_config)
            logger.info(f"Created training workflow: {workflow_path}")
            return workflow_path
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            raise
    
    async def test_model(self, test_texts: List[str]) -> List[int]:
        """Test the trained model"""
        if not self.trainer:
            raise ValueError("No trained model available")
        
        try:
            predictions = self.trainer.predict(test_texts)
            logger.info(f"Made predictions for {len(test_texts)} texts")
            return predictions
        except Exception as e:
            logger.error(f"Error making predictions: {e}")
            raise
    
    def print_training_summary(self, training_history: Dict[str, Any]):
        """Print a summary of the training results"""
        print("\n" + "="*50)
        print("TRAINING SUMMARY")
        print("="*50)
        
        if "train_loss" in training_history:
            final_train_loss = training_history["train_loss"][-1] if training_history["train_loss"] else "N/A"
            print(f"Final Training Loss: {final_train_loss}")
        
        if "val_loss" in training_history:
            final_val_loss = training_history["val_loss"][-1] if training_history["val_loss"] else "N/A"
            print(f"Final Validation Loss: {final_val_loss}")
        
        if "learning_rate" in training_history:
            final_lr = training_history["learning_rate"][-1] if training_history["learning_rate"] else "N/A"
            print(f"Final Learning Rate: {final_lr}")
        
        print(f"Model Type: {self.config['model_type']}")
        print(f"Architecture: {self.config['model_config']['hidden_size']} hidden, {self.config['model_config']['num_hidden_layers']} layers")
        print("="*50)


async def main():
    """Main training function"""
    print("🤖 SRM Guide Bot - Custom AI Training Pipeline")
    print("="*60)
    
    # Initialize training pipeline
    pipeline = AITrainingPipeline()
    
    try:
        # Create AI model in database
        print("📝 Creating AI model in database...")
        model_id = await pipeline.create_ai_model()
        
        # Create Langflow workflow
        print("🔧 Creating Langflow training workflow...")
        workflow_path = await pipeline.create_training_workflow(pipeline.config)
        
        # Train the model
        print("🚀 Starting model training...")
        training_history = await pipeline.train_model(model_id)
        
        # Print training summary
        pipeline.print_training_summary(training_history)
        
        # Test the model
        print("\n🧪 Testing the trained model...")
        test_texts = [
            "What are the admission requirements?",
            "Tell me about the Computer Science program",
            "What facilities are available on campus?"
        ]
        
        predictions = await pipeline.test_model(test_texts)
        
        print("\nTest Results:")
        for text, pred in zip(test_texts, predictions):
            label_name = "Question" if pred == 0 else "Answer"
            print(f"Text: {text}")
            print(f"Prediction: {label_name} (Class {pred})")
            print("-" * 40)
        
        print("\n✅ Training pipeline completed successfully!")
        print(f"Model saved with ID: {model_id}")
        print(f"Workflow created at: {workflow_path}")
        
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}")
        print(f"\n❌ Training pipeline failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    # Check if CUDA is available
    if torch.cuda.is_available():
        print(f"🚀 CUDA available: {torch.cuda.get_device_name(0)}")
    else:
        print("💻 Using CPU for training")
    
    # Run the training pipeline
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 All done! Your custom AI model is ready.")
        print("You can now use it with your SRM Guide Bot!")
    else:
        print("\n💥 Something went wrong. Check the logs for details.")
        sys.exit(1)
