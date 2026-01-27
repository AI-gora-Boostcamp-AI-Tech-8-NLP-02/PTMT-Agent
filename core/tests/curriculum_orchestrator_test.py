import asyncio
import json
import os
from dotenv import load_dotenv
from core.agents.curriculum_orchestrator import CurriculumOrchestrator
from core.llm.solar_pro_2_llm import get_solar_model

async def main():
    # 환경 설정 및 LLM 초기화
    load_dotenv()
    llm = get_solar_model(temperature=0.1) 
    agent = CurriculumOrchestrator(llm)

    # 더미 데이터 경로 설정
    user_info_path = "../../dummy_data/dummy_user_information.json"
    curriculum_path = "../../dummy_data/dummy_initial_curriculum.json"
    paper_content_path="../../dummy_data/dummy_parsing_paper_v2.json"
    
    # 데이터 로드
    try:
        with open(curriculum_path, "r", encoding="utf-8") as f:
            curriculum = json.load(f)
        with open(user_info_path, "r", encoding="utf-8") as f:
            user_info = json.load(f)
        with open(paper_content_path, "r", encoding="utf-8") as f:
            paper_content = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ 파일을 찾을 수 없습니다: {e}")
        return

    

    print("📡 오케스트레이터 판단 시작...")
    print(f"👤 학습자 수준: {user_info['level']} | 목적: {user_info['purpose']}")
    
    # Agent 실행
    result = await agent.run(
        paper_content=paper_content,
        curriculum=curriculum,
        user_info=user_info
    )

    # 결과 분석 및 출력
    print("\n" + "="*50)
    print("🎯 Orchestrator Decision Result")
    print("="*50)
    print(f"📋 생성된 Tasks: {result.get('tasks', [])}")
    print(f"✅ 키워드 충분성: {result.get('is_keyword_sufficient')}")
    print(f"✅ 리소스 충분성: {result.get('is_resource_sufficient')}")
    print("-" * 60)
    print(f"🔑 Keyword Reasoning: {result.get('keyword_reasoning')}")
    print(f"📚 Resource Reasoning: {result.get('resource_reasoning')}")
    print("-" * 60)
    
    if result.get("missing_concepts"):
        print(f"💡 추가가 필요한 개념: {result['missing_concepts']}")
    
    if result.get("insufficient_resource_nodes"):
        print(f"🔍 리소스 부족 노드 ID: {result['insufficient_resource_ids']}")
        
    if result.get("needs_description_nodes"):
        print(f"📝 설명 생성 필요 노드 ID: {result['needs_description_ids']}")

    print("\n" + "="*50)
    print("📝 전체 결과 JSON")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())