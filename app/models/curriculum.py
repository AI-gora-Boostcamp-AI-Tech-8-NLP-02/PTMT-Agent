from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.graph import Graph


# Curriculum API Models
class UserTraits(BaseModel):
    goal: Optional[str] = None
    level: Optional[str] = None
    understood_keywords: Optional[List[str]] = None
    investment_time: Optional[List[int]] = Field(None, description="총 일수, 하루 시간")
    preferred_format: Optional[List[str]] = None


class CurriculumGenerateRequest(BaseModel):
    analysis_id: str
    paper_title: str
    paper_db_id: Optional[str] = None
    keywords: List[str]
    user_traits: UserTraits


class CurriculumGenerateResponse(BaseModel):
    curriculum_id: str
    title: str
    graph: Graph
    created_at: str
