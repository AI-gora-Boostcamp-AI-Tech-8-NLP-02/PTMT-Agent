from typing import List, Dict, Any, TypedDict, Optional


class PaperInfo(TypedDict):
    """논문 정보 구조"""
    title: str
    author: List[str]
    abstract: str
    body: List[Dict[str, str]]  # [{"subtitle": str, "text": str}, ...]


class GraphMeta(TypedDict):
    """커리큘럼 그래프 메타 정보"""
    paper_id: str
    title: str
    summarize: str


class CurriculumNode(TypedDict):
    """커리큘럼 노드 구조"""
    keyword_id: str
    keyword: str
    description: Optional[str]
    keyword_importance: int
    resources: List[Dict[str, Any]]


class CurriculumEdge(TypedDict):
    """커리큘럼 엣지 구조"""
    start: str
    end: str


class CurriculumData(TypedDict):
    """커리큘럼 전체 구조"""
    graph_meta: GraphMeta
    nodes: List[CurriculumNode]
    edges: List[CurriculumEdge]


class PaperConceptAlignmentInput(TypedDict):
    """Paper Concept Alignment Agent 입력"""
    paper_info: PaperInfo
    curriculum: CurriculumData


class PaperConceptAlignmentOutput(TypedDict):
    """Paper Concept Alignment Agent 출력 - 키워드 ID와 설명 매핑"""
    descriptions: Dict[str, str]  # {"keyword_id": "description", ...}
