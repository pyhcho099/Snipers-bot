from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: int
    discord_id: str
    codename: Optional[str] = None
    coins: int = 0
    xp: int = 0
    rank: str = 'Recruit'
    contracts_completed: int = 0
    created_at: datetime
    last_seen: Optional[datetime] = None
    
    class Config:
        from_attributes = True
