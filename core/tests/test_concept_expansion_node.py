# python -m core.tests.test_concept_expansion_node

import asyncio
import json
from typing import cast

from core.contracts.types.curriculum import CurriculumGraph
from core.graphs.parallel.nodes_parallel import concept_expansion_node
from core.graphs.parallel.state_parallel import CreateCurriculumOverallState

def main():
    # 테스트용 JSON 데이터 로드
    with open("./dummy_data/dummy_middle_curriculum_Inter.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    
    dummy_state: CreateCurriculumOverallState = cast(CreateCurriculumOverallState, data)
    
    # state 출력
    print("===== Concept Expansion State =====")
    print(json.dumps(dummy_state, indent=2, ensure_ascii=False))
    
    # node 실행
    result = asyncio.run(concept_expansion_node(dummy_state))

    # # 6. 결과 출력
    print("===== Concept Expansion Result =====")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()