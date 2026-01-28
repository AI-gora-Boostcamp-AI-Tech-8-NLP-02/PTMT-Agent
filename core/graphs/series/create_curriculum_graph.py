import asyncio
import json
import os
from dotenv import load_dotenv
from typing import Literal, Dict, Any

from langgraph.graph import StateGraph, START, END

from core.graphs.subgraph_to_curriculum import transform_subgraph_to_final_curriculum
from core.graphs.series.nodes import (
    curriculum_orchestrator_node, 
    resource_discovery_agent_node,
    curriculum_compose_node,
    concept_expansion_node,
    paper_concept_alignment_node
)
from core.graphs.series.state_definition import CreateCurriculumOverallState

def create_initial_state(
    subgraph_data: Dict[str, Any],
    user_info_data: Dict[str, Any],
    paper_raw_data: Dict[str, Any]
) -> CreateCurriculumOverallState:
    """
    데이터를 입력받아 Transform을 수행
    LangGraph 실행을 위한 Initial State를 생성하여 반환
    """
    
    
    meta_data_input = {
        "paper_id": "123456", 
        "title" : paper_raw_data.get("title", "Unknown Title"),
        "summarize": "이 논문은 기존의 RNN이나 CNN을 완전히 배제하고 오로지 어텐션(Attention) 메커니즘만으로 구성된 트랜스포머(Transformer) 아키텍처를 제시하며 딥러닝 연구의 새로운 패러다임을 열었습니다. 연산의 병렬화를 통해 학습 속도를 비약적으로 높였을 뿐만 아니라, 기존 모델들의 고질적인 문제였던 장거리 의존성 문제를 해결함으로써 현재 GPT와 같은 초거대 언어 모델들이 탄생할 수 있는 결정적인 토대를 마련했습니다."
    }

    # Subgraph -> Curriculum 변환 (Transform)
    curriculum_data = transform_subgraph_to_final_curriculum(subgraph_data, meta_data_input)

    # Initial State 
    initial_state = {
        "paper_name": paper_raw_data.get("title", "Unknown"),
        "paper_summary": paper_raw_data.get("abstract", ""),
        "initial_keywords": [n.get("keyword") for n in curriculum_data.get("nodes", [])],
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

    return initial_state

def agent_loop_router(state: CreateCurriculumOverallState) -> Literal["resource_discovery", "concept_expansion", "paper_concept_alignment", "orchestrator"]:
    tasks = state.get("tasks", [])

    # tasks가 남아있으면 다음 agent로 이동
    if tasks:
        next_task = tasks[0] # 혹은 우선순위 로직
        print(f"🔄 [Agent] ({next_task}) -> 다음 에이전트로 이동")
        if next_task == "generate_description": return "paper_concept_alignment"    
        if next_task == "resource_search": return "resource_discovery"
        if next_task == "keyword_expansion": return "concept_expansion"

            
    print("✅ [Agent] 할 일 목록 비어있음 -> Orchestrator로 복귀하여 재진단")
    return "orchestrator"

def orchestrator_router(state: CreateCurriculumOverallState) -> Literal["resource_discovery", "concept_expansion", "paper_concept_alignment", "curriculum_compose"]:
    tasks = state.get("tasks", [])
    
    current_count = state.get("current_iteration_count", 0)
    MAX_ITERATIONS = 6


    if not tasks: 
        return "curriculum_compose"
        
    next_task = tasks[0] 

    # 종료 확인
    if next_task == "curriculum_compose":
        print("🏁 최종 단계(Compose)로 이동합니다.")
        return "curriculum_compose"

    if current_count >= MAX_ITERATIONS:
        print("⚠️ 반복 횟수 초과. 종료합니다.")
        return "curriculum_compose" 

    # agnet 배정
    print(f"🔄 [Agent] ({next_task}) -> 다음 에이전트로 이동") 
    if next_task == "generate_description": return "paper_concept_alignment"
    if next_task == "resource_search": return "resource_discovery"
    if next_task == "keyword_expansion": return "concept_expansion"

    return "curriculum_compose"


# 메인 실행 함수
def run_langgraph_workflow():
    # StateGraph 구성
    workflow = StateGraph(CreateCurriculumOverallState)

    # 노드 등록
    workflow.add_node("orchestrator", curriculum_orchestrator_node)
    workflow.add_node("resource_discovery", resource_discovery_agent_node)
    workflow.add_node("curriculum_compose", curriculum_compose_node)
    workflow.add_node("concept_expansion", concept_expansion_node)
    workflow.add_node("paper_concept_alignment", paper_concept_alignment_node)

    # 엣지 연결
    workflow.add_edge(START, "orchestrator")
    
    # orchestrator edge
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

    # agent edge
    workflow.add_conditional_edges(
        "resource_discovery", 
        agent_loop_router, 
        {
            "resource_discovery": "resource_discovery",
            "concept_expansion": "concept_expansion",
            "paper_concept_alignment": "paper_concept_alignment",
            "orchestrator": "orchestrator" 
        }
    )

    workflow.add_conditional_edges(
        "paper_concept_alignment", 
        agent_loop_router, 
        {
            "resource_discovery": "resource_discovery",
            "concept_expansion": "concept_expansion",
            "paper_concept_alignment": "paper_concept_alignment",
            "orchestrator": "orchestrator" 
        }
    )

    workflow.add_conditional_edges(
        "concept_expansion", 
        agent_loop_router, 
        {
            "resource_discovery": "resource_discovery",
            "concept_expansion": "concept_expansion",
            "paper_concept_alignment": "paper_concept_alignment",
            "orchestrator": "orchestrator" 
        }
    )

    # 최종 edge
    workflow.add_edge("curriculum_compose",END)

    # 컴파일
    return workflow.compile()

    