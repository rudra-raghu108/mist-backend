"""
Authentication schemas for SRM Guide Bot
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.models.database import UserRole


class UserLogin(BaseModel):
    """User login request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")
    ip_address: Optional[str] = Field(None, description="User IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")


class UserRegister(BaseModel):
    """User registration request schema"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    username: Optional[str] = Field(None, max_length=100, description="Username")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    campus: Optional[str] = Field(None, max_length=100, description="SRM campus preference")
    focus: Optional[str] = Field(None, max_length=100, description="Academic focus area")
    role: UserRole = Field(UserRole.STUDENT, description="User role")


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class UserResponse(BaseModel):
    """User response schema"""
    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    username: Optional[str] = Field(None, description="Username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    campus: Optional[str] = Field(None, description="SRM campus")
    focus: Optional[str] = Field(None, description="Academic focus")
    role: UserRole = Field(..., description="User role")
    is_email_verified: bool = Field(..., description="Email verification status")
    created_at: datetime = Field(..., description="Account creation date")

    class Config:
        from_attributes = True


class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class UpdateProfileRequest(BaseModel):
    """Update user profile request schema"""
    username: Optional[str] = Field(None, max_length=100, description="Username")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    campus: Optional[str] = Field(None, max_length=100, description="SRM campus")
    focus: Optional[str] = Field(None, max_length=100, description="Academic focus")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
