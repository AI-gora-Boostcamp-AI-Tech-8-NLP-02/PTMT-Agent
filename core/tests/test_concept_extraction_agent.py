# python -m core.tests.test_concept_extraction_agent

import json
from dotenv import load_dotenv

from core.agents.concept_extraction_agent import ConceptExtractionAgent
from core.contracts.concept_extraction import ConceptExtractionInput
from core.llm.solar_pro_2_llm import get_solar_model

def main():
    # 1. env 로드
    load_dotenv()

    # 2. LLM 생성
    llm = get_solar_model(
        model_name="solar-pro2",
        temperature=0.5
    )

    # 3. Agent 생성
    agent = ConceptExtractionAgent(llm)

    # 4. 테스트용 JSON 데이터 로드
    with open("./dummy_data/dummy_parsing_paper_v2.json", "r", encoding="utf-8") as f:
        paper_data = json.load(f)

    paper_id = "paper_1"
    paper_name = "Attention Is All You Need"
    paper_content = paper_data

    paper: ConceptExtractionInput = {
        "paper_id": paper_id,
        "paper_name": paper_name,
        "paper_content": paper_content,
    }
    
    # 5. Agent 실행
    result = agent.run(paper)

    # # 6. 결과 출력
    print("===== Concept Extraction Result =====")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
