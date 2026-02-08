from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.curriculum import PaperContent


# Keywords API Models
class KeywordExtractRequest(BaseModel):
    paper_id: str
    paper_content: PaperContent
    assigned_key_slot: Optional[int] = None


class KeywordExtractResponse(BaseModel):
    paper_id: str
    keywords: List[str]
    summary: Optional[str] = None
    extracted_at: str
    extracted_by: str
