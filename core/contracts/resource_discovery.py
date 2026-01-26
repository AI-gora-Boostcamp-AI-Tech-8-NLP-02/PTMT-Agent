from typing import List, Dict, Any, TypedDict, Set

class ResourceDiscoveryAgentInput(TypedDict):
    nodes: List[Dict[str, Any]]
    user_level: str
    purpose: str
    pref_types: List[str]

class ResourceDiscoveryAgentOutput(TypedDict):
    evaluated_resources: List[Dict[str, Any]]