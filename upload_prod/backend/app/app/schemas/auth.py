from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator


class LoginRequest(BaseModel):
    identifier: Optional[str] = Field(None, description="Email, username or phone")
    username: Optional[str] = Field(None, description="Backward-compatible login field")
    password: str

    @model_validator(mode="after")
    def validate_identifier(self):
        if not self.identifier and not self.username:
            raise ValueError("Either 'identifier' or 'username' is required")
        return self


class RefreshRequest(BaseModel):
    pass  # refresh token read from httpOnly cookie


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class SendOtpRequest(BaseModel):
    phone: str


class VerifyOtpRequest(BaseModel):
    phone: str
    otp: str = Field(..., min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class SchoolBasicResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    logo_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: UUID
    school_id: Optional[UUID] = None
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_super_admin: bool
    avatar_url: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    permissions: list[str] = []

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    access_token: str
    user: UserResponse
    school: Optional[SchoolBasicResponse] = None
