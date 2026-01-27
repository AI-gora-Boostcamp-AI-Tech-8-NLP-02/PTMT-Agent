# uv run python core/tests/paper_concept_alignment_agent_test.py
import os
import sys
import asyncio
import json
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from core.agents.paper_concept_alignment_agent import PaperConceptAlignmentAgent
from core.contracts.paper_concept_alignment import PaperConceptAlignmentInput
from core.llm.solar_pro_2_llm import get_solar_model


async def main():
    load_dotenv()
    
    # LLM 초기화
    llm = get_solar_model(temperature=0.3)
    
    # 테스트 데이터 로드
    data_dir = project_root / "tests" / "dummy_data"
    paper_path = data_dir / "dummy_parsing_paper.json"
    curriculum_path = data_dir / "dummy_initial_curriculum.json"
    
    try:
        with open(paper_path, "r", encoding="utf-8") as f:
            paper_info = json.load(f)
        with open(curriculum_path, "r", encoding="utf-8") as f:
            curriculum_data = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ 파일을 찾을 수 없습니다: {e}")
        return

    # 테스트를 위해 일부 노드의 description 제거
    test_curriculum = curriculum_data.copy()
    nodes_to_clear = ["key-001", "key-003", "key-005"]  # 일부 노드만 테스트
    
    for node in test_curriculum["nodes"]:
        if node["keyword_id"] in nodes_to_clear:
            node["description"] = ""  # description 비우기
    
    # 입력 데이터 구성
    test_input: PaperConceptAlignmentInput = {
        "paper_info": paper_info,
        "curriculum": test_curriculum
    }

    # Agent 생성 및 실행
    agent = PaperConceptAlignmentAgent(llm=llm)

    print(f"🚀 테스트 시작: 논문 '{paper_info['title']}'")
    print(f"📄 커리큘럼 노드 수: {len(curriculum_data['nodes'])}")
    print("=" * 60)
    
    result = await agent.run(test_input)

    print("\n" + "=" * 60)
    print("✅ Paper Concept Alignment Agent 테스트 완료")
    print("=" * 60)
    
    descriptions = result.get("descriptions", {})
    print(f"\n📝 생성된 설명 수: {len(descriptions)}")
    
    for keyword_id, description in descriptions.items():
        # 해당 키워드 이름 찾기
        keyword_name = next(
            (n["keyword"] for n in curriculum_data["nodes"] if n["keyword_id"] == keyword_id),
            "Unknown"
        )
        print(f"\n[{keyword_id}] {keyword_name}")
        print(f"  설명: {description}")

    print("\n" + "=" * 60)
    print("📊 전체 결과 JSON:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
