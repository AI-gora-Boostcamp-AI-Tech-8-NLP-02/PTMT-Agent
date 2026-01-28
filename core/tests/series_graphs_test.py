import asyncio
import json
import os
from dotenv import load_dotenv

from core.graphs.series.create_curriculum_graph import run_langgraph_workflow, create_initial_state

async def main():
    load_dotenv()
    print("🚀 테스트 스크립트 시작...")

    # dummy 데이터 경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    user_info_path = os.path.join(current_dir, "../../dummy_data/dummy_user_information.json")
    paper_content_path = os.path.join(current_dir, "../../dummy_data/dummy_parsing_paper_v2.json")
    subgraph_path = os.path.join(current_dir, "../../dummy_data/dummy_subgraph.json")
    
    
    
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
    

    initial_state = create_initial_state(
        subgraph_data=dummy_subgraph,
        user_info_data=user_info_data,
        paper_raw_data=paper_raw_data
    )

    app = run_langgraph_workflow()
    
    print("\n🌊 LangGraph 직렬 워크플로우 실행...")
    final_state = await app.ainvoke(initial_state)


    print("\n" + "="*50)
    print(f"📊 최종 루프 횟수: {final_state.get('current_iteration_count')}")
    print(f"✅ 리소스 충분성: {final_state.get('is_resource_sufficient')}")
    
    output_filename = "langgraph_series.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(final_state, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 결과 저장 완료: {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())