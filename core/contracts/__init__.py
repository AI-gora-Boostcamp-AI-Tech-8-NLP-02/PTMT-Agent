"""
Core Contracts 모듈 - 입출력 데이터 모델 정의
"""
from core.contracts.paper import (
    PaperBodySection,
    PaperInfo,
)
from core.contracts.subgraph import (
    Resource,
    SubgraphNode,
    SubgraphEdge,
    Subgraph,
)
from core.contracts.paper_alignment import (
    PaperConceptAlignmentInput,
    KeywordAlignment,
    PaperConceptAlignmentOutput,
    PaperConceptAlignmentState,
)

__all__ = [
    # 입력 모델
    "PaperBodySection",
    "PaperInfo",
    "Resource",
    "SubgraphNode",
    "SubgraphEdge",
    "Subgraph",
    "PaperConceptAlignmentInput",
    # 출력 모델
    "KeywordAlignment",
    "PaperConceptAlignmentOutput",
    # State 모델
    "PaperConceptAlignmentState",
]
