from typing import Optional, List
from pydantic import BaseModel, Field


# Keywords API Models
class KeywordExtractRequest(BaseModel):
    pdf_text: Optional[str] = Field(None, description="PDF를 텍스트로 변환한 값")
    weblink: Optional[str] = None
    paper_title: Optional[str] = None
    paper_db_id: Optional[str] = None


class KeywordExtractResponse(BaseModel):
    analysis_id: str
    title: str
    paper_db_id: Optional[str] = None
    keywords: List[str]
    summary: Optional[str] = None
    extracted_at: str
    extracted_by: str
