from typing import List, TypedDict

from core.contracts.types.curriculum import CurriculumGraph

# Concept Extraction Agent Input & Output
class ConceptExpansionInput(TypedDict):
    curriculum: CurriculumGraph
    keyword_expand_reason: str
    missing_concepts: List[str]

class ConceptExpansionOutput(TypedDict):
    curriculum: CurriculumGraph