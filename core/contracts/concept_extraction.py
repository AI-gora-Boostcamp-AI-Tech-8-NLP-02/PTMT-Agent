from typing import List, TypedDict

from core.contracts.types.paper_info import PaperInfo

# Concept Extraction Agent Input & Output
class ConceptExtractionInput(TypedDict):
    paper_id: str
    paper_name: str       # 논문 이름
    paper_content: PaperInfo    # 구조화 된 full 입력 논문

class ConceptExtractionOutput(TypedDict):
    paper_id: str
    paper_name: str
    paper_summary: str          # 논문 요약
    paper_concepts: List[str]   # 1차 키워드 리스트