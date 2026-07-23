from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class UserCreate(BaseModel):
    username: str
    email: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True

class PostCreate(BaseModel):
    content: str

class PostResponse(BaseModel):
    id: int
    user_id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class FollowCreate(BaseModel):
    followee_id: int
