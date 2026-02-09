import asyncio
import json
import os
from dotenv import load_dotenv
from typing import Literal, List, Dict, Any

from langgraph.graph import StateGraph, START, END


from core.graphs.subgraph_to_curriculum import transform_subgraph_to_final_curriculum
from core.graphs.parallel.nodes_parallel import (
    curriculum_orchestrator_node, 
    resource_discovery_agent_node,
    curriculum_compose_node,
    concept_expansion_node,
    paper_concept_alignment_node,
    first_node_order_node
)
from core.graphs.parallel.state_parallel import CreateCurriculumOverallState

def create_initial_state(
    subgraph_data: Dict[str, Any],
    user_info_data: Dict[str, Any],
    paper_raw_data: Dict[str, Any],
    paper_meta_data: Dict[str,Any],
    initial_keywords: List[str]
) -> CreateCurriculumOverallState:
    """
    데이터를 입력받아 Transform을 수행
    LangGraph 실행을 위한 Initial State를 생성하여 반환
    """
    # Subgraph -> Curriculum 변환 (Transform)
    curriculum_data = transform_subgraph_to_final_curriculum(subgraph_data, paper_meta_data)

    # Initial State 
    initial_state = {
        "paper_name": paper_raw_data.get("title", "Unknown"),
        "paper_summary": paper_meta_data.get("summarize", ""),
        "initial_keywords": initial_keywords,
        "paper_content": paper_raw_data,
        "user_info": user_info_data,
        "curriculum": curriculum_data,
        "tasks": [],
        "current_iteration_count": 0, # 시작 카운트 0
        "is_keyword_sufficient": False,
        "is_resource_sufficient": False,
        "needs_description_ids": [],
        "insufficient_resource_ids": [],
        "missing_concepts": [],
        "keyword_reasoning": "Init",
        "resource_reasoning": "Init",
        "keyword_expand_reason": ""
    }

    return CreateCurriculumOverallState(**initial_state)

# Router: 병렬 실행
def orchestrator_router(state: CreateCurriculumOverallState) -> List[str]:
    tasks = state.get("tasks", [])
    current_count = state.get("current_iteration_count", 0)
    MAX_ITERATIONS = 6

    # 병렬 실행할 노드 리스트 
    next_nodes = []
    is_over_limit = current_count >= MAX_ITERATIONS

    has_desc = "generate_description" in tasks
    has_res = "resource_search" in tasks
    has_exp = "keyword_expansion" in tasks

    is_critical_cleanup = has_desc and has_res

    if is_over_limit:
        # 둘 다 동시에 있을 때만 실행
        if is_critical_cleanup:
            print(f"⚠️ [Router] 반복 초과({current_count})! 그러나 '설명,자료'가 동시에 누락되어 마지막으로 보충합니다.")
            next_nodes.append("paper_concept_alignment")
            next_nodes.append("resource_discovery")
        else:
            print(f"🛑 [Router] 반복 초과. (설명,자료 동시 누락 조건 불만족) -> 강제 종료.")
            return ["curriculum_compose"]
    else:
        # 제한 안 넘었으면 있는 태스크 다 담기
        if has_desc: next_nodes.append("paper_concept_alignment")
        if has_res: next_nodes.append("resource_discovery")
        if has_exp: next_nodes.append("concept_expansion")

    if next_nodes:
        print(f"🔀 [Parallel] 동시 실행: {next_nodes} (Loop: {current_count})")
        return next_nodes

    print("✅ [Router] 실행 가능한 태스크 없음. 종료.")
    return ["curriculum_compose"]


# Join Node, 결과 병합 후처리
async def join_parallel_results_node(state: CreateCurriculumOverallState):
    """
    병렬 실행된 노드들이 리듀서를 통해 데이터를 합치고 task 정리
    """
    print(" [Join] 병렬 작업 완료. Task 목록 정리 중...")
    remaining_tasks = [ ]
    
    return {
        "tasks": remaining_tasks
    }


def run_langgraph_workflow():
    # StateGraph 구성
    workflow = StateGraph(CreateCurriculumOverallState)

    # 노드 등록
    workflow.add_node("orchestrator", curriculum_orchestrator_node)
    workflow.add_node("resource_discovery", resource_discovery_agent_node)
    workflow.add_node("paper_concept_alignment", paper_concept_alignment_node)
    workflow.add_node("concept_expansion", concept_expansion_node)
    workflow.add_node("curriculum_compose", curriculum_compose_node)
    workflow.add_node("first_node_order",first_node_order_node)
    
    # join 노드 등록
    workflow.add_node("join_results", join_parallel_results_node)

    # 엣지 연결
    workflow.add_edge(START, "orchestrator")
    
    # 병렬 노드들
    # 리스트를 반환하므로 map 딕셔너리의 키와 일치하는 노드들이 동시 실행됨
    workflow.add_conditional_edges(
        "orchestrator",
        orchestrator_router,
        {
            "resource_discovery": "resource_discovery",
            "paper_concept_alignment": "paper_concept_alignment",
            "concept_expansion": "concept_expansion",
            "curriculum_compose": "curriculum_compose"
        }
    )

    
    # 일이 끝나면 무조건 Join 노드로 모임
    workflow.add_edge("resource_discovery", "join_results")
    workflow.add_edge("paper_concept_alignment", "join_results")
    workflow.add_edge("concept_expansion", "join_results")
    workflow.add_edge("join_results", "orchestrator")

    # 종료 처리
    workflow.add_edge("curriculum_compose", "first_node_order")
    workflow.add_edge("first_node_order",END)

    # 컴파일
    return workflow.compile()