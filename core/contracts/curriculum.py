from typing import TypedDict, List, Optional

class Resource(TypedDict):
    resource_id: str
    resource_name: str
    url: str
    type: str  # "paper" | "web_doc" | "video"
    resource_description: str
    difficulty: int
    importance: int
    study_load: float
    is_necessary: Optional[bool]

class KeywordNode(TypedDict):
    keyword_id: str
    keyword: str
    description: str
    keyword_importance: int
    is_resource_sufficient: bool
    resources: List[Resource]

class KeywordEdge(TypedDict):
    start: str
    end: str


class GraphMeta(TypedDict):
    paper_id: str
    title: str
    summarize: str

class CurriculumGraph(TypedDict):
    graph_meta: GraphMeta
    nodes: List[KeywordNode]
    edges: List[KeywordEdge]
