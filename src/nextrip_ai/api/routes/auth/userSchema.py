from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr = Field(..., examples=["user@example.com"])
    username: str = Field(..., min_length=3, max_length=30, examples=["johndoe"])

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Plaintext password", examples=["SecurePass123!"])

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = Field(None, min_length=3, max_length=30)
    password: str | None = Field(None, min_length=8)

class UserResponse(UserBase):
    id: UUID = Field(..., description="Unique database identifier")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
