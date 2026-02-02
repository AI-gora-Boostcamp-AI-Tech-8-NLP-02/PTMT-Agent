from typing import List, TypedDict

from core.contracts.types.curriculum import CurriculumGraph
from core.contracts.types.user_info import UserInfo

# Concept Extraction Agent Input & Output
class ConceptExpansionInput(TypedDict):
    curriculum: CurriculumGraph
    keyword_expand_reason: str
    missing_concepts: List[str]
    user_info: UserInfo

class ConceptExpansionOutput(TypedDict):
    curriculum: CurriculumGraph



