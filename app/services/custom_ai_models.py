"""
Custom AI Models using PyTorch for SRM Guide Bot
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer, AutoModel, AutoConfig,
    TrainingArguments, Trainer, DataCollatorWithPadding
)
from typing import Dict, List, Optional, Tuple, Any
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SRMTransformerModel(nn.Module):
    """
    Custom Transformer model for SRM Guide Bot
    Based on BERT architecture with custom modifications
    """
    
    def __init__(
        self,
        vocab_size: int = 30522,
        hidden_size: int = 768,
        num_hidden_layers: int = 12,
        num_attention_heads: int = 12,
        intermediate_size: int = 3072,
        max_position_embeddings: int = 512,
        dropout: float = 0.1,
        num_labels: int = 2
    ):
        super().__init__()
        
        self.config = {
            'vocab_size': vocab_size,
            'hidden_size': hidden_size,
            'num_hidden_layers': num_hidden_layers,
            'num_attention_heads': num_attention_heads,
            'intermediate_size': intermediate_size,
            'max_position_embeddings': max_position_embeddings,
            'dropout': dropout,
            'num_labels': num_labels
        }
        
        # Embeddings
        self.embeddings = nn.Embedding(vocab_size, hidden_size)
        self.position_embeddings = nn.Embedding(max_position_embeddings, hidden_size)
        self.token_type_embeddings = nn.Embedding(2, hidden_size)
        self.layer_norm = nn.LayerNorm(hidden_size)
        self.dropout = nn.Dropout(dropout)
        
        # Transformer layers
        self.transformer_layers = nn.ModuleList([
            TransformerLayer(hidden_size, num_attention_heads, intermediate_size, dropout)
            for _ in range(num_hidden_layers)
        ])
        
        # Output layers
        self.pooler = nn.Linear(hidden_size, hidden_size)
        self.classifier = nn.Linear(hidden_size, num_labels)
        
        # Initialize weights
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            module.weight.data.normal_(mean=0.0, std=0.02)
            if module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.Embedding):
            module.weight.data.normal_(mean=0.0, std=0.02)
        elif isinstance(module, nn.LayerNorm):
            module.bias.data.zero_()
            module.weight.data.fill_(1.0)
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        token_type_ids: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        
        batch_size, seq_length = input_ids.size()
        
        if attention_mask is None:
            attention_mask = torch.ones(batch_size, seq_length, device=input_ids.device)
        
        if token_type_ids is None:
            token_type_ids = torch.zeros(batch_size, seq_length, device=input_ids.device)
        
        # Create position IDs
        position_ids = torch.arange(seq_length, device=input_ids.device).unsqueeze(0).expand(batch_size, -1)
        
        # Embeddings
        embeddings = self.embeddings(input_ids)
        position_embeddings = self.position_embeddings(position_ids)
        token_type_embeddings = self.token_type_embeddings(token_type_ids)
        
        # Combine embeddings
        hidden_states = embeddings + position_embeddings + token_type_embeddings
        hidden_states = self.layer_norm(hidden_states)
        hidden_states = self.dropout(hidden_states)
        
        # Transformer layers
        for transformer_layer in self.transformer_layers:
            hidden_states = transformer_layer(hidden_states, attention_mask)
        
        # Pooling
        pooled_output = self.pooler(hidden_states[:, 0])
        pooled_output = torch.tanh(pooled_output)
        
        # Classification
        logits = self.classifier(pooled_output)
        
        outputs = {'logits': logits, 'hidden_states': hidden_states, 'pooled_output': pooled_output}
        
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits.view(-1, self.config['num_labels']), labels.view(-1))
            outputs['loss'] = loss
        
        return outputs


class TransformerLayer(nn.Module):
    """Single Transformer layer"""
    
    def __init__(self, hidden_size: int, num_attention_heads: int, intermediate_size: int, dropout: float):
        super().__init__()
        
        self.attention = MultiHeadAttention(hidden_size, num_attention_heads, dropout)
        self.intermediate = nn.Linear(hidden_size, intermediate_size)
        self.output = nn.Linear(intermediate_size, hidden_size)
        self.layer_norm1 = nn.LayerNorm(hidden_size)
        self.layer_norm2 = nn.LayerNorm(hidden_size)
        self.dropout = nn.Dropout(dropout)
        self.activation = nn.GELU()
    
    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor] = None):
        # Self-attention
        attention_output = self.attention(hidden_states, attention_mask)
        hidden_states = self.layer_norm1(hidden_states + attention_output)
        
        # Feed-forward
        intermediate_output = self.intermediate(hidden_states)
        intermediate_output = self.activation(intermediate_output)
        intermediate_output = self.dropout(intermediate_output)
        
        output = self.output(intermediate_output)
        output = self.dropout(output)
        
        hidden_states = self.layer_norm2(hidden_states + output)
        
        return hidden_states


class MultiHeadAttention(nn.Module):
    """Multi-head attention mechanism"""
    
    def __init__(self, hidden_size: int, num_attention_heads: int, dropout: float):
        super().__init__()
        
        self.num_attention_heads = num_attention_heads
        self.attention_head_size = int(hidden_size / num_attention_heads)
        self.all_head_size = self.num_attention_heads * self.attention_head_size
        
        self.query = nn.Linear(hidden_size, self.all_head_size)
        self.key = nn.Linear(hidden_size, self.all_head_size)
        self.value = nn.Linear(hidden_size, self.all_head_size)
        self.dropout = nn.Dropout(dropout)
    
    def transpose_for_scores(self, x: torch.Tensor) -> torch.Tensor:
        new_x_shape = x.size()[:-1] + (self.num_attention_heads, self.attention_head_size)
        x = x.view(*new_x_shape)
        return x.permute(0, 2, 1, 3)
    
    def forward(self, hidden_states: torch.Tensor, attention_mask: Optional[torch.Tensor] = None):
        batch_size = hidden_states.size(0)
        
        # Linear transformations
        query_layer = self.transpose_for_scores(self.query(hidden_states))
        key_layer = self.transpose_for_scores(self.key(hidden_states))
        value_layer = self.transpose_for_scores(self.value(hidden_states))
        
        # Attention scores
        attention_scores = torch.matmul(query_layer, key_layer.transpose(-1, -2))
        attention_scores = attention_scores / (self.attention_head_size ** 0.5)
        
        if attention_mask is not None:
            attention_scores = attention_scores + attention_mask
        
        # Softmax
        attention_probs = F.softmax(attention_scores, dim=-1)
        attention_probs = self.dropout(attention_probs)
        
        # Apply attention to values
        context_layer = torch.matmul(attention_probs, value_layer)
        context_layer = context_layer.permute(0, 2, 1, 3).contiguous()
        new_context_layer_shape = context_layer.size()[:-2] + (self.all_head_size,)
        context_layer = context_layer.view(*new_context_layer_shape)
        
        return context_layer


class SRMLSTMModel(nn.Module):
    """
    Custom LSTM model for sequence classification
    """
    
    def __init__(
        self,
        vocab_size: int = 30522,
        embedding_dim: int = 256,
        hidden_size: int = 512,
        num_layers: int = 2,
        num_labels: int = 2,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(
            embedding_dim,
            hidden_size,
            num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True
        )
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_size * 2, num_labels)  # *2 for bidirectional
        
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: Optional[torch.Tensor] = None,
        labels: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        
        # Embeddings
        embedded = self.embedding(input_ids)
        
        # LSTM
        lstm_out, (hidden, cell) = self.lstm(embedded)
        
        # Use last hidden state from both directions
        last_hidden = torch.cat((hidden[-2], hidden[-1]), dim=1)
        last_hidden = self.dropout(last_hidden)
        
        # Classification
        logits = self.classifier(last_hidden)
        
        outputs = {'logits': logits}
        
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits, labels)
            outputs['loss'] = loss
        
        return outputs


class SRMDataset(Dataset):
    """
    Custom dataset for SRM Guide Bot training data
    """
    
    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_length: int = 512):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = self.labels[idx]
        
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }


class CustomAITrainer:
    """
    Custom AI Trainer for SRM Guide Bot models
    """
    
    def __init__(self, model_config: Dict[str, Any], device: str = 'auto'):
        self.model_config = model_config
        self.device = self._get_device(device)
        self.model = None
        self.tokenizer = None
        
    def _get_device(self, device: str) -> str:
        """Determine the best available device"""
        if device == 'auto':
            if torch.cuda.is_available():
                return 'cuda'
            elif torch.backends.mps.is_available():
                return 'mps'
            else:
                return 'cpu'
        return device
    
    def create_model(self, model_type: str = 'transformer') -> nn.Module:
        """Create a new model instance"""
        if model_type == 'transformer':
            self.model = SRMTransformerModel(**self.model_config)
        elif model_type == 'lstm':
            self.model = SRMLSTMModel(**self.model_config)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        self.model.to(self.device)
        return self.model
    
    def load_pretrained_model(self, model_path: str, model_type: str = 'transformer'):
        """Load a pretrained model"""
        if model_type == 'transformer':
            self.model = SRMTransformerModel(**self.model_config)
        elif model_type == 'lstm':
            self.model = SRMLSTMModel(**self.model_config)
        
        # Load state dict
        state_dict = torch.load(model_path, map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        
        return self.model
    
    def train(
        self,
        train_texts: List[str],
        train_labels: List[int],
        val_texts: Optional[List[str]] = None,
        val_labels: Optional[List[int]] = None,
        training_args: Optional[Dict[str, Any]] = None,
        model_type: str = 'transformer'
    ) -> Dict[str, Any]:
        """Train the model"""
        
        # Create model if not exists
        if self.model is None:
            self.create_model(model_type)
        
        # Default training arguments
        default_args = {
            'learning_rate': 2e-5,
            'num_epochs': 3,
            'batch_size': 16,
            'warmup_steps': 500,
            'weight_decay': 0.01,
            'logging_steps': 100,
            'save_steps': 1000,
            'eval_steps': 1000,
            'save_total_limit': 2,
        }
        
        if training_args:
            default_args.update(training_args)
        
        # Create tokenizer
        if self.tokenizer is None:
            self.tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Create datasets
        train_dataset = SRMDataset(train_texts, train_labels, self.tokenizer)
        train_loader = DataLoader(train_dataset, batch_size=default_args['batch_size'], shuffle=True)
        
        val_loader = None
        if val_texts and val_labels:
            val_dataset = SRMDataset(val_texts, val_labels, self.tokenizer)
            val_loader = DataLoader(val_dataset, batch_size=default_args['batch_size'])
        
        # Training setup
        optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=default_args['learning_rate'],
            weight_decay=default_args['weight_decay']
        )
        
        # Learning rate scheduler
        total_steps = len(train_loader) * default_args['num_epochs']
        scheduler = torch.optim.lr_scheduler.LinearLR(
            optimizer,
            start_factor=1.0,
            end_factor=0.1,
            total_iters=total_steps
        )
        
        # Training loop
        self.model.train()
        training_history = {
            'train_loss': [],
            'val_loss': [],
            'learning_rate': []
        }
        
        for epoch in range(default_args['num_epochs']):
            epoch_loss = 0.0
            
            for batch_idx, batch in enumerate(train_loader):
                # Move batch to device
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                # Forward pass
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                loss = outputs['loss']
                epoch_loss += loss.item()
                
                # Backward pass
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                scheduler.step()
                
                # Logging
                if batch_idx % default_args['logging_steps'] == 0:
                    logger.info(f"Epoch {epoch+1}/{default_args['num_epochs']}, "
                              f"Batch {batch_idx}/{len(train_loader)}, "
                              f"Loss: {loss.item():.4f}")
                
                training_history['learning_rate'].append(scheduler.get_last_lr()[0])
            
            # Validation
            if val_loader:
                val_loss = self._validate(val_loader)
                training_history['val_loss'].append(val_loss)
                logger.info(f"Epoch {epoch+1}, Train Loss: {epoch_loss/len(train_loader):.4f}, "
                          f"Val Loss: {val_loss:.4f}")
            else:
                logger.info(f"Epoch {epoch+1}, Train Loss: {epoch_loss/len(train_loader):.4f}")
            
            training_history['train_loss'].append(epoch_loss / len(train_loader))
        
        return training_history
    
    def _validate(self, val_loader: DataLoader) -> float:
        """Validate the model"""
        self.model.eval()
        total_loss = 0.0
        
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['labels'].to(self.device)
                
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels
                )
                
                total_loss += outputs['loss'].item()
        
        self.model.train()
        return total_loss / len(val_loader)
    
    def save_model(self, save_path: str):
        """Save the trained model"""
        if self.model is None:
            raise ValueError("No model to save")
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Save model state
        torch.save(self.model.state_dict(), save_path)
        
        # Save model config
        config_path = save_path.replace('.pth', '_config.json')
        with open(config_path, 'w') as f:
            json.dump(self.model_config, f, indent=2)
        
        # Save tokenizer
        if self.tokenizer:
            tokenizer_path = save_path.replace('.pth', '_tokenizer')
            self.tokenizer.save_pretrained(tokenizer_path)
        
        logger.info(f"Model saved to {save_path}")
    
    def predict(self, texts: List[str], batch_size: int = 32) -> List[int]:
        """Make predictions on new data"""
        if self.model is None:
            raise ValueError("No model loaded")
        
        self.model.eval()
        predictions = []
        
        # Create dataset
        dataset = SRMDataset(texts, [0] * len(texts), self.tokenizer)  # Dummy labels
        dataloader = DataLoader(dataset, batch_size=batch_size)
        
        with torch.no_grad():
            for batch in dataloader:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                
                outputs = self.model(
                    input_ids=input_ids,
                    attention_mask=attention_mask
                )
                
                batch_predictions = torch.argmax(outputs['logits'], dim=-1)
                predictions.extend(batch_predictions.cpu().tolist())
        
        return predictions
