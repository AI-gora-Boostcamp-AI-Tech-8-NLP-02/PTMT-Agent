import os
import json

from core.prompts.keyword_graph import KEYWORD_GRAPH_PROMPT_V1
from core.contracts.keywordgraph import KeywordGraphInput, KeywordGraphOutput
from core.contracts.types.subgraph import Subgraph


class KeywordGraphAgent:
    """"""

    def __init__(self, llm):
        """사용자 정보와 키워드 DB를 가지고 사용자 정보 반영한 가지치기 된 Subgraph를 만들어 줌
        
        Args:
            llm: LangChain 호환 LLM 인스턴스
        """
        self.llm = llm
        self.chain = KEYWORD_GRAPH_PROMPT_V1 | llm

    async def run(self, input_data: KeywordGraphInput) -> KeywordGraphOutput:
        """에이전트 실행

        TODO: 임시로 더미 데이터 반환, 이후에 구현 필요

        Args:
            input_data: 논문 정보,유저 정보, 1차 논문 키워드

        Returns:
            Subgraph
        """

        # response = await self.chain.ainvoke(input_data)

        target_paper_id = input_data.get("paper_id")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        subgraph_path = os.path.join(current_dir, "../../dummy_data/dummy_subgraph.json")
    
        # 데이터 로드
        try:
            with open(subgraph_path, "r", encoding="utf-8") as f:
                dummy_subgraph = json.load(f)
        except FileNotFoundError as e:
            print(f" subgraph 더미 데이터 로드 실패: {e}")
            return {"subgraph": {"paper_id": "dummy_paper", "nodes": [], "edges": []}}

        # Paper ID 교체
        if target_paper_id:
            original_paper_id = dummy_subgraph.get("paper_id")
            dummy_subgraph["paper_id"] = target_paper_id

            if original_paper_id and "edges" in dummy_subgraph:
                for edge in dummy_subgraph["edges"]:
                    if edge.get("start") == original_paper_id:
                        edge["start"] = target_paper_id
                    if edge.get("end") == original_paper_id:
                        edge["end"] = target_paper_id

        return {"subgraph": dummy_subgraph}