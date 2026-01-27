import json
from typing import Any, Dict, Tuple
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_tavily import TavilySearch

from core.contracts.types.curriculum import CurriculumGraph
from core.graphs.state_definition import CreateCurriculumOverallState
from core.prompts.concept_expansion.v1 import CONCEPT_EXPANSION_PROMPT_V1
from core.utils.get_message import get_last_ai_message

load_dotenv()

class ConceptExpansionAgent:
    def __init__(self, llm):
        self.llm = llm
        
        self.tools = [
            TavilySearch(max_results=3, topic="general")
        ]
        
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools
        )
    
    def run(self, state: CreateCurriculumOverallState) -> CreateCurriculumOverallState:
        keyword_graph = self._extract_keyword_graph(state["curriculum"])
        paper_info = state["curriculum"]["graph_meta"]
        
        messages = CONCEPT_EXPANSION_PROMPT_V1.format_messages(
            paper_info = paper_info,
            keyword_graph=json.dumps(
                keyword_graph, ensure_ascii=False
            ),
            reason=state["keyword_expand_reason"],
            keyword_ids = state["missing_concepts"]
        )
        
        print(messages)

        response = self.agent.invoke(
            {
                "messages": messages
            },
            config={
                "max_tokens": 1024,
                "tags": [
                    "agent:concept-expansion",
                    "prompt:v1",
                    "tool:tavily",
                ],
            }
        )
        
        ai_message = get_last_ai_message(response)
        parsed_response = self._parse_response(ai_message.content)
        
        expanded_graph = parsed_response.get("expanded_graph")
        
        if not self._is_valid_expanded_graph(expanded_graph):
            result = keyword_graph
        else:
            result = self._merge_graph(keyword_graph, expanded_graph)

        return result

    def _parse_response(self, text: str) -> dict:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"ConceptExpansionAgent output is not valid JSON:\n{text}"
            ) from e

        return parsed
    
    def _extract_keyword_graph(self, curriculum_graph: CurriculumGraph) -> dict:
        """
        Curriculum 그래프에서 keyword 노드만 추출하여
        표준화된 keyword 그래프 구조로 변환한다.
        """

        nodes = curriculum_graph.get("nodes", [])
        edges = curriculum_graph.get("edges", [])

        # 1. keyword 노드만 추출
        keyword_nodes = [
            {
                "keyword_id": node["keyword_id"],
                "keyword": node.get("keyword"),
                "description": node.get("description", "")
            }
            for node in nodes
        ]

        return {
            "nodes": keyword_nodes,
            "edges": edges
        }

    def _merge_graph(
        self,
        base_graph: Dict[str, Any],
        expanded_graph: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        기존 curriculum graph와 expanded_graph를 병합한다.
        - keyword_id 기준으로 node 중복 제거
        - (start, end) 기준으로 edge 중복 제거
        - 기존 구조는 유지하고 추가만 수행
        """

        # ---- Nodes 병합 ----
        base_nodes = base_graph.get("nodes", [])
        expanded_nodes = expanded_graph.get("nodes", [])

        node_map = {
            node["keyword_id"]: node
            for node in base_nodes
        }

        for node in expanded_nodes:
            keyword_id = node["keyword_id"]

            # description 없으면 None으로 보정
            if "description" not in node:
                node["description"] = None

            if keyword_id not in node_map:
                node_map[keyword_id] = node

        merged_nodes = list(node_map.values())

        # ---- Edges 병합 ----
        base_edges = base_graph.get("edges", [])
        expanded_edges = expanded_graph.get("edges", [])

        edge_set: set[Tuple[str, str]] = {
            (edge["start"], edge["end"])
            for edge in base_edges
        }

        for edge in expanded_edges:
            edge_set.add((edge["start"], edge["end"]))

        merged_edges = [
            {"start": start, "end": end}
            for start, end in edge_set
        ]

        return {
            "nodes": merged_nodes,
            "edges": merged_edges
        }

    def _is_valid_expanded_graph(self, expanded_graph: Dict[str, Any]) -> bool:
        """
        expanded_graph가 기대한 구조를 만족하는지 검증한다.
        """

        if not isinstance(expanded_graph, dict):
            return False

        nodes = expanded_graph.get("nodes")
        edges = expanded_graph.get("edges")

        if not isinstance(nodes, list) or not isinstance(edges, list):
            return False

        # ---- node 검증 ----
        for node in nodes:
            if not isinstance(node, dict):
                return False
            if "keyword_id" not in node or "keyword" not in node:
                return False
            if not isinstance(node["keyword_id"], str):
                return False
            if not isinstance(node["keyword"], str):
                return False

        # ---- edge 검증 ----
        for edge in edges:
            if not isinstance(edge, dict):
                return False
            if "start" not in edge or "end" not in edge:
                return False
            if not isinstance(edge["start"], str):
                return False
            if not isinstance(edge["end"], str):
                return False
            # reason은 optional이지만, 있으면 string이어야 함
            if "reason" in edge and not isinstance(edge["reason"], str):
                return False

        return True
