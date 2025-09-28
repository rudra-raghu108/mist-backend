"""
Authentication endpoints for SRM Guide Bot
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db
from app.models.database import User, Session as UserSession
from app.schemas.auth import UserLogin, UserRegister, TokenResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

auth_service = AuthService()


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        # Create new user
        user = auth_service.create_user(db, user_data)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            campus=user.campus,
            focus=user.focus,
            role=user.role,
            is_email_verified=user.is_email_verified,
            created_at=user.created_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token"""
    try:
        # Authenticate user
        user = auth_service.authenticate_user(db, user_data.email, user_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create access token
        access_token = auth_service.create_access_token(data={"sub": user.email})
        
        # Create refresh token
        refresh_token = auth_service.create_refresh_token(data={"sub": user.email})
        
        # Update user's last login
        user.last_login_at = datetime.utcnow()
        user.login_count += 1
        db.commit()
        
        # Create session
        session = UserSession(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            ip_address=user_data.ip_address if hasattr(user_data, 'ip_address') else None,
            user_agent=user_data.user_agent if hasattr(user_data, 'user_agent') else None
        )
        db.add(session)
        db.commit()
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        payload = jwt.decode(
            refresh_token, 
            settings.REFRESH_TOKEN_SECRET, 
            algorithms=[settings.ALGORITHM]
        )
        email = payload.get("sub")
        
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Check if session exists and is valid
        session = db.query(UserSession).filter(
            UserSession.token == refresh_token,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Get user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new access token
        new_access_token = auth_service.create_access_token(data={"sub": user.email})
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/logout")
async def logout(refresh_token: str, db: Session = Depends(get_db)):
    """Logout user by invalidating refresh token"""
    try:
        # Find and deactivate session
        session = db.query(UserSession).filter(
            UserSession.token == refresh_token,
            UserSession.is_active == True
        ).first()
        
        if session:
            session.is_active = False
            db.commit()
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        campus=current_user.campus,
        focus=current_user.focus,
        role=current_user.role,
        is_email_verified=current_user.is_email_verified,
        created_at=current_user.created_at
    )


@router.post("/forgot-password")
async def forgot_password(email: str, db: Session = Depends(get_db)):
    """Send password reset email"""
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Don't reveal if user exists or not
            return {"message": "If the email exists, a password reset link has been sent"}
        
        # Generate password reset token
        reset_token = auth_service.create_password_reset_token(user.email)
        user.password_reset_token = reset_token
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        
        # Send email (implement email service)
        # await email_service.send_password_reset_email(user.email, reset_token)
        
        return {"message": "If the email exists, a password reset link has been sent"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )


@router.post("/reset-password")
async def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    """Reset password using reset token"""
    try:
        # Find user with valid reset token
        user = db.query(User).filter(
            User.password_reset_token == token,
            User.password_reset_expires > datetime.utcnow()
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Update password
        user.password_hash = pwd_context.hash(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        db.commit()
        
        return {"message": "Password successfully reset"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )
