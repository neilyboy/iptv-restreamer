from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# Stream schemas
class StreamLogBase(BaseModel):
    log_type: str
    message: str

class StreamLogCreate(StreamLogBase):
    pass

class StreamLog(StreamLogBase):
    id: int
    stream_id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class StreamBase(BaseModel):
    name: str
    url: str
    stream_type: str

class StreamCreate(StreamBase):
    pass

class StreamUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    stream_type: Optional[str] = None

class Stream(StreamBase):
    id: int
    status: str
    process_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    logs: List[StreamLog] = []

    class Config:
        orm_mode = True

# User schemas
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
