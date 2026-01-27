# python -m core.tests.test_concept_expansion_agent

import json
from typing import cast
from dotenv import load_dotenv

from core.agents.concept_expansion_agent import ConceptExpansionAgent
from core.contracts.curriculum import CurriculumGraph
from core.graphs.state_definition import CreateCurriculumOverallState
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
    agent = ConceptExpansionAgent(llm)

    # 4. 테스트용 JSON 데이터 로드
    with open("./dummy_data/dummy_initial_curriculum.json", "r", encoding="utf-8") as f:
        curriculum = json.load(f)

    curriculum_graph: CurriculumGraph = cast(CurriculumGraph, curriculum)
    reason = "논문 이해에 필요한 'layer normalization' 개념이 커리큘럼에 존재하지만, bachelor 수준 학습자가 이해하기 위해 필요한 선수 지식(예: 배치 정규화와의 차이점)이 명시적으로 포함되지 않음"
    missing_concepts = ["key-007"]
    
    dummy_state: CreateCurriculumOverallState = {
        # ===== Input State =====
        "paper_name": None,
        "paper_summary": None,
        "initial_keywords": [],
        "paper_content": None,
        "user_info": None,

        # ===== Output State (초기에는 비어있거나 None 성격) =====
        "final_curriculum": None,
        
        "keyword_subgraph": None,
        "curriculum": curriculum_graph,
        "is_keyword_sufficient": False,
        "is_resource_sufficient": False,
        "current_iteration_count": 0,
        "keyword_expand_reason": reason,
        "missing_concepts": missing_concepts
    }
    
    # 5. Agent 실행
    result = agent.run(dummy_state)

    # # 6. 결과 출력
    print("===== Concept Expansion Result =====")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()