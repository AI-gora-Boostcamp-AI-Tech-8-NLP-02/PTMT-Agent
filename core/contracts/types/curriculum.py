from typing import TypedDict, List, Optional

class Resource(TypedDict):
    resource_id: str
    resource_name: str
    url: str
    type: str  # "paper" | "web_doc" | "video"
    resource_description: str
    difficulty: int | str
    importance: int | str
    study_load: float | str
    is_necessary: Optional[bool]
    
    # Optional fields from ResourceData merger
    keyword_id: Optional[str]
    keyword: Optional[str]
    raw_content: Optional[str]

class KeywordNode(TypedDict):
    keyword_id: str
    keyword: str
    description: str
    keyword_importance: int
    is_keyword_necessary: Optional[bool]
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
    first_node_order:List[str]
    nodes: List[KeywordNode]
    edges: List[KeywordEdge]


