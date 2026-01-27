# python -m core.tests.test_concept_expansion_agent

import json
from typing import cast
from dotenv import load_dotenv

from core.agents.concept_expansion_agent import ConceptExpansionAgent
from core.contracts.types.curriculum import CurriculumGraph
from core.graphs.state_definition import CreateCurriculumOverallState
from core.llm.solar_pro_2_llm import get_solar_model

def main():
    # 1. env 로드
    load_dotenv()

    # 2. LLM 생성
    llm = get_solar_model(
        model_name="solar-pro3",
        temperature=0.5
    )

    # 3. Agent 생성
    agent = ConceptExpansionAgent(llm)

    # 4. 테스트용 JSON 데이터 로드
    with open("./dummy_data/dummy_initial_curriculum.json", "r", encoding="utf-8") as f:
        curriculum = json.load(f)

    curriculum_graph: CurriculumGraph = cast(CurriculumGraph, curriculum)
    reason = "The curriculum omits essential components such as multi‑head attention, residual connections, ReLU activation, embedding scaling, Adam optimizer, label smoothing, and BLEU evaluation, so the listed keywords cannot fully convey the paper’s concepts to a bachelor‑level learner."
    missing_concepts = [
    "key-001",
    "key-002",
    "key-003",
    "key-004",
    "key-006",
    "key-007",
    "key-008",
    "key-010",
    "key-011",
    "123456"
  ]
    
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