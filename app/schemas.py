from pydantic import BaseModel, HttpUrl, EmailStr
from typing import Optional
from datetime import datetime

class ScrapeRequest(BaseModel):
    url: HttpUrl

class ScrapeResponse(BaseModel):
    title: str
    price: float
    currency: str
    url: str

# User schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

# Token schemas (para compatibilidade)
class Token(BaseModel):
    access_token: str
    token_type: str
