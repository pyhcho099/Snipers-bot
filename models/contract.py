from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models.enums import ContractRole

class Contract(BaseModel):
    id: int
    assigner_id: int
    assignee_id: int
    role: ContractRole
    series: str
    chapter: int
    reward_amount: int
    status: str = 'active'
    proof_url: Optional[str] = None
    receipt_url: Optional[str] = None
    due_at: Optional[datetime] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
