from typing import List, Dict, Any, TypedDict, Optional, Literal

class BudgetedTime(TypedDict):
    total_days: str
    hours_per_day: str
    total_hours: str

class UserInfo(TypedDict):
    purpose: str
    level: str
    known_concept: List[str]
    budgeted_time: BudgetedTime
    resource_type_preference: List[str]

class CurriculumNode(TypedDict):
    keyword_id: str
    keyword: str
    description: Optional[str]
    keyword_importance: int
    is_necessary: Optional[bool]
    resources: List[Dict[str, Any]]

class CurriculumEdge(TypedDict):
    start: str
    end: str

class CurriculumGraphMeta(TypedDict):
    paper_id: str
    title: str
    summarize: str

class CurriculumData(TypedDict):
    graph_meta: CurriculumGraphMeta
    nodes: List[CurriculumNode]
    edges: List[CurriculumEdge]

class CurriculumComposeInput(TypedDict):
    user_info: UserInfo
    curriculum: CurriculumData

class CurriculumComposeOutput(TypedDict):
    curriculum: CurriculumData

# 에이전트 내부 판단용 타입
class NodeAction(TypedDict):
    keyword_id: str
    action: Literal["DELETE", "PRESERVE", "EMPHASIZE"]
    reason: str
