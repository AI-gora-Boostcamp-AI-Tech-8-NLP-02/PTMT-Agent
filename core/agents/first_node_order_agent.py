import json, re, asyncio
from typing import Dict, Any, List
from core.contracts.types.curriculum import CurriculumGraph, KeywordNode, Resource
from core.contracts.types.paper_info import PaperInfo
from core.contracts.first_node_order_agent import (
    FirstNodeOrderAgentInput, 
    FirstNodeOrderAgentOutput
)
# from core.prompts.first_node_order.v1 import FIRST_ORDER_PROMPT_V1
from core.prompts.first_node_order.v2 import FIRST_ORDER_PROMPT_V2

class FirstNodeOrderAgent:
    def __init__(self, llm):
        self.llm = llm
        self.order_chain = FIRST_ORDER_PROMPT_V2 | llm
        

    async def run(self, input_data: FirstNodeOrderAgentInput) -> FirstNodeOrderAgentOutput:
        paper_content = input_data["paper_content"]
        curriculum = input_data["curriculum"]
        user_info = input_data["user_info"]

        user_level = user_info.get("level", "unknown")
        user_purpose = user_info.get("purpose", "simple_study")

        first_nodes=self._get_first_nodes(curriculum)
        
        chain_input = {
            "first_nodes": json.dumps(first_nodes, ensure_ascii=False),
            "paper_content": curriculum["graph_meta"]["summarize"], 
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

        #final_order = self._reorder_by_necessary_and_cap(curriculum, final_order)

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
        """문자열을 JSON으로 파싱하여 {"reason": "...", "results": [...]} 형식에서 results 리스트 추출. reason은 출력만 하고 반환하지 않음."""
        try:
            cleaned_content = re.sub(r"```(json|list)?", "", content).replace("```", "").strip()
            parsed = json.loads(cleaned_content)

            if isinstance(parsed, dict) and "results" in parsed:
                reason = parsed.get("reason")
                if reason is not None and isinstance(reason, str) and reason.strip():
                    print(f"📋 [FirstNodeOrder] reason: {reason.strip()}")
                results = parsed["results"]
                if isinstance(results, list):
                    return results
                print(f"⚠️ [FirstNodeOrder] 'results'가 리스트가 아님: {type(results)}")
                return []
            if isinstance(parsed, list):
                # 이전 형식 호환: 리스트만 반환한 경우
                return parsed
            print(f"⚠️ [FirstNodeOrder] 기대한 JSON 형식이 아님 (reason/results 또는 list): {type(parsed)}")
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

        # 디버깅: 불일치 상세 출력
        extra_ids = list(llm_set - original_set)  # LLM이 넣은 잘못된 ID
        missing_ids = list(original_set - llm_set)  # LLM이 빼먹은 ID
        print("⚠️ [FirstNodeOrder] 순서 검증 불일치 발생! 보정 로직 실행.")
        print(f"   - 원본 개수: {len(original_list)}개  |  LLM 결과 개수: {len(llm_output_list)}개")
        print(f"   - 원본 리스트: {original_list}")
        print(f"   - LLM 결과 리스트: {llm_output_list}")
        if extra_ids:
            print(f"   - [무시] 원본에 없는 ID (LLM이 잘못 포함): {extra_ids}")
        if missing_ids:
            print(f"   - [추가 예정] 원본에 있으나 LLM이 누락: {missing_ids}")

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
            print(f"   - 보정 후 누락 노드 추가: {missing_nodes}")
            final_list.extend(missing_nodes)

        return final_list

    def _reorder_by_necessary_and_cap(
        self, curriculum: Dict[str, Any], order_list: List[str]
    ) -> List[str]:
        """
        graph에서 시작 노드의 is_keyword_necessary를 확인한 뒤:
        1. is_keyword_necessary=False 인 노드는 리스트 후방으로 재배치 (false 끼리의 순서는 유지).
        2. necessary가 5개 이하면 상위 5개만 최종 학습 순서로, 6개 이상이면 전부 포함.
        """
        nodes = curriculum.get("nodes", [])
        id_to_necessary = {
            n["keyword_id"]: bool(n.get("is_keyword_necessary", False))
            for n in nodes
        }
        id_to_keyword = {n["keyword_id"]: n.get("keyword", n["keyword_id"]) for n in nodes}

        necessary_first = [nid for nid in order_list if id_to_necessary.get(nid, False)]
        not_necessary = [nid for nid in order_list if not id_to_necessary.get(nid, False)]
        reordered = necessary_first + not_necessary

        necessary_count = len(necessary_first)
        # is_necessary 개수 및 해당 노드 출력
        necessary_labels = [f"{nid}({id_to_keyword.get(nid, nid)})" for nid in necessary_first]
        print(f"📌 [FirstNodeOrder] is_keyword_necessary=True 인 노드: {necessary_count}개 → {necessary_labels}")
        not_necessary_labels = [f"{nid}({id_to_keyword.get(nid, nid)})" for nid in not_necessary]
        print(f"   is_keyword_necessary=False 인 노드: {len(not_necessary)}개 → {not_necessary_labels}")

        if necessary_count <= 5:
            final_order = reordered[:5]
            print(f"📌 [FirstNodeOrder] is_keyword_necessary={necessary_count}개(≤5) → 상위 5개만 최종 순서: {final_order}")
        else:
            final_order = reordered
            print(f"📌 [FirstNodeOrder] is_keyword_necessary={necessary_count}개(≥6) → 전체 포함 최종 순서 (총 {len(final_order)}개)")

        return final_order