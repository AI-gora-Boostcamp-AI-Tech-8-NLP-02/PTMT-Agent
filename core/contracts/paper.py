from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.contracts.subgraph import Subgraph


class PaperBodySection(BaseModel):
    """논문 본문 섹션"""
    subtitle: str = Field(..., description="소제목 단위 (e.g. 3.1 Encoder and Decoder Stacks)")
    text: str = Field(..., description="논문 텍스트 (ref 제거, 수식 포함)")


class PaperInfo(BaseModel):
    """논문 정보"""
    title: str = Field(..., description="논문 제목")
    author: List[str] = Field(default_factory=list, description="저자 목록")
    abstract: str = Field(..., description="Abstract 내용")
    body: List[PaperBodySection] = Field(default_factory=list, description="본문 섹션 리스트")


