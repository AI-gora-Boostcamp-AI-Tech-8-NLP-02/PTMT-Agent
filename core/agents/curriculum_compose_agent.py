import json
import re
from typing import Dict, Any, List, Tuple
from core.contracts.curriculum_compose import (
    CurriculumComposeInput,
    CurriculumComposeOutput,
    CurriculumNode,
    CurriculumEdge
)
from core.prompts.curriculum_compose.v1 import CURRICULUM_COMPOSE_PROMPT_V1


class CurriculumComposeAgent:
    """사용자 정보를 바탕으로 커리큘럼 내 자료(Resource)를 최적화(삭제/보존/강조)하는 에이전트"""

    def __init__(self, llm):
        self.llm = llm
        self.chain = CURRICULUM_COMPOSE_PROMPT_V1 | llm

    async def run(self, input_data: CurriculumComposeInput) -> CurriculumComposeOutput:
        """에이전트 실행"""
        user_info = input_data["user_info"]
        curriculum = input_data["curriculum"]
        nodes = curriculum.get("nodes", [])

        # 1. 모든 리소스를 수집 및 포맷팅
        all_resources = []
        for node in nodes:
            for res in node.get("resources", []):
                # 리소스 식별을 위해 node_keyword도 같이 기록하면 좋지만, 
                # 프롬프트에는 리소스 정보 위주로 전달
                res_info = {
                    "resource_id": res.get("resource_id"),
                    "resource_name": res.get("resource_name"),
                    "type": res.get("type"),
                    "keyword": node.get("keyword"), # 맥락 정보
                    "difficulty": res.get("difficulty"),
                    "importance": res.get("importance"),
                    "study_load": res.get("study_load")
                }
                all_resources.append(res_info)

        if not all_resources:
            return {"curriculum": curriculum}

        formatted_resources, total_load = self._format_resources(all_resources)

        # 2. LLM 호출
        try:
            response = await self.chain.ainvoke({
                "user_purpose": user_info.get("purpose", ""),
                "user_level": user_info.get("level", ""),
                "user_known_concepts": ", ".join(user_info.get("known_concept", [])),
                "user_total_hours": user_info.get("budgeted_time", {}).get("total_hours", ""),
                "current_total_load": f"{total_load:.1f}",
                "paper_title": curriculum["graph_meta"].get("title", ""),
                "formatted_resources": formatted_resources
            },
            config={
                "tags": ["curriculum-compose"]
            })
            
            parsed_result = self._parse_json(response.content)
            classifications = parsed_result.get("resource_classifications", [])
            
        except Exception as e:
            print(f"❌ LLM Classification Failed: {e}")
            return {"curriculum": curriculum}

        # 3. 결과 매핑 (resource_id -> action)
        action_map = {item["resource_id"]: item["action"] for item in classifications}

        # 4. 커리큘럼 업데이트 (Resources 필터링 및 업데이트)
        new_nodes = []
        for node in nodes:
            new_node = node.copy()
            original_resources = node.get("resources", [])
            new_resources = []
            
            for res in original_resources:
                rid = res.get("resource_id")
                action = action_map.get(rid, "PRESERVE") # 기본값 PRESERVE

                if action == "DELETE":
                    # print(f"🗑️ [DELETE Resource] {res.get('resource_name')} ({rid})")
                    continue
                
                new_res = res.copy()
                if action == "EMPHASIZE":
                    new_res["is_necessary"] = True
                else: # PRESERVE
                    new_res["is_necessary"] = False
                
                new_resources.append(new_res)
            
            new_node["resources"] = new_resources
            new_nodes.append(new_node)

        new_curriculum = curriculum.copy()
        new_curriculum["nodes"] = new_nodes
        
        return {"curriculum": new_curriculum}

    def _format_resources(self, resources: List[Dict[str, Any]]) -> Tuple[str, float]:
        lines = []
        total_load = 0.0
        for r in resources:
            load = float(r.get('study_load', 0) or 0)
            total_load += load
            line = f"- [{r['resource_id']}] {r['resource_name']} (Type: {r['type']}, Keyword: {r['keyword']}, Diff: {r['difficulty']}, Load: {load}h)"
            lines.append(line)
        return "\n".join(lines), total_load

    def _parse_json(self, text: str) -> Dict[str, Any]:
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            json_str = match.group() if match else text
            return json.loads(json_str)
        except Exception:
            return {}
