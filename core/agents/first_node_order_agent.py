import json, re, asyncio
from typing import Dict, Any, List
from core.contracts.types.curriculum import CurriculumGraph, KeywordNode, Resource
from core.contracts.types.paper_info import PaperInfo
from core.contracts.first_node_order_agent import (
    FirstNodeOrderAgentInput, 
    FirstNodeOrderAgentOutput
)
from core.prompts.first_node_order.v1 import FIRST_ORDER_PROMPT_V1

class FirstNodeOrderAgent:
    def __init__(self, llm):
        self.llm = llm
        self.order_chain = FIRST_ORDER_PROMPT_V1 | llm
        

    async def run(self, input_data: FirstNodeOrderAgentInput) -> FirstNodeOrderAgentOutput:
        paper_content = input_data["paper_content"]
        curriculum = input_data["curriculum"]
        user_info = input_data["user_info"]

        user_level = user_info.get("level", "unknown")
        user_purpose = user_info.get("purpose", "simple_study")

        first_nodes=self._get_first_nodes(curriculum)
        
        chain_input = {
            "first_nodes": json.dumps(first_nodes, ensure_ascii=False),
            "paper_content": paper_content.get("abstract", ""), 
            "keyword_graph": json.dumps(curriculum, ensure_ascii=False),
            "user_level": user_level,
            "user_purpose": user_purpose
        }

        response = await self.order_chain.ainvoke(chain_input)

        ordered_first_nodes = self._parse_response(response.content)

        final_order = self._validate_and_fix_order(
            original_list=first_nodes,      
            llm_output_list=ordered_first_nodes
        )

        curriculum["first_node_order"] = final_order

        return {
            "curriculum": curriculum
        }


    def _get_first_nodes(self, curriculum_data: Dict[str, Any]) -> List[str]:
        """
        엣지의 'end'에 한 번도 등장하지 않은 노드의 ID 리스트를 반환
        """
        # 모든 엣지의 end ID를 집합으로 수집
        target_ids = {edge['end'] for edge in curriculum_data['edges']}
        
        # 전체 노드를 순회하며 target_ids에 없는 노드만 필터링
        first_node_ids = [
            node['keyword_id']
            for node in curriculum_data['nodes']
            if node['keyword_id'] not in target_ids
        ]
        
        return first_node_ids
    
    def _parse_response(self, content: str) -> List[str]:
        """문자열을 파이썬 리스트로 변환"""
        try:
            cleaned_content = re.sub(r"```(json|list)?", "", content).replace("```", "").strip()
            
            parsed = json.loads(cleaned_content)
            
            if isinstance(parsed, list):
                return parsed
            else:
                print(f"⚠️ [FirstNodeOrder] 리스트가 아닌 형식이 반환됨: {type(parsed)}")
                return []
                
        except json.JSONDecodeError:
            print(f"⚠️ [FirstNodeOrder] JSON 파싱 실패. 원본: {content}")
            return []
    
    def _validate_and_fix_order(self, original_list: List[str], llm_output_list: List[str]) -> List[str]:
        """
        LLM이 반환한 리스트가 원본 리스트의 모든 요소를 포함하고 있는지 검증
        - 중복 제거, 없는 요소 추가, 이상한 요소 제거 
        """
        original_set = set(original_list)
        llm_set = set(llm_output_list)

        # 일치하는 경우
        if len(original_list) == len(llm_output_list) and original_set == llm_set:
            return llm_output_list

        print(f"⚠️ [FirstNodeOrder] 순서 검증 불일치 발생! 보정 로직 실행.")
        print(f"   - 원본: {len(original_list)}개, LLM결과: {len(llm_output_list)}개")

        # 보정 
        final_list = []
        seen = set()

        # LLM 결과 중 유효한 것만 순서대로 담기
        for node_id in llm_output_list:
            if node_id in original_set and node_id not in seen:
                final_list.append(node_id)
                seen.add(node_id)
        
        # LLM이 빼먹은 것 찾아서 뒤에 붙이기
        missing_nodes = [node for node in original_list if node not in seen]
        if missing_nodes:
            print(f"   - 누락된 노드 추가됨: {missing_nodes}")
            final_list.extend(missing_nodes)

        return final_list