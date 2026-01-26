# uv run python core/tests/resource_discovery_test.py
import os
import asyncio
import json
from dotenv import load_dotenv
from core.agents.resource_discovery_agent import ResourceDiscoveryAgent
from core.contracts.resource_discovery import ResourceDiscoveryAgentInput 
from core.llm.solar_pro_2_llm import get_solar_model

async def main():

    load_dotenv()
    llm_for_search = get_solar_model(temperature=0.7)
    llm_for_eval = get_solar_model(temperature=0.1)
    
    user_info_path = "../../dummy_data/dummy_user_information.json"
    curriculum_path = "../../dummy_data/dummy_initial_curriculum.json"

    try:
        with open(user_info_path, "r", encoding="utf-8") as f:
            user_info = json.load(f)
        with open(curriculum_path, "r", encoding="utf-8") as f:
            curriculum_data = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ 파일을 찾을 수 없습니다: {e}")
        return

    target_nodes = curriculum_data.get("nodes", [])

    test_input: ResourceDiscoveryAgentInput = {
        "nodes": target_nodes,
        "user_level": user_info.get("level", "bachelor"),
        "purpose": user_info.get("purpose", "simple_study"),
        "pref_types": user_info.get("resource_type_preference", ["web_doc"]),
    }

    # Agent 생성 및 실행
    agent = ResourceDiscoveryAgent(
        llm_discovery=llm_for_search, 
        llm_estimation=llm_for_eval
    )

    print(f"🚀 테스트 시작: 논문 '{curriculum_data['graph_meta']['title']}'의 키워드 자료 검색 중...")
    result = await agent.run(test_input)

    print("\n" + "="*50)
    print("✅ Resource Discovery Agent 테스트 완료")
    resources = result.get("evaluated_resources", [])
    print(f"새롭게 검색 및 평가된 총 리소스 수: {len(resources)}")
    print("="*50)
        
    # 상세 결과 확인
    for i, res in enumerate(resources):
        print(f"\n[{i+1}] {res['keyword']} - {res['resource_name']}")
        print(f"    Query: {res['query']}")
        print(f"    URL: {res['url']}")
        print(f"    Content (100자): {res['raw_content'][:100]}...")
        print(f"    difficulty: {res['difficulty']}")
        print(f"    importance: {res['importance']}")
        print(f"    study_load: {res['study_load']}")
        print(f"    resource_type: {res['resource_type']}")   

    print("=======result=========")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())