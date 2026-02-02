import os
import asyncio
import json
from dotenv import load_dotenv

from core.agents.first_node_order_agent import FirstNodeOrderAgent
from core.contracts.first_node_order_agent import FirstNodeOrderAgentInput
from core.llm.solar_pro_2_llm import get_solar_model


async def main():
    load_dotenv()
    llm = get_solar_model(temperature=0.1) 
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    user_info_path = os.path.join(current_dir, "../../dummy_data/dummy_user_information_known.json")
    paper_content_path = os.path.join(current_dir, "../../dummy_data/dummy_parsing_paper.json")
    curriculum_path = os.path.join(current_dir, "../../dummy_data/langgraph__parallel.json")

    print("📂 데이터 로드 중...")
    try:
        with open(user_info_path, "r", encoding="utf-8") as f:
            user_info = json.load(f)
        with open(curriculum_path, "r", encoding="utf-8") as f:
            curriculum_data = json.load(f)
            if "paper_content" not in curriculum_data:
                paper_raw_data = {
                    "title": curriculum_data["graph_meta"]["title"],
                    "abstract": curriculum_data["graph_meta"]["summarize"]
                }
            else:
                paper_raw_data = curriculum_data["paper_content"]

    except FileNotFoundError as e:
        print(f"❌ 파일을 찾을 수 없습니다: {e}")
        print("💡 팁: dummy_data 폴더 위치를 확인하거나 경로를 절대 경로로 바꿔보세요.")
        return

    # Agent Input 구성
    test_input: FirstNodeOrderAgentInput = {
        "curriculum": curriculum_data["curriculum"],
        "paper_content": paper_raw_data,
        "user_info": user_info
    }

    # Agent 생성
    agent = FirstNodeOrderAgent(llm=llm)

    # 실행
    print(f"🚀 [FirstNodeOrder] 순서 결정 시작...")
    print(f"   - 논문: {paper_raw_data.get('title')}")
    print(f"   - 사용자 수준: {user_info.get('level')}")
    
    result = await agent.run(test_input)

    # 결과 검증 및 출력
    print("\n" + "="*50)
    print("✅ First Node Order Agent 테스트 완료")
    print("="*50)

    updated_curriculum = result.get("curriculum")
    ordered_nodes = updated_curriculum.get("first_node_order", [])

    if ordered_nodes:
        print(f"🔢 결정된 학습 순서 (총 {len(ordered_nodes)}개):")
        for i, node_id in enumerate(ordered_nodes):
            # ID에 해당하는 키워드 이름 찾기
            node_name = next((n['keyword'] for n in updated_curriculum['nodes'] if n['keyword_id'] == node_id), "Unknown")
            print(f"   {i+1}. [{node_id}] {node_name}")
    else:
        print("⚠️ 순서가 결정되지 않았습니다. (빈 리스트 반환됨)")
        print("   - 원인: 시작 노드가 없거나(순환 참조), LLM 파싱 실패 가능성")

    # 원본 데이터와 비교
    print("\n[Data Check]")
    print(f"Key 'first_node_order' exists: {'first_node_order' in updated_curriculum}")

if __name__ == "__main__":
    asyncio.run(main())