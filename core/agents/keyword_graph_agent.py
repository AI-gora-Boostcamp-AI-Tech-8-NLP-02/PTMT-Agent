import os
import re
import copy
import json

from core.prompts.keyword_graph import KEYWORD_GRAPH_PROMPT_V2
from core.contracts.keywordgraph import KeywordGraphInput, KeywordGraphOutput


class KeywordGraphAgent:
    def __init__(self, llm):
        """사용자 정보와 키워드 DB를 가지고 사용자 정보 반영한 가지치기 된 Subgraph를 만들어 줌
        
        Args:
            llm: LangChain 호환 LLM 인스턴스
        """
        self.llm = llm
        self.chain = KEYWORD_GRAPH_PROMPT_V2 | llm
        self.init_subgraph = None

    async def run(self, input_data: KeywordGraphInput) -> KeywordGraphOutput:
        """에이전트 실행

        Args:
            input_data: 논문 정보,유저 정보, 1차 논문 키워드

        Returns:
            Subgraph
        """
        # 1. input_data를 이용해 1차 Subgraph 생성
        # TODO
        # self.init_subgraph = ...

        # 2. 생성된 1차 Subgraph를 LLM Input에 맞춰 처리
        subgraph = self._preprocess_graph(self.init_subgraph)

        # 3. LLM 실행
        user_info = input_data['user_info']
        response = await self.chain.ainvoke(
            input={
                'user_level': user_info['level'],
                'user_purpose': user_info['purpose'],
                'total_days': user_info['budgeted_time']['total_days'],
                'hours_per_day': user_info['budgeted_time']['hours_per_day'],
                'total_hours': user_info['budgeted_time']['total_hours'],
                'known_concepts': user_info['known_concept'],
                'graph_json': subgraph
            },
            config={
                "max_tokens": 8192
            }
        )

        # 4. LLM 실행 결과 후처리
        subgraph = self._postprocess_graph(
            paper_id="paper-123",
            text=response.content
        )

        return {"subgraph": subgraph}
    
    def _preprocess_graph(self, subgraph):
        """
        TODO: sub-graph 형식을 변경해서 사용할 지 
        """

        return copy.deepcopy(subgraph)

    def _postprocess_graph(self, paper_id, text):
        try:
            json_pattern = r'```json\s*(.*?)\s*```'
            match = re.search(json_pattern, text, re.DOTALL)

            if match:
                json_str = match.group(1)
                parsed_text = json.loads(json_str)
            else:
                parsed_text = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM output is not valid JSON: {text}") from e
        except Exception as e:
            raise RuntimeError(f"Unknown Error: {e}")

        '''
        id -> name 변환
        '''
        id_to_name = {}
        init_subgraph = self.init_subgraph['graph']
        for keyword in init_subgraph['nodes']['keywords']:
            id_to_name[keyword['id']] = keyword['name']
        for paper in init_subgraph['nodes']['papers']:
            id_to_name[paper['id']] = paper['name']

        # parsed_text node id -> node name
        parsed_text['filtered_graph']['nodes']['keywords'] = [
            id_to_name.get(kid, kid) for kid in parsed_text['filtered_graph']['nodes']['keywords']
        ]
        
        parsed_text['filtered_graph']['nodes']['papers'] = [
            id_to_name.get(pid, pid) for pid in parsed_text['filtered_graph']['nodes']['papers']
        ]

        # edges의 source와 target을 이름으로 변환
        for edge_type in ['IN', 'REF_BY', 'PREREQ', 'ABOUT']:
            if edge_type in parsed_text['filtered_graph']['edges']:
                for edge in parsed_text['filtered_graph']['edges'][edge_type]:
                    edge['source'] = id_to_name.get(edge['source'], edge['source'])
                    edge['target'] = id_to_name.get(edge['target'], edge['target'])
        
        # removed_nodes의 ID들도 이름으로 변환
        for removal_type in ['by_level', 'by_known_concepts', 'by_priority']:
            if removal_type in parsed_text['removed_nodes']:
                parsed_text['removed_nodes'][removal_type] = [
                    id_to_name.get(node_id, node_id) 
                    for node_id in parsed_text['removed_nodes'][removal_type]
                ]
        
        return parsed_text