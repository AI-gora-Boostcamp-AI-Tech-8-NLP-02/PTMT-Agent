# uv run python core/tests/curriculum_compose_node_test.py
import os
import sys
import asyncio
import json
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from core.graphs.nodes import curriculum_compose_node
from core.graphs.state_definition import CreateCurriculumOverallState

from langgraph.graph import StateGraph, START, END

async def main():
    load_dotenv()
    
    print("🚀 테스트 시작: Curriculum Compose Node (LangGraph Execution)")
    print("=" * 60)

    # 데이터 로드
    data_dir = project_root / "tests" / "dummy_data"
    user_path = data_dir / "dummy_user_information.json"
    curriculum_path = data_dir / "dummy_initial_curriculum.json"
    
    try:
        with open(user_path, "r") as f:
            user_info = json.load(f)
        with open(curriculum_path, "r") as f:
            curriculum_data = json.load(f)

    except Exception as e:
        print(f"❌ 데이터 로드 실패: {e}")
        return

    # 1. Test Curriculum Compose Node
    print("\n[1] Testing curriculum_compose_node...")
    
    state_v1: CreateCurriculumOverallState = {
        "curriculum": curriculum_data,
        "user_info": user_info,
        "paper_name": "Test",
        "paper_summary": "",
        "initial_keywords": [],
        "paper_content": {},
        "final_curriculum": {},
        "keyword_subgraph": {},
        "is_keyword_sufficient": True,
        "is_resource_sufficient": True,
        "current_iteration_count": 0,
        "keyword_expand_reason": "",
        "tasks": [],
        "needs_description_ids": [],
        "insufficient_resource_ids": [],
        "missing_concepts": [],
        "keyword_reasoning": "",
        "resource_reasoning": ""
    }

    try:
        # LangGraph 구성
        workflow = StateGraph(CreateCurriculumOverallState)
        workflow.add_node("curriculum_compose", curriculum_compose_node)
        workflow.add_edge(START, "curriculum_compose")
        workflow.add_edge("curriculum_compose", END)
        
        app = workflow.compile()
        
        # LangGraph 실행
        result_state = await app.ainvoke(state_v1)
        new_curr = result_state.get("curriculum", {})
        
        print("✅ curriculum_compose_node 완료")
        
        # 상세 변경 내역 분석
        nodes_before = curriculum_data["nodes"]
        total_res_before = sum(len(n.get("resources", [])) for n in nodes_before)
        
        # 원본 로드 계산
        total_load_before = 0.0
        for n in nodes_before:
            for r in n.get("resources", []):
                try:
                    load = float(r.get("study_load", 0))
                except:
                    load = 0.0
                total_load_before += load

        # 결과 로드 및 상태 계산
        new_nodes = new_curr.get("nodes", [])
        total_res_after = 0
        emphasize_load = 0.0
        preserve_load = 0.0
        
        print("\n[상세 변경 내역 (Resources)]")
        for n in new_nodes:
            # 변경된 노드의 리소스 확인
            # (기존 노드와 매칭해서 변화를 볼 수도 있지만, 결과 상태 위주로 출력)
            has_print_node = False
            
            for r in n.get("resources", []):
                total_res_after += 1
                try:
                    load = float(r.get("study_load", 0) or 0)
                except:
                    load = 0.0
                
                is_nec = r.get("is_necessary")
                
                if is_nec:
                    status = "🔴 EMPHASIZE"
                    emphasize_load += load
                else:
                    status = "⚪ PRESERVE"
                    preserve_load += load
                
                if not has_print_node:
                    print(f"\n[{n['keyword']}]")
                    has_print_node = True
                    
                print(f"  {status} : {r['resource_name']} ({load}h)")

        total_load_after = emphasize_load + preserve_load
        
        print("\n" + "=" * 40)
        print(f"Original Resources: {total_res_before} (Load: {total_load_before:.1f}h)")
        print(f"Final Resources   : {total_res_after} (Deleted: {total_res_before - total_res_after})")
        print("-" * 40)
        print(f"🔴 EMPHASIZE Load : {emphasize_load:.1f}h")
        print(f"⚪ PRESERVE Load  : {preserve_load:.1f}h")
        print(f"Total Load        : {total_load_after:.1f}h")
        print("=" * 40)
        
    except Exception as e:
        print(f"❌ curriculum_compose_node 실패: {e}")

    print("\n" + "=" * 60)
    print("🎉 테스트 종료")

if __name__ == "__main__":
    asyncio.run(main())
