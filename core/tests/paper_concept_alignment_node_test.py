# uv run python core/tests/paper_concept_alignment_node_test.py
import os
import sys
import asyncio
import json
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from core.graphs.nodes import paper_concept_alignment_node
from core.graphs.state_definition import CreateCurriculumOverallState

from langgraph.graph import StateGraph, START, END

async def main():
    load_dotenv()
    
    print("🚀 테스트 시작: Paper Concept Alignment Node (LangGraph Execution)")
    print("=" * 60)

    # 데이터 로드
    data_dir = project_root / "tests" / "dummy_data"
    curriculum_path = data_dir / "dummy_initial_curriculum.json"
    paper_path = data_dir / "dummy_parsing_paper.json"
    
    try:
        with open(curriculum_path, "r") as f:
            curriculum_data = json.load(f)
            
            # paper_concept_alignment 테스트를 위해 일부 description 비우기
            for node in curriculum_data["nodes"][:3]:
                 node["description"] = ""
        
        with open(paper_path, "r") as f:
            paper_info = json.load(f)

    except Exception as e:
        print(f"❌ 데이터 로드 실패: {e}")
        return

    # 2. Test Paper Concept Alignment Node
    print("\n[1] Testing paper_concept_alignment_node...")
    
    state_v2: CreateCurriculumOverallState = {
        "curriculum": curriculum_data,
        "paper_content": paper_info,
        "user_info": {},
        "paper_name": "Test",
        "paper_summary": "",
        "initial_keywords": [],
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
    
    # Target Nodes 확인 (description 비운 노드들)
    target_node_ids = [n["keyword_id"] for n in curriculum_data["nodes"][:3]]
    print(f"🎯 Target Nodes (Description cleared): {target_node_ids}")
    
    try:
        # LangGraph 구성
        workflow = StateGraph(CreateCurriculumOverallState)
        workflow.add_node("paper_concept_alignment", paper_concept_alignment_node)
        workflow.add_edge(START, "paper_concept_alignment")
        workflow.add_edge("paper_concept_alignment", END)
        
        app = workflow.compile()
        
        # LangGraph 실행
        result_state = await app.ainvoke(state_v2)
        new_curr_v2 = result_state.get("curriculum", {})
        
        print("✅ paper_concept_alignment_node 완료")
        
        # Description 확인
        filled_desc = 0
        print("\n[Description 채우기 결과]")
        
        for node in new_curr_v2.get("nodes", []):
            kid = node.get("keyword_id")
            desc = node.get("description", "")
            
            # 전체 통계
            if desc:
                filled_desc += 1
            
            # 타겟 노드 확인
            if kid in target_node_ids:
                status = "✅ FILLED" if desc else "❌ EMPTY"
                print(f"  - [{kid}] {node['keyword']}: {status}")
                if desc:
                    print(f"    -> {desc[:60]}...") # 내용 일부 출력

        print(f"\n  - Total Nodes with Description: {filled_desc}/{len(new_curr_v2.get('nodes', []))}")
        
    except Exception as e:
        print(f"❌ paper_concept_alignment_node 실패: {e}")

    print("\n" + "=" * 60)
    print("🎉 테스트 종료")

if __name__ == "__main__":
    asyncio.run(main())
