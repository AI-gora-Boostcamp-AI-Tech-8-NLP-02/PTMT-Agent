import operator
from typing import Annotated, Any, Dict, List, TypedDict
from core.contracts.types.curriculum import CurriculumGraph
from core.contracts.types.paper_info import PaperInfo
from core.contracts.types.user_info import UserInfo

# 리듀서 정의
def merge_curriculum(existing: CurriculumGraph, delta: CurriculumGraph) -> CurriculumGraph:
    """
    병렬 노드들의 결과를 합쳐주는 리듀서
    """
    # 기존 노드 맵핑
    node_map = {n["keyword_id"]: n.copy() for n in existing.get("nodes", [])}
    
    # 노드 정보 병합
    for d_node in delta.get("nodes", []):
        kid = d_node["keyword_id"]
        if kid in node_map:
            # 기존 노드 업데이트
            for key, val in d_node.items():
                if val is not None and val != "":
                    if key == "resources":
                        # Resource ID 기준 중복 제거/병합
                        current_list = node_map[kid].get("resources", [])
                        new_list = val
                        
                        res_dict = {r["resource_id"]: r for r in current_list if r.get("resource_id")}
                        
                        for res in new_list:
                            rid = res.get("resource_id")
                            if rid:
                                res_dict[rid] = res # ID가 같으면 최신 정보로 덮어씀
                        
                        # 다시 리스트로 변환
                        merged_resources = list(res_dict.values())
                        merged_resources.sort(key=lambda x: x.get("resource_id", ""))
                        
                        node_map[kid]["resources"] = merged_resources
                        
                    else:
                        node_map[kid][key] = val
        else:
            node_map[kid] = d_node

    # 엣지 병합
    existing_edges = list(existing.get("edges", []))
    edge_keys = {f"{e['start']}->{e['end']}" for e in existing_edges}
    for n_edge in delta.get("edges", []):
        if f"{n_edge['start']}->{n_edge['end']}" not in edge_keys:
            existing_edges.append(n_edge)
            
    preserved_meta = delta.get("graph_meta") or existing.get("graph_meta") or {}

    new_first_node_order = delta.get("first_node_order")
    if new_first_node_order is None:
        new_first_node_order = existing.get("first_node_order")

    return {
        "graph_meta": preserved_meta,
        "first_node_order":new_first_node_order,
        "nodes": list(node_map.values()),
        "edges": existing_edges
    }


# Create Curriculm Graph State
class CreateCurriculumInputState(TypedDict):
    paper_name: str                 # 논문 이름
    paper_summary: str              # 논문 요약 
    initial_keywords: List[str]     # 1차 키워드 리스트
    paper_content: PaperInfo              # 구조화 된 full 입력 논문 
    user_info: UserInfo       # 구조화 된 사용자 정보 (목적,수준,시간,자료선호,{ "level": "", "purpose": "", "time_investment": "", "pref_type": "" })
	 
class CreateCurriculmOutputState(TypedDict):
    final_curriculum: CurriculumGraph    # 최종 커리큘럼 그래프 (JSON)

class CreateCurriculumOverallState(CreateCurriculumInputState, CreateCurriculmOutputState):
    # Subgraph
    keyword_subgraph: Dict[str, Any]
    
    # 커리큘럼 그래프
    curriculum: Annotated[CurriculumGraph, merge_curriculum]
    
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
    resource_reasoning:Dict[str, str]    
