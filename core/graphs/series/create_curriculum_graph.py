import asyncio
import json
import os
from dotenv import load_dotenv
from typing import Literal

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



# 전처리 함수
def format_paper_content(paper_json: dict) -> str:
    title = paper_json.get("title", "Unknown Title")
    abstract = paper_json.get("abstract", "")
    body = paper_json.get("body", [])
    text = f"# {title}\n\n## Abstract\n{abstract}\n\n"
    for section in body:
        text += f"### {section.get('subtitle', '')}\n{section.get('text', '')}\n\n"
    return text

# 메인 실행 함수
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
    app = workflow.compile()

    # 실행
    print("\n🚀 LangGraph 워크플로우 가동...")
    final_state = await app.ainvoke(initial_state)

    # 결과 분석
    print("\n" + "="*50)
    print("🎯 최종 결과 리포트")
    print("="*50)
    print(f"📊 최종 반복 횟수: {final_state.get('current_iteration_count')}")
    print(f"📊 남은 Tasks: {final_state.get('tasks')}")
    print(f"✅ 전체 리소스 충분성: {final_state.get('is_resource_sufficient')}")
    
    # 개별 노드 상태 확인
    for node in final_state['curriculum']['nodes']:
        print(f"  - [{node['keyword_id']}] {node['keyword']}: Sufficient={node['is_resource_sufficient']}, Resources={len(node.get('resources', []))}")
    
    with open("langgraph_test_result_series_final.json", "w", encoding="utf-8") as f:
        json.dump(final_state, f, indent=2, ensure_ascii=False)
    print("\n✅ 'langgraph_test_result_full.json' 저장 완료.")

if __name__ == "__main__":
    asyncio.run(run_langgraph_workflow())