from typing import List, TypedDict
from core.contracts.types.curriculum import Resource

class StudyLoadEstimationInput(TypedDict):
    resources: List[Resource]
    user_level: str
    purpose: str

class StudyLoadEstimationOutput(TypedDict):
    evaluated_resources: List[Resource]
