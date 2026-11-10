from pydantic import BaseModel, Field

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="The JWT access token string")
    token_type: str = Field("bearer", description="The type of the token, usually 'bearer'")
    
class LoginRequest(BaseModel):
    username: str = Field(..., examples=["john_doe@example.com"])
    password: str = Field(..., min_length=8, examples=["SecurePass123!"])


class TokenData(BaseModel):
    user_id: int | None = None
