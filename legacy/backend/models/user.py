from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid

def generate_uuid():
    return str(uuid.uuid4())

def current_time():
    return datetime.now(timezone.utc)

# User Models
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    phone: str
    name: str
    
class UserCreate(UserBase):
    password: str
    
class UserLogin(BaseModel):
    identifier: str  # email or phone
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=generate_uuid)
    email: Optional[str] = None
    phone: str
    name: str
    avatar: str = "https://api.dicebear.com/7.x/avataaars/svg?seed=default"
    created_at: datetime = Field(default_factory=current_time)
    is_active: bool = True
    role: str = "user"

class UserInDB(UserResponse):
    password_hash: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None
