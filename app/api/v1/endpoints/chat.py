"""
Chat endpoints for SRM Guide Bot
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime
import json
import logging

from app.core.database import get_db
from app.models.database import User, Chat, Message, MessageRole
from app.schemas.chat import ChatCreate, ChatResponse, MessageCreate, MessageResponse, AIResponse
from app.services.ai_service import ai_service
from app.services.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()
logger = logging.getLogger(__name__)


@router.post("/chats", response_model=ChatResponse)
async def create_chat(
    chat_data: ChatCreate,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session"""
    try:
        chat = Chat(
            title=chat_data.title,
            user_id=current_user.id,
            is_active=True
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)
        
        return ChatResponse(
            id=chat.id,
            title=chat.title,
            user_id=chat.user_id,
            is_active=chat.is_active,
            created_at=chat.created_at,
            updated_at=chat.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create chat: {str(e)}"
        )


@router.get("/chats", response_model=List[ChatResponse])
async def get_user_chats(
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get all chats for the current user"""
    try:
        chats = db.query(Chat).filter(
            Chat.user_id == current_user.id,
            Chat.is_active == True
        ).order_by(Chat.updated_at.desc()).all()
        
        return [
            ChatResponse(
                id=chat.id,
                title=chat.title,
                user_id=chat.user_id,
                is_active=chat.is_active,
                created_at=chat.created_at,
                updated_at=chat.updated_at
            ) for chat in chats
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chats: {str(e)}"
        )


@router.get("/chats/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific chat by ID"""
    try:
        chat = db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == current_user.id
        ).first()
        
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        return ChatResponse(
            id=chat.id,
            title=chat.title,
            user_id=chat.user_id,
            is_active=chat.is_active,
            created_at=chat.created_at,
            updated_at=chat.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat: {str(e)}"
        )


@router.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a chat (soft delete)"""
    try:
        chat = db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == current_user.id
        ).first()
        
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        chat.is_active = False
        db.commit()
        
        return {"message": "Chat deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chat: {str(e)}"
        )


@router.post("/chats/{chat_id}/messages", response_model=MessageResponse)
async def send_message(
    chat_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message and get AI response"""
    try:
        # Verify chat exists and belongs to user
        chat = db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == current_user.id,
            Chat.is_active == True
        ).first()
        
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        # Save user message
        user_message = Message(
            content=message_data.content,
            role=MessageRole.USER,
            chat_id=chat_id,
            user_id=current_user.id
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        # Get chat history for context
        chat_history = db.query(Message).filter(
            Message.chat_id == chat_id
        ).order_by(Message.created_at.desc()).limit(10).all()
        
        # Generate AI response
        ai_response_data = await ai_service.generate_response(
            user_message=message_data.content,
            user=current_user,
            chat_history=chat_history
        )
        
        # Save AI response
        ai_message = Message(
            content=ai_response_data["content"],
            role=MessageRole.ASSISTANT,
            chat_id=chat_id,
            user_id=None,  # AI message
            extra_metadata={
                "tokens_used": ai_response_data["tokens_used"],
                "model_used": ai_response_data["model_used"],
                "category": ai_response_data["category"],
            },
        )
        db.add(ai_message)
        
        # Update chat title if it's the first message
        if not chat.title:
            chat.title = message_data.content[:50] + "..." if len(message_data.content) > 50 else message_data.content
        
        chat.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(ai_message)
        
        return MessageResponse(
            id=ai_message.id,
            content=ai_message.content,
            role=ai_message.role,
            chat_id=ai_message.chat_id,
            user_id=ai_message.user_id,
            metadata=ai_message.extra_metadata,
            created_at=ai_message.created_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


@router.get("/chats/{chat_id}/messages", response_model=List[MessageResponse])
async def get_chat_messages(
    chat_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages for a specific chat"""
    try:
        # Verify chat exists and belongs to user
        chat = db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == current_user.id
        ).first()
        
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        messages = db.query(Message).filter(
            Message.chat_id == chat_id
        ).order_by(Message.created_at.desc()).offset(offset).limit(limit).all()
        
        # Reverse to get chronological order
        messages.reverse()
        
        return [
            MessageResponse(
                id=message.id,
                content=message.content,
                role=message.role,
                chat_id=message.chat_id,
                user_id=message.user_id,
                metadata=message.extra_metadata,
                created_at=message.created_at
            ) for message in messages
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get messages: {str(e)}"
        )


@router.get("/suggestions")
async def get_quick_suggestions(
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get quick suggestion buttons for the user"""
    try:
        suggestions = await ai_service.generate_quick_suggestions(current_user)
        return {"suggestions": suggestions}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )


@router.post("/chats/{chat_id}/clear")
async def clear_chat(
    chat_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """Clear all messages from a chat"""
    try:
        # Verify chat exists and belongs to user
        chat = db.query(Chat).filter(
            Chat.id == chat_id,
            Chat.user_id == current_user.id
        ).first()
        
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
        
        # Delete all messages in the chat
        db.query(Message).filter(Message.chat_id == chat_id).delete()
        db.commit()
        
        return {"message": "Chat cleared successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear chat: {str(e)}"
        )


# WebSocket endpoint for real-time chat
@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_id: str,
    token: str
):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    try:
        # Verify token and get user
        # This is a simplified version - you should implement proper token verification
        db = next(get_db())
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message and generate AI response
            # This is a simplified version - implement full logic here
            
            # Send response back to client
            response = {
                "type": "ai_response",
                "content": "This is a placeholder AI response",
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()
    finally:
        if db:
            db.close()
