from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Resource(BaseModel):
    """키워드 관련 학습 자료"""
    resource_id: str = Field(..., description="자료 ID (DB Paper ID)")
    resource_name: str = Field(..., description="자료명")
    url: Optional[str] = Field(None, description="자료 링크")
    type: str = Field(..., description="자료 종류")
    abstract: Optional[str] = Field(None, description="DB Paper node의 abstract")


class SubgraphNode(BaseModel):
    """Subgraph 노드 (키워드)"""
    keyword_id: str = Field(..., description="키워드 ID (DB KC ID)")
    keyword: str = Field(..., description="실제 사용자에게 표시할 keyword")
    resources: List[Resource] = Field(default_factory=list, description="관련 자료 리스트")


class SubgraphEdge(BaseModel):
    """Subgraph 엣지 (키워드 간 관계)"""
    start: str = Field(..., description="시작 node keyword_id")
    end: str = Field(..., description="도착 node keyword_id")
    type: str = Field(..., description="관계 종류 (PREREQ, ABOUT, IN, REF_BY 등)")
    reason: Optional[str] = Field(None, description="관계 설명 또는 증거")
    strength: Optional[float] = Field(None, description="GDB edge strength")


class Subgraph(BaseModel):
    """Keyword Graph Agent가 추출한 Subgraph"""
    paper_id: str = Field(..., description="목표 논문 ID (RDB 저장 ID)")
    nodes: List[SubgraphNode] = Field(default_factory=list, description="노드 리스트")
    edges: List[SubgraphEdge] = Field(default_factory=list, description="엣지 리스트")

