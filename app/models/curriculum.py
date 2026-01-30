from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.graph import Graph


# Curriculum API Models
class BudgetedTime(BaseModel):
    total_days: str
    hours_per_day: str
    total_hours: str

class UserTraits(BaseModel):
    purpose: Optional[str] = None
    level: Optional[str] = None
    known_concept: Optional[List[str]] = Field(None, alias="known_concept")
    budgeted_time: Optional[BudgetedTime] = None
    resource_type_preference: Optional[List[str]] = Field(None, alias="resource_type_preference")


class PaperContentPart(BaseModel):
    subtitle: str
    text: str

class PaperContent(BaseModel):
    title: str
    author: Optional[str | List[str]] = None
    abstract: str
    body: List[PaperContentPart]

class CurriculumGenerateRequest(BaseModel):
    curriculum_id: str
    paper_id: str
    initial_keyword: List[str]
    paper_content: PaperContent
    user_traits: UserTraits = Field(alias="user_info")
    paper_title: Optional[str] = None # Deprecated, keep for compatibility or remove
    keywords: Optional[List[str]] = None # Deprecated



class CurriculumGenerateResponse(BaseModel):
    success: bool

