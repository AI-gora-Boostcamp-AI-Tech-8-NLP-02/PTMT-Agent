"""
Paper-Concept Alignment Agent 테스트
"""
import json
import os
from dotenv import load_dotenv

from core.agents.paper_concept_alginment_agent import PaperConceptAlignmentAgent


def main():

    # 2. Agent 생성
    agent = PaperConceptAlignmentAgent()

    # 3. 더미 데이터 로드
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    with open(os.path.join(base_dir, "dummy_data/dummy_paper_info.json"), "r", encoding="utf-8") as f:
        paper_info = json.load(f)
    
    with open(os.path.join(base_dir, "dummy_data/dummy_subgraph.json"), "r", encoding="utf-8") as f:
        subgraph = json.load(f)

    # 4. Agent 실행
    print("===== Paper-Concept Alignment Agent 실행 중... =====\n")
    
    result = agent.run(
        paper_info=paper_info,
        subgraph=subgraph
    )

    # 5. 결과 출력
    print("===== Paper-Concept Alignment Result =====\n")
    print(f"Paper ID: {result.paper_id}")
    print(f"Paper Title: {result.paper_title}")
    print("\n--- Alignments (키워드별 연관성 설명) ---")
    print(json.dumps(result.alignments, indent=2, ensure_ascii=False))
    
    if result.detailed_alignments:
        print("\n--- Detailed Alignments ---")
        for alignment in result.detailed_alignments:
            print(f"\n[{alignment.keyword_id}] {alignment.keyword}")
            print(f"  설명: {alignment.description}")


if __name__ == "__main__":
    main()
