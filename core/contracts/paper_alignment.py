"""
Paper-Concept Alignment Agent 입출력 데이터 모델 정의
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.contracts.paper import PaperInfo
from core.contracts.subgraph import Subgraph


# ============== 입력 모델 ==============
class PaperConceptAlignmentInput(BaseModel):
    """Paper-Concept Alignment Agent 입력"""
    paper_info: PaperInfo = Field(..., description="논문 정보")
    subgraph: Subgraph = Field(..., description="Keyword Graph Agent가 추출한 Subgraph")

# ============== 출력 모델 ==============

class KeywordAlignment(BaseModel):
    """개별 키워드와 논문의 연관 관계"""
    keyword_id: str = Field(..., description="키워드 ID")
    keyword: str = Field(..., description="키워드명")
    description: str = Field(..., description="해당 논문과의 연관성 설명")
    relevance_score: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0, 
        description="연관성 점수 (0.0 ~ 1.0)"
    )
    evidence_sections: Optional[List[str]] = Field(
        None, 
        description="연관성 근거가 되는 논문 섹션 목록"
    )


class PaperConceptAlignmentOutput(BaseModel):
    """Paper-Concept Alignment Agent 출력"""
    paper_id: str = Field(..., description="논문 ID")
    paper_title: str = Field(..., description="논문 제목")
    alignments: Dict[str, str] = Field(
        ..., 
        description="키워드별 연관성 설명 {keyword_id: description}"
    )
    detailed_alignments: Optional[List[KeywordAlignment]] = Field(
        None, 
        description="상세 연관성 정보 (선택적)"
    )


# ============== State 모델 (LangGraph용) ==============

class PaperConceptAlignmentState(BaseModel):
    """LangGraph State 정의"""
    # 입력
    paper_info: Optional[PaperInfo] = None
    subgraph: Optional[Subgraph] = None
    
    # 중간 처리 데이터
    paper_summary: Optional[str] = None
    keyword_context: Optional[Dict[str, Any]] = None
    
    # 출력
    alignments: Optional[Dict[str, str]] = None
    detailed_alignments: Optional[List[KeywordAlignment]] = None
    
    # 에러 처리
    error: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
