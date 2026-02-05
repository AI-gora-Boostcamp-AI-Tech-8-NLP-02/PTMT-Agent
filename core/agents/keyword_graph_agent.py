# core/agents/keyword_graph_agent.py

import os
import re
import ast
import copy
import json

from core.tools.gdb_search import get_subgraph_1
from core.prompts.keyword_graph import KEYWORD_GRAPH_PROMPT_V8
from core.contracts.keywordgraph import KeywordGraphInput, KeywordGraphOutput
from core.utils.kg_agent_preprocessing import preprocess_graph, build_keyword_name_to_property
from core.utils.kg_agent_postprocessing import transform_graph_data

class KeywordGraphAgent:
    def __init__(self, llm):
        """사용자 정보와 키워드 DB를 가지고 사용자 정보 반영한 가지치기 된 Subgraph를 만들어 줌
        
        Args:
            llm: LangChain 호환 LLM 인스턴스
        """
        self.llm = llm
        self.chain = KEYWORD_GRAPH_PROMPT_V8 | llm
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

        # 만약 init_subgraph가 빈칸인 경우 초기값으로 채우기 -> RDB의 ID, NAME
        if self.init_subgraph['graph']['target_paper'] == None:
            target_paper = {
                'citationCount': 0,
                'name': paper_name,
                'description': '',
                'abstract': input_data['paper_info']['abstract'],
                'id': "paper-0" 
            }
            self.init_subgraph['graph']['target_paper'] = target_paper

        # 디버깅 -> json으로 저장
        with open("debug_1차_서브그래프.json", "w", encoding="utf-8") as f:
            json.dump(self.init_subgraph, f, ensure_ascii=False, indent=2)

        # 2. 생성된 1차 Subgraph를 LLM Input에 맞춰 처리
        subgraph = self._preprocess_graph(self.init_subgraph)

        # 3. LLM 실행
        user_info = input_data['user_info']
        target_paper = (self.init_subgraph.get("graph", self.init_subgraph).get("target_paper", {})) or {}

        # bt = user_info.get("budgeted_time", {}) or {}
        # total_hours = bt.get("total_hours", 0)
        # total_days = bt.get("total_days", 0)
        # hours_per_day = bt.get("hours_per_day", 0)

        response = await self.chain.ainvoke(
            input={
                "user_level": user_info["level"],
                # "user_purpose": user_info["purpose"],
                "known_concepts": user_info.get("known_concept", []),
                # "total_hours": total_hours,
                # "total_days": total_days, 
                # "hours_per_day": hours_per_day, 
                "target_paper_title": target_paper.get("name", ""),
                "target_paper_id": target_paper.get("id", ""),
                "target_paper_description": target_paper.get("description", ""),
                "graph_json": subgraph
            }, 
            config={
                "tags": ["keyword-graph-agent"]
            }
        )

        # 4. LLM 실행 결과 후처리
        subgraph = self._postprocess_graph(
            paper_id=target_paper['id'],
            initial_keyword=initial_keyword,
            text=response.content
        )

        return {"subgraph": subgraph}


    def _preprocess_graph(self, raw_subgraph):
        return preprocess_graph(raw_subgraph=raw_subgraph)


    def _postprocess_graph(self, paper_id, initial_keyword, text):
        try:
            json_pattern = r'```json\s*(.*?)\s*```'
            match = re.search(json_pattern, text, re.DOTALL)

            if match:
                json_str = match.group(1)
                parsed_dict = ast.literal_eval(json_str)
                agent_output = json.loads(json.dumps(parsed_dict, ensure_ascii=True))
            else:
                parsed_dict = ast.literal_eval(text)
                agent_output = json.loads(json.dumps(parsed_dict, ensure_ascii=True))
        
            print("\n===== RAW AGENT OUTPUT (BEFORE POSTPROCESS) =====")
            print(json.dumps(agent_output, indent=2, ensure_ascii=False))
            print("================================================\n")
        
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM output is not valid JSON: {text}") from e
        except Exception as e:
            raise RuntimeError(f"Unknown Error: {e}")

        # 1. 삭제된 Node를 참고하고 있는 Edge 존재시 삭제
        tp_name = self.init_subgraph.get('graph', {}).get('target_paper', {}).get('name', '')
        tp_id = self.init_subgraph.get('graph', {}).get('target_paper', {}).get('id', '')
        valid_keywords = set(agent_output.get('nodes', []) + [tp_name, tp_id])
        agent_output['edges'] = [
            edge for edge in agent_output['edges']
            if edge['start'] in valid_keywords and edge['end'] in valid_keywords
        ]

        # 2. 최종 출력 형식 변환
        keyword_name_to_property = build_keyword_name_to_property(self.init_subgraph)
        subgraph = transform_graph_data(self.init_subgraph, agent_output, keyword_name_to_property, paper_id)

        # 3. Agent의 출력 Keyword의 GraphDB 상 name, alias 뽑기
        all_keyword_alias = {}
        for db_keyword in self.init_subgraph['graph']['nodes']['keywords']:
            if db_keyword['name'] in valid_keywords:
                all_keyword_alias[db_keyword['name'].lower()] = db_keyword['name'] 
                for alias in db_keyword['alias']:
                    all_keyword_alias[alias.lower()] = db_keyword['name']

        # 4. Initial Keyword 처리
        for keyword in initial_keyword:
            if keyword.lower() in all_keyword_alias:
                # 4-1. Agent 생성에 포함된 Initial Keyword 처리
                original_keyword_name = all_keyword_alias[keyword.lower()].lower()
                original_keyword_property = keyword_name_to_property[original_keyword_name]
                
                for edge in subgraph['edges']:
                    if edge['start'] == original_keyword_property['id'] and edge['end'] == paper_id:
                        break
                else:
                    subgraph['edges'].append({
                        'start': original_keyword_property['id'],
                        'end': paper_id,
                        'type': "IN",
                        'reason': "",
                        'strength': ""
                    })
            else:
                # 4-2. Agent 생성에 포함되지 않았던 Initial Keyword 추가
                subgraph['nodes'].append({
                    "keyword_id": None,
                    "keyword": keyword,
                    "resources": []
                })

        # 5. Subgraph Keyword 이름 수정
        for nodes in subgraph['nodes']:
            nodes['keyword'] = nodes['keyword'].split("(")[0].strip().title()

        return subgraph