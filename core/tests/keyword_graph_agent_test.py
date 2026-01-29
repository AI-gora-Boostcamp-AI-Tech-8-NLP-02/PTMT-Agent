# uv run python core/tests/keyword_graph_agent_test.py
import os
import sys
import asyncio
import json
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from core.agents.keyword_graph_agent import KeywordGraphAgent
from core.contracts.keywordgraph import KeywordGraphInput
from core.llm.solar_pro_2_llm import get_solar_model

async def main():
    """
    TODO: 이것도 나중에 제대로 구현
    """
    llm = get_solar_model(temperature=0.3)
    
    # 테스트 데이터 로드
    data_dir = project_root / "dummy_data"
    paper_path = data_dir / "dummy_parsing_paper.json"
    user_info_path = data_dir / "dummy_user_information.json"
    
    try:
        with open(paper_path, "r", encoding="utf-8") as f:
            paper_info = json.load(f)
        with open(user_info_path, "r", encoding="utf-8") as f:
            user_info = json.load(f)

    except FileNotFoundError as e:
        print(f"❌ 파일을 찾을 수 없습니다: {e}")
        # 파일이 없을 경우 더미 입력 데이터 생성
        paper_info = {"paper_id": "dummy_paper"}
        user_info = {"id": "dummy_user"}
    
    # 입력 데이터 구성
    # KeywordGraphInput: paper_info, user_info, initial_keyword
    test_input: KeywordGraphInput = {
        "paper_info": paper_info,
        "user_info": user_info,
        "initial_keyword": ["test_keyword1", "test_keyword2"] # 일단 임의로 설정
    }

    # Agent 생성 및 실행
    agent = KeywordGraphAgent(llm=llm)

    print(f"🚀 테스트 시작: Keyword Graph Agent")
    print("=" * 60)
    
    result = await agent.run(test_input)

    print("\n" + "=" * 60)
    print("✅ Keyword Graph Agent 테스트 완료")
    print("=" * 60)
    
    subgraph = result.get("subgraph")
    
    if subgraph:
        print(f"\n📝 생성된 Subgraph ID: {subgraph.get('paper_id')}")
        nodes = subgraph.get("nodes", [])
        edges = subgraph.get("edges", [])
        print(f"🔹 Nodes Count: {len(nodes)}")
        print(f"🔹 Edges Count: {len(edges)}")
    else:
        print("\n❌ Subgraph 생성 실패 (None 반환됨)")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
