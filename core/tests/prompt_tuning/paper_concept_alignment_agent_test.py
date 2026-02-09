# python -m core.tests.prompt_tuning.paper_concept_alignment_agent_test
import sys
import asyncio
import json
from pathlib import Path

# # repo root를 sys.path에 추가 (import core.* 가 동작하도록)
# workspace_root = Path(__file__).resolve().parents[3]  # .../PTMT-Agent
# sys.path.insert(0, str(workspace_root))

from dotenv import load_dotenv
from core.agents.paper_concept_alignment_agent import PaperConceptAlignmentAgent
from core.contracts.paper_concept_alignment import PaperConceptAlignmentInput
from core.graphs.subgraph_to_curriculum import transform_subgraph_to_final_curriculum
from core.llm.solar_pro_2_llm import get_solar_model


async def main():
    load_dotenv()
    
    # LLM 초기화
    llm = get_solar_model(temperature=0.3)
    
    # 테스트 데이터 로드 (이 파일 기준 dummies 경로)
    _dir = Path(__file__).resolve().parent
    paper_path = _dir / "dummies" / "dummy_parsing_paper.json"
    curriculum_path = _dir / "dummies" / "dummy_curriculum.json"

    try:
        with open(paper_path, "r", encoding="utf-8") as f:
            paper_info = json.load(f)
        with open(curriculum_path, "r", encoding="utf-8") as f:
            curriculum_data = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ 파일을 찾을 수 없습니다: {e}")
        return


    print("\n📦 curriculum_data (pretty)")
    print(json.dumps(curriculum_data, ensure_ascii=False, indent=2))

    # 입력 데이터 구성
    test_input: PaperConceptAlignmentInput = {
        "paper_info": paper_info,
        "curriculum": curriculum_data
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
    
    # 구현이 {"response": {...}} 로 반환하는 경우도 있어 방어적으로 처리
    descriptions = result.get("descriptions") or result.get("response") or {}
    print(f"\n📝 생성된 설명 수: {len(descriptions)}")
    
    for keyword_id, description in descriptions.items():
        # 해당 키워드 이름 찾기
        keyword_name = next(
            (n["keyword"] for n in curriculum_data["nodes"] if n["keyword_id"] == keyword_id),
            "Unknown"
        )
        print(f"\n[{keyword_id}] {keyword_name}")
        if isinstance(description, dict):
            print(f"  설명: {description.get('description', '')}")
        else:
            print(f"  설명: {description}")

    print("\n" + "=" * 60)
    print("📊 전체 결과 JSON:")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
