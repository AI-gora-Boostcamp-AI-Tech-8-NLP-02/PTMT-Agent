import asyncio
import json
import os
from dotenv import load_dotenv
from typing import Literal, List

from langgraph.graph import StateGraph, START, END


from core.graphs.subgraph_to_curriculum import transform_subgraph_to_final_curriculum
from core.graphs.parallel.nodes_parallel import (
    curriculum_orchestrator_node, 
    resource_discovery_agent_node,
    curriculum_compose_node,
    concept_expansion_node,
    paper_concept_alignment_node
)
from core.graphs.parallel.state_parallel import CreateCurriculumOverallState


# Router: 병렬 실행
def orchestrator_router(state: CreateCurriculumOverallState) -> List[str]:
    tasks = state.get("tasks", [])
    current_count = state.get("current_iteration_count", 0)
    MAX_ITERATIONS = 6

    # 종료 조건: 태스크가 없거나 반복 횟수 초과 시
    if not tasks: 
        print("🏁 [Router] 모든 태스크 완료. 최종 단계로 이동합니다.")
        return ["curriculum_compose"]
    
    if current_count >= MAX_ITERATIONS:
        print("⚠️ [Router] 반복 횟수 초과. 강제 종료합니다.")
        return ["curriculum_compose"]

    # 2. 병렬 실행할 노드 리스트 
    next_nodes = []
    
    # tasks 리스트에 있는 키워드를 보고 실행할 노드를 결정
    if "generate_description" in tasks: 
        next_nodes.append("paper_concept_alignment")
    if "resource_search" in tasks: 
        next_nodes.append("resource_discovery")
    if "keyword_expansion" in tasks: 
        next_nodes.append("concept_expansion")

    # tasks에는 있는데 매핑된 노드가 없는 경우
    if not next_nodes:
        return ["curriculum_compose"]
        
    print(f"🔀 [Parallel] 다음 에이전트들 동시 실행: {next_nodes} (Loop: {current_count})")
    
    return next_nodes


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


async def run_langgraph_workflow():
    load_dotenv()
    
    # dummy 데이터 경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    user_info_path = os.path.join(current_dir, "../../../dummy_data/dummy_user_information.json")
    paper_content_path = os.path.join(current_dir, "../../../dummy_data/dummy_parsing_paper_v2.json")
    subgraph_path = os.path.join(current_dir, "../../../dummy_data/dummy_subgraph.json")
    
    meta_data_input = {
        "paper_id": "123456",
        "title" : "Attention Is All You Need",
        "summarize": "이 논문은 기존의 RNN이나 CNN을 완전히 배제하고 오로지 어텐션(Attention) 메커니즘만으로 구성된 트랜스포머(Transformer) 아키텍처를 제시하며 딥러닝 연구의 새로운 패러다임을 열었습니다. 연산의 병렬화를 통해 학습 속도를 비약적으로 높였을 뿐만 아니라, 기존 모델들의 고질적인 문제였던 장거리 의존성 문제를 해결함으로써 현재 GPT와 같은 초거대 언어 모델들이 탄생할 수 있는 결정적인 토대를 마련했습니다."
    }
    
    # 데이터 로드
    try:
        with open(subgraph_path, "r", encoding="utf-8") as f:
            dummy_subgraph = json.load(f)
        with open(user_info_path, "r", encoding="utf-8") as f:
            user_info_data = json.load(f)
        with open(paper_content_path, "r", encoding="utf-8") as f:
            paper_raw_data = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ 파일을 찾을 수 없습니다: {e}")
        return

    curriculum_data = transform_subgraph_to_final_curriculum(dummy_subgraph, meta_data_input)

    # 초기 State 구성 
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

   
    # StateGraph 구성
    workflow = StateGraph(CreateCurriculumOverallState)

    # 노드 등록
    workflow.add_node("orchestrator", curriculum_orchestrator_node)
    workflow.add_node("resource_discovery", resource_discovery_agent_node)
    workflow.add_node("paper_concept_alignment", paper_concept_alignment_node)
    workflow.add_node("concept_expansion", concept_expansion_node)
    workflow.add_node("curriculum_compose", curriculum_compose_node)
    
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
    workflow.add_edge("curriculum_compose", END)

    # 컴파일
    app = workflow.compile()

    # 실행
    print("\n🚀 LangGraph 병렬 워크플로우 가동...")
    final_state = await app.ainvoke(initial_state)

    # 결과 리포트
    print("\n" + "="*50)
    print("🎯 최종 결과 리포트")
    print("="*50)
    print(f"📊 최종 반복 횟수: {final_state.get('current_iteration_count')}")
    print(f"✅ 전체 리소스 충분성: {final_state.get('is_resource_sufficient')}")
    
    with open("langgraph_test_result_parallel_final.json", "w", encoding="utf-8") as f:
        json.dump(final_state, f, indent=2, ensure_ascii=False)
    print("\n✅ 결과 저장 완료.")

if __name__ == "__main__":
    asyncio.run(run_langgraph_workflow())