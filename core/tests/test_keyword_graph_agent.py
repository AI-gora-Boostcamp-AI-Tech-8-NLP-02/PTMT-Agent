# core/tests/test_keyword_graph_agent.py

import json
from typing import cast
import asyncio
import sys
from dotenv import load_dotenv
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.agents.keyword_graph_agent import KeywordGraphAgent
from core.contracts.keywordgraph import KeywordGraphInput
from core.llm.solar_pro_2_llm import get_solar_model
from dummy_data.dummy_bert_query import BERT_QUERY


async def main():
    # 1. env 로드
    load_dotenv()

    # 2. LLM 생성
    llm = get_solar_model(
        model_name="solar-pro2",
        temperature=0.3
    )

    # 3. Agent 생성
    agent = KeywordGraphAgent(llm)
    agent.init_subgraph = BERT_QUERY

    # 4. Agent 실행
    ## 테스트 데이터 로드
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
    
    ## 입력 데이터 구성
    ## KeywordGraphInput: paper_info, user_info, initial_keyword
    test_input: KeywordGraphInput = {
        "paper_info": paper_info,
        "user_info": user_info,
        "initial_keyword": [
                            "Self-Attention Mechanism",
                            "Scaled Dot-Product Attention",
                            "Multi-Head Attention",
                            "Position-wise Feed-Forward Networks",
                            "Positional Encoding",
                            "Residual Connections and Layer Normalization"
                            ] # 일단 임의로 설정
    }
    result = await agent.run(test_input)

    subgraph = result.get("subgraph")
    print(subgraph)


if __name__ == "__main__":
    asyncio.run(main())