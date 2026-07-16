from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# ─── Auth Schemas ────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# ─── Chat Schemas ─────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    reply: str
    session_id: str

class MessageOut(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None

class SessionHistoryOut(BaseModel):
    session_id: str
    messages: list[MessageOut]
