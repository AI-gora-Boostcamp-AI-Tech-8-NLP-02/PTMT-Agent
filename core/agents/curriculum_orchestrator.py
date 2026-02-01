import json, re, asyncio
from typing import Dict, Any, List
from core.contracts.types.curriculum import CurriculumGraph, KeywordNode, Resource
from core.contracts.types.paper_info import PaperInfo
from core.contracts.curriculum_orchestrator import (
    CurriculumOrchestratorInput, 
    CurriculumOrchestratorOutput
)
from core.prompts.curriculum_orchestrator.v1 import KEYWORD_CHECK_PROMPT, RESOURCE_CHECK_PROMPT

class CurriculumOrchestrator:
    def __init__(self, llm):
        self.llm = llm
        self.kw_chain = KEYWORD_CHECK_PROMPT | llm
        self.res_chain = RESOURCE_CHECK_PROMPT | llm

    async def run(self, input_data: CurriculumOrchestratorInput) -> CurriculumOrchestratorOutput:
        paper_content = input_data["paper_content"]
        curriculum = input_data["curriculum"]
        user_info = input_data["user_info"]

        nodes: List[KeywordNode] = curriculum.get("nodes", [])
        user_level = user_info.get("level", "unknown")
        user_purpose = user_info.get("purpose", "simple_study")
        current_count= input_data.get("current_iteration_count", 0)
        MAX_ITERATIONS = 6
        
        # Rule-based 분기 
        tasks = []
        missing_desc_ids = [n["keyword_id"] for n in nodes if not n.get("description")]
        zero_resource_ids = [n["keyword_id"] for n in nodes if not n.get("resources")]

        if missing_desc_ids: tasks.append("generate_description")
        if zero_resource_ids: tasks.append("resource_search")
        
        if tasks: 
            return self.format_rule_base_result(
                tasks=tasks, 
                desc_ids=missing_desc_ids, 
                res_ids=zero_resource_ids,
                current_kw_sufficient=input_data.get("is_keyword_sufficient", True),
                current_res_sufficient=input_data.get("is_resource_sufficient", True)
            )

        if current_count+1>=MAX_ITERATIONS:
            print(f"🛑 [Orchestrator] 반복 횟수({current_count+1}) 초과. LLM 미호출.")
            return self.format_rule_base_result(
                tasks=tasks, 
                desc_ids=missing_desc_ids, 
                res_ids=zero_resource_ids,
                current_kw_sufficient=input_data.get("is_keyword_sufficient", True),
                current_res_sufficient=input_data.get("is_resource_sufficient", True)
            )

        # Keyword Check + Resource Checks
        nodes_to_check = [n for n in nodes if not n.get("is_resource_sufficient", False)]
        resource_tasks = [
            self.check_single_resource(
                node=node, 
                level=user_level, 
                purpose=user_purpose
            )
            for node in nodes_to_check
        ]

        # 키워드 충분성 체크 + 각 노드별 리소스 체크를 병렬 실행
        results = await asyncio.gather(
            self.check_keyword_sufficiency(paper_content, curriculum, user_level, user_purpose),
            *resource_tasks
        )

        kw_decision = results[0]  # 키워드 체크 결과
        res_decisions = results[1:] # 각 노드별 리소스 체크 결과들

        existing_keywords = {n.get("keyword_id") for n in nodes if n.get("keyword_id")}
        
        raw_missing_concepts = kw_decision.get("missing_concepts", [])
        
        # 기존 키워드에 포함되지 않은 개념만 필터링
        filtered_missing_concepts = [
            concept for concept in raw_missing_concepts 
            if concept in existing_keywords
        ]

        print(f"거르기전:{raw_missing_concepts}")
        print(f"거른 후:{filtered_missing_concepts}")

        insufficient_res_ids = [
            nodes_to_check[i]["keyword_id"] for i, dec in enumerate(res_decisions) 
            if not dec.get("is_resource_sufficient", True)
        ]

        # 결과 합치기 
        final_tasks = []

        if filtered_missing_concepts:
            final_tasks.append("keyword_expansion")
        if insufficient_res_ids:
            final_tasks.append("resource_search")

        res_reasoning_list = [
            f"[{nodes_to_check[i]['keyword']}]: {dec.get('reasoning')}" 
            for i, dec in enumerate(res_decisions) 
            if not dec.get("is_resource_sufficient", True)
        ]
        res_reasoning = " | ".join(res_reasoning_list) if res_reasoning_list else "All resources are sufficient."

        if not final_tasks:
            final_tasks = ["curriculum_compose"]

        return {
            "tasks": final_tasks,
            "is_keyword_sufficient": len(filtered_missing_concepts) == 0,
            "is_resource_sufficient": len(insufficient_res_ids) == 0,
            "needs_description_ids": [],
            "missing_concepts": filtered_missing_concepts,
            "insufficient_resource_ids": insufficient_res_ids,
            "keyword_reasoning": kw_decision.get("reasoning", "No keyword gaps found."),
            "resource_reasoning": res_reasoning,
        }


    async def check_keyword_sufficiency(self, paper: PaperInfo, curr: CurriculumGraph, level: str, purpose: str) -> Dict[str, Any]:
        """전체적인 키워드 구성이 논문을 커버하는지 확인"""
        response = await self.kw_chain.ainvoke({
            "paper_content": paper,
            "curriculum_json": curr,
            "user_level": level,
            "user_purpose": purpose
        }, config={"tags": ["orch-kw-check"]})
        return self.parse_json(response.content)

    async def check_single_resource(self, node: KeywordNode, level: str, purpose: str) -> Dict[str, Any]:
        """
        단일 키워드의 리소스만 충분한지 판단
        """
        response = await self.res_chain.ainvoke({
            "keyword_id": node["keyword_id"],
            "keyword": node["keyword"],
            "description": node["description"],
            "resources": node["resources"], 
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

    def format_rule_base_result(
        self, 
        tasks: List[str], 
        desc_ids: List[str], 
        res_ids: List[str],
        current_kw_sufficient: bool, 
        current_res_sufficient: bool  
    ) -> CurriculumOrchestratorOutput:
        return {
            "tasks": list(set(tasks)),
            "is_keyword_sufficient": current_kw_sufficient,
            "is_resource_sufficient": False if "resource_search" in tasks else current_res_sufficient,
            "insufficient_resource_ids": res_ids,
            "needs_description_ids": desc_ids,
            "missing_concepts": [],
            "keyword_reasoning": "Rule-base: No missing keywords detected (pre-check).",
            "resource_reasoning": "Rule-base: Missing resources/descriptions detected in nodes.",
        }