from typing import List, TypedDict
from core.contracts.types.curriculum import KeywordNode, Resource

class ResourceDiscoveryAgentInput(TypedDict):
    nodes: List[KeywordNode]    
    user_level: str
    purpose: str
    pref_types: List[str]

class ResourceDiscoveryAgentOutput(TypedDict):
    # 최종적으로 Estimation을 거쳐 완성된 Resource 목록을 반환
    evaluated_resources: List[Resource]  