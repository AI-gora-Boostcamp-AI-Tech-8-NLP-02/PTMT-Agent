# core/agents/keyword_graph_agent.py

import os
import re
import ast
import copy
import json

from core.tools.gdb_search import get_subgraph_1
from core.prompts.keyword_graph import KEYWORD_GRAPH_PROMPT_V3_ENG
from core.contracts.keywordgraph import KeywordGraphInput, KeywordGraphOutput
from core.contracts.types.subgraph import Subgraph


class KeywordGraphAgent:
    def __init__(self, llm):
        """사용자 정보와 키워드 DB를 가지고 사용자 정보 반영한 가지치기 된 Subgraph를 만들어 줌
        
        Args:
            llm: LangChain 호환 LLM 인스턴스
        """
        self.llm = llm
        self.chain = KEYWORD_GRAPH_PROMPT_V3_ENG | llm
        self.init_subgraph = None

    async def run(self, input_data: KeywordGraphInput) -> KeywordGraphOutput:
        """에이전트 실행

        Args:
            input_data: 논문 정보,유저 정보, 1차 논문 키워드

        Returns:
            Subgraph
        """
        # 1. input_data를 이용해 1차 Subgraph 생성
        paper_name = input_data["paper_info"]["title"]
        initial_keyword = input_data["initial_keyword"]

        # 디버깅
        print(f"paper_name = {paper_name}")
        print(f'initial_keyword = {initial_keyword}')
        
        self.init_subgraph = get_subgraph_1(paper_name, initial_keyword)
        # 디버깅 -> json으로 저장
        # with open("debug_1차_서브그래프.json", "w", encoding="utf-8") as f:
        #     json.dump(self.init_subgraph, f, ensure_ascii=False, indent=2)

        # 2. 생성된 1차 Subgraph를 LLM Input에 맞춰 처리
        subgraph = self._preprocess_graph(self.init_subgraph)

        # 3. LLM 실행
        user_info = self._preprocess_user_info(input_data['user_info'])
        target_paper = (self.init_subgraph.get("graph", self.init_subgraph).get("target_paper", {})) or {}

        bt = user_info.get("budgeted_time", {}) or {}
        total_hours = bt.get("total_hours", 0)
        total_days = bt.get("total_days", 0)
        hours_per_day = bt.get("hours_per_day", 0)

        response = await self.chain.ainvoke(
        input={
            "user_level": user_info["level"],
            "user_purpose": user_info["purpose"],
            "known_concepts": user_info.get("known_concept", []),
            "total_hours": total_hours,
            "total_days": total_days, 
            "hours_per_day": hours_per_day, 
            "target_paper_title": target_paper.get("name", ""),
            "target_paper_id": target_paper.get("id", ""),
            "target_paper_description": target_paper.get("description", ""),
            "graph_json": subgraph
        }
        )

        # 4. LLM 실행 결과 후처리
        subgraph = self._postprocess_graph(
            paper_id=target_paper['id'],
            initial_keyword=initial_keyword,
            text=response.content
        )

        return {"subgraph": subgraph}
    

    def _preprocess_user_info(self, user_info):
        """
        - 필요한 키만 가져오기
        """
        ui = copy.deepcopy(user_info) if user_info else {}
        ui_out = {}
        for k in ("purpose", "level", "known_concept", "budgeted_time", "resource_type_preference"):
            if k in ui:
                ui_out[k] = ui[k]
        return ui_out
    

    def _preprocess_graph(self, raw_subgraph):
        return preprocess_graph(raw_subgraph=raw_subgraph)


    def _postprocess_graph(self, paper_id, initial_keyword, text):
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
