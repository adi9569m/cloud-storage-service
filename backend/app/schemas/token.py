from typing import Optional
from pydantic import BaseModel, Field

class Token(BaseModel):
    """Schema for returning JWT access and refresh token pair."""

    access_token: str = Field(..., description="Short-lived JWT access token")
    refresh_token: str = Field(..., description="Long-lived JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")

class TokenRefreshRequest(BaseModel):
    """Schema for requesting a new token pair using a refresh token."""

    refresh_token: str = Field(..., description="Valid JWT refresh token")

class TokenPayload(BaseModel):
    """Schema representing the decoded payload of a JWT token."""

    sub: str = Field(..., description="Subject identifier (User UUID)")
    type: str = Field(..., description="Token type ('access' or 'refresh')")
    exp: int = Field(..., description="Expiration timestamp (epoch)")
    iat: Optional[int] = Field(None, description="Issued-at timestamp (epoch)")
