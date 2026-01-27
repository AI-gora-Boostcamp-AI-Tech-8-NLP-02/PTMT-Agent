import json, re, asyncio
from typing import Dict, Any, List
from core.prompts.curriculum_orchestrator.v1 import KEYWORD_CHECK_PROMPT, RESOURCE_CHECK_PROMPT

class CurriculumOrchestrator:
    def __init__(self, llm):
        self.llm = llm
        self.kw_chain = KEYWORD_CHECK_PROMPT | llm
        self.res_chain = RESOURCE_CHECK_PROMPT | llm

    async def run(
        self, 
        paper_content: Dict[str, Any], 
        curriculum: Dict[str, Any], 
        user_info: Dict[str, Any] 
    ) -> Dict[str, Any]:
        
        nodes = curriculum.get("nodes", [])
        user_level = user_info.get("level", "unknown")
        user_purpose = user_info.get("purpose", "simple_study")

        # Rule-based 분기 
        tasks = []
        missing_desc_ids = [n["keyword_id"] for n in nodes if not n.get("description")]
        zero_resource_ids = [n["keyword_id"] for n in nodes if not n.get("resources")]

        if missing_desc_ids: tasks.append("generate_description")
        if zero_resource_ids: tasks.append("resource_search")
        
        if tasks: 
            return self.format_rule_base_result(tasks, missing_desc_ids, zero_resource_ids)

        # Keyword Check + Resource Checks
        # 모든 키워드에 대해 리소스 체크 태스크 생성
        resource_tasks = []
        for node in nodes:
            # LLM에게 전달할 노드의 추출 
            node_info_for_llm = {
                "keyword_id": node.get("keyword_id"),
                "keyword": node.get("keyword"),
                "description": node.get("description"),
                "resources": node.get("resources", []) 
            }
            
            # 병렬 실행을 위한 리스트에 추가
            task = self.check_single_resource(
                node_info_for_llm, 
                user_level, 
                user_purpose
            )
            resource_tasks.append(task)

        # 키워드 충분성 체크 + 각 노드별 리소스 체크를 병렬 실행
        results = await asyncio.gather(
            self.check_keyword_sufficiency(paper_content, curriculum, user_level, user_purpose),
            *resource_tasks
        )

        kw_decision = results[0]  # 키워드 체크 결과
        res_decisions = results[1:] # 각 노드별 리소스 체크 결과들

        # 결과 합치기 
        final_tasks = []
        insufficient_res_ids = [
            nodes[i]["keyword_id"] for i, dec in enumerate(res_decisions) 
            if not dec.get("is_resource_sufficient", True)
        ]

        if not kw_decision.get("is_keyword_sufficient", True):
            final_tasks.append("keyword_expansion")
        if insufficient_res_ids:
            final_tasks.append("resource_search")

        res_reasoning_list = [
            f"[{nodes[i]['keyword']}]: {dec.get('reasoning')}" 
            for i, dec in enumerate(res_decisions) 
            if not dec.get("is_resource_sufficient", True)
        ]
        res_reasoning = " | ".join(res_reasoning_list) if res_reasoning_list else "All resources are sufficient."


        return {
            "tasks": final_tasks,
            "is_keyword_sufficient": kw_decision.get("is_keyword_sufficient", True),
            "is_resource_sufficient": len(insufficient_res_ids) == 0,
            "missing_concepts": kw_decision.get("missing_concepts", []),
            "insufficient_resource_ids": insufficient_res_ids,
            "keyword_reasoning": kw_decision.get("reasoning", "No keyword gaps found."),
            "resource_reasoning": res_reasoning,
        }


    async def check_keyword_sufficiency(self, paper, curr, level, purpose):
        """전체적인 키워드 구성이 논문을 커버하는지 확인"""
        response = await self.kw_chain.ainvoke({
            "paper_content": paper,
            "curriculum_json": curr,
            "user_level": level,
            "user_purpose": purpose
        }, config={"tags": ["orch-kw-check"]})
        return self.parse_json(response.content)

    async def check_single_resource(self, node_info: Dict[str, Any],  level: str, purpose: str):
        """
        단일 키워드의 리소스만 충분한지 판단
        """
        response = await self.res_chain.ainvoke({
            **node_info,
            "user_level": level,
            "user_purpose": purpose
        }, config={"tags": ["orch-res-check"]})
        return self.parse_json(response.content)

    def parse_json(self, text: str) -> Dict[str, Any]:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try: return json.loads(match.group())
            except: return {}
        return {}

    def format_rule_base_result(self, tasks, desc_ids, res_ids):
        return {
            "tasks": list(set(tasks)),
            "is_resource_sufficient": False if "resource_search" in tasks else True,
            "insufficient_resource_ids": res_ids,
            "needs_description_ids": desc_ids,
            "missing_concepts": [],
            "keyword_reasoning": "Rule-base: No missing keywords detected.",
            "resource_reasoning": "Rule-base: Missing resources detected in nodes.",
        }