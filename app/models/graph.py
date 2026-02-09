from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class GraphNode(BaseModel):
    id: str
    label: str
    type: Optional[str] = None
    metadata: Optional[dict] = None


class GraphEdge(BaseModel):
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    weight: Optional[float] = None
    metadata: Optional[dict] = None

    model_config = ConfigDict(populate_by_name=True)


class Graph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
