from typing import Any, Dict, List, TypedDict

# Create Curriculm Graph State
class CreateCurriculumInputState(TypedDict):
    paper_name: str                 # 논문 이름
    paper_summary: str              # 논문 요약 
    initial_keywords: List[str]     # 1차 키워드 리스트
    paper_content: str              # 구조화 된 full 입력 논문
    user_info: Dict[str, Any]       # 구조화 된 사용자 정보 (목적,수준,시간,자료선호,{ "level": "", "purpose": "", "time_investment": "", "pref_type": "" })
	 
class CreateCurriculmOutputState(TypedDict):
    final_curriculum: Dict[str, Any]    # 최종 커리큘럼 그래프 (JSON)

class CreateCurriculumOverallState(CreateCurriculumInputState, CreateCurriculmOutputState):
    # Subgraph
    keyword_subgraph: Dict[str, Any]
    
    # 커리큘럼 그래프
    curriculum: Dict[str, Any]
    
    # Resource Discovery: 키워드별 학습 자료 리스트
    discovered_resources: List[Dict[str, Any]]
    
    # --- 제어 및 프로세스 데이터 ---
    is_keyword_sufficient: bool               # 키워드 충분성 플래그
    is_resource_sufficient: bool              # 자료 충분성 플래그
    current_iteration_count: int              # Expansion 루프 횟수