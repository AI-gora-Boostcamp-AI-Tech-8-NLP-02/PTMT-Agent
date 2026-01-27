from typing import Any, Dict, List, TypedDict

from core.contracts.types.curriculum import CurriculumGraph
from core.contracts.types.user_info import UserInfo


# Create Curriculm Graph State
class CreateCurriculumInputState(TypedDict):
    paper_name: str                 # 논문 이름
    paper_summary: str              # 논문 요약 
    initial_keywords: List[str]     # 1차 키워드 리스트
    paper_content: str              # 구조화 된 full 입력 논문 //이거 str이 맞나?
    user_info: UserInfo       # 구조화 된 사용자 정보 (목적,수준,시간,자료선호,{ "level": "", "purpose": "", "time_investment": "", "pref_type": "" })
	 
class CreateCurriculmOutputState(TypedDict):
    final_curriculum: Dict[str, Any]    # 최종 커리큘럼 그래프 (JSON)

class CreateCurriculumOverallState(CreateCurriculumInputState, CreateCurriculmOutputState):
    # Subgraph
    keyword_subgraph: Dict[str, Any]
    
    # 커리큘럼 그래프
    curriculum: CurriculumGraph
    
    # --- 제어 및 프로세스 데이터 ---
    is_keyword_sufficient: bool               # 키워드 충분성 플래그
    is_resource_sufficient: bool              # 자료 충분성 플래그
    current_iteration_count: int              # Expansion 루프 횟수
    
    # concept expansion 추가 state
    keyword_expand_reason: str                # 키워드 추가 판단 이유

    tasks: List[str]                          # orchestrator가 출력하는 task list
    needs_description_ids: List[str]    
    insufficient_resource_ids: List[str] 
    missing_concepts: List[str]          
    keyword_reasoning:str
    resource_reasoning:str          
