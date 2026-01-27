from typing import List, Dict, Any, TypedDict

class ResourceData(TypedDict):
    keyword_id: str
    keyword: str
    resource_name: str
    url: str
    raw_content: str
    difficulty: str
    importance: str
    study_load: str
    type: str

class StudyLoadEstimationInput(TypedDict):
    resources: List[ResourceData]
    user_level: str
    purpose: str

class StudyLoadEstimationOutput(TypedDict):
    evaluated_resources: List[ResourceData]
