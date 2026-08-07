from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    display_name: str
    is_admin: bool
    is_active: bool


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=256)
    new_password: str = Field(min_length=12, max_length=256)


class AuditLogResponse(BaseModel):
    id: str
    action: str
    entity_type: str | None
    entity_id: str | None
    details_json: str | None
    remote_address: str | None
    created_at: str
