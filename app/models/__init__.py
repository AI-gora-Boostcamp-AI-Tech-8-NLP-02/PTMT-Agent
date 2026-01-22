# Re-export all models for backward compatibility
from app.models.base import ErrorResponse
from app.models.keyword import KeywordExtractRequest, KeywordExtractResponse
from app.models.curriculum import (
    UserTraits,
    CurriculumGenerateRequest,
    CurriculumGenerateResponse
)
from app.models.graph import Graph, GraphNode, GraphEdge

__all__ = [
    "ErrorResponse",
    "KeywordExtractRequest",
    "KeywordExtractResponse",
    "UserTraits",
    "CurriculumGenerateRequest",
    "CurriculumGenerateResponse",
    "Graph",
    "GraphNode",
    "GraphEdge",
]
