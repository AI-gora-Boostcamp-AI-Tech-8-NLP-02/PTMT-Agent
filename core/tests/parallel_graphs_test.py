import asyncio
import json
import os
from dotenv import load_dotenv

from core.graphs.parallel.graph_parallel import run_langgraph_workflow, create_initial_state

async def main():
    load_dotenv()
    print("🚀 테스트 스크립트 시작...")

    # dummy 데이터 경로 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    user_info_path = os.path.join(current_dir, "../../dummy_data/dummy_user_information_EX.json")
    paper_content_path = os.path.join(current_dir, "../../dummy_data/dummy_parsing_paper_BERT.json")
    subgraph_path = os.path.join(current_dir, "../../dummy_data/dummy_BERT_expert.json")
    meta_path = os.path.join(current_dir, "../../dummy_data/dummy_meta_data_BERT.json")
    
    initial_keywords=["Bidirectional Encoder Representations","Masked Language Model","Next Sentence Prediction","Transformer","Fine-tuning"]
    
    # 데이터 로드
    try:
        with open(subgraph_path, "r", encoding="utf-8") as f:
            dummy_subgraph = json.load(f)
        with open(user_info_path, "r", encoding="utf-8") as f:
            user_info_data = json.load(f)
        with open(paper_content_path, "r", encoding="utf-8") as f:
            paper_raw_data = json.load(f)
        with open(meta_path, "r", encoding="utf-8") as f:
            paper_meta_data = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ 파일을 찾을 수 없습니다: {e}")
        return
    

    initial_state = create_initial_state(
        subgraph_data=dummy_subgraph,
        user_info_data=user_info_data,
        paper_raw_data=paper_raw_data,
        paper_meta_data=paper_meta_data,
        initial_keywords=initial_keywords
    )

    app = run_langgraph_workflow()

    
    print("\n🌊 LangGraph 병렬 워크플로우 실행...")
    final_state = await app.ainvoke(initial_state)
    real_final_state= final_state.get("final_curriculum")

    print("\n" + "="*50)
    print(f"📊 최종 루프 횟수: {final_state.get('current_iteration_count')}")
    print(f"✅ 리소스 충분성: {final_state.get('is_resource_sufficient')}")
    
    output_filename = "dummy_initial_EX.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(real_final_state, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 결과 저장 완료: {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())