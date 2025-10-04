# assistant/schema.py
from typing import List, Literal, Dict, Any
from pydantic import BaseModel, Field

Priority = Literal["high", "medium", "low"]

class TriageOut(BaseModel):
    summary: str = Field(min_length=10, max_length=800)
    priority: Priority
    reasons: List[str]
    suggested_actions: List[Dict[str, Any]]

__all__ = ["TriageOut", "Priority"]
