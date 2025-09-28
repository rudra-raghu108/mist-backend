"""
Authentication service for SRM Guide Bot
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.models.database import User, UserRole
from app.schemas.auth import UserRegister

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class AuthService:
    """Authentication service"""
    
    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_password_reset_token(self, email: str) -> str:
        """Create password reset token"""
        to_encode = {"sub": email, "type": "password_reset"}
        expire = datetime.utcnow() + timedelta(hours=1)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return email"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            email: str = payload.get("sub")
            if email is None:
                return None
            return email
        except JWTError:
            return None
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        try:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return None
            if not self.verify_password(password, user.password_hash):
                return None
            return user
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None
    
    def create_user(self, db: Session, user_data: UserRegister) -> User:
        """Create a new user"""
        try:
            # Hash password
            hashed_password = self.get_password_hash(user_data.password)
            
            # Create user object
            user = User(
                email=user_data.email,
                username=user_data.username,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                campus=user_data.campus,
                focus=user_data.focus,
                role=user_data.role,
                password_hash=hashed_password,
                is_email_verified=False,
                is_active=True
            )
            
            # Add to database
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"Created new user: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            db.rollback()
            raise
    
    def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(lambda: next(get_db()))) -> User:
        """Get current authenticated user"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            email = self.verify_token(token)
            if email is None:
                raise credentials_exception
            
            user = db.query(User).filter(User.email == email).first()
            if user is None:
                raise credentials_exception
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Inactive user"
                )
            
            return user
            
        except Exception as e:
            logger.error(f"Error getting current user: {str(e)}")
            raise credentials_exception
    
    def get_current_active_user(self, current_user: User = Depends(lambda: get_current_user())) -> User:
        """Get current active user"""
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        return current_user
    
    def validate_password_strength(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            return False
        
        if settings.PASSWORD_REQUIRE_SPECIAL_CHARS:
            if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in password):
                return False
        
        if settings.PASSWORD_REQUIRE_NUMBERS:
            if not any(char.isdigit() for char in password):
                return False
        
        if settings.PASSWORD_REQUIRE_UPPERCASE:
            if not any(char.isupper() for char in password):
                return False
        
        return True
    
    def update_user_last_login(self, db: Session, user: User):
        """Update user's last login timestamp"""
        try:
            user.last_login_at = datetime.utcnow()
            user.login_count += 1
            db.commit()
        except Exception as e:
            logger.error(f"Error updating user last login: {str(e)}")
            db.rollback()


# Create singleton instance
auth_service = AuthService()
