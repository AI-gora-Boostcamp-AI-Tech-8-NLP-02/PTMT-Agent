from typing import TypedDict, List

class SubgraphResource(TypedDict):
    resource_name: str
    url: str
    type: str # "paper" | "web_doc" | "video"
    abstract: str

class SubgraphNode(TypedDict):
    keyword_id: str
    keyword: str
    resources: List[SubgraphResource]

class SubgraphEdge(TypedDict):
    start: str
    end: str
    type: str # "PREREQ" | "IN"
    reason: str
    strength: float | int

class Subgraph(TypedDict):
    paper_id: str
    nodes: List[SubgraphNode]
    edges: List[SubgraphEdge]
