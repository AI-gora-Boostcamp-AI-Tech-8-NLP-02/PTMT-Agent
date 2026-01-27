from typing import Dict, TypedDict
from core.contracts.types.paper_info import PaperInfo
from core.contracts.types.curriculum import CurriculumGraph

class PaperConceptAlignmentInput(TypedDict):
    """Paper Concept Alignment Agent 입력"""
    paper_info: PaperInfo
    curriculum: CurriculumGraph


class PaperConceptAlignmentOutput(TypedDict):
    """Paper Concept Alignment Agent 출력 - 키워드 ID와 설명 매핑"""
    descriptions: Dict[str, str]  # {"keyword_id": "description", ...}
