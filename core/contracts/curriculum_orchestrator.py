from typing import List, TypedDict, Optional
from core.contracts.types.paper_info import PaperInfo
from core.contracts.types.curriculum import CurriculumGraph
from core.contracts.types.user_info import UserInfo


class CurriculumOrchestratorInput(TypedDict):
    paper_content: PaperInfo
    curriculum: CurriculumGraph
    user_info: UserInfo

class CurriculumOrchestratorOutput(TypedDict):
    tasks: List[str]                  # 실행해야 할 다음 태스크 목록
    is_keyword_sufficient: bool       # 키워드 충분성 여부
    is_resource_sufficient: bool      # 리소스 충분성 여부
    
    needs_description_ids: List[str]      # 설명 생성이 필요한 노드 ID들
    insufficient_resource_ids: List[str]  # 리소스 검색이 필요한 노드 ID들
    missing_concepts: List[str]           # 부족한 키워드 id 목록
    
    keyword_reasoning: str            # 키워드 판단 근거
    resource_reasoning: str           # 리소스 판단 근거

           




    
    
    