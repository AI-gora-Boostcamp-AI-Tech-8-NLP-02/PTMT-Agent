import json
import re
from typing import Any, Dict, List, Tuple
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_tavily import TavilySearch

from core.contracts.concept_expansion import ConceptExpansionInput, ConceptExpansionOutput
from core.contracts.types.curriculum import CurriculumGraph, KeywordNode
from core.prompts.concept_expansion.v1 import CONCEPT_EXPANSION_PROMPT_V1
from core.utils.get_message import get_last_ai_message

load_dotenv()

KEYWORD_ID_PATTERN = re.compile(r"^key-(\d{3})$")

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
    
    def run(self, input: ConceptExpansionInput) -> ConceptExpansionOutput:
        # Input 추출
        keyword_graph = self._extract_keyword_graph(input["curriculum"])
        paper_info = input["curriculum"]["graph_meta"]
        
        # 프롬프트 적용
        messages = CONCEPT_EXPANSION_PROMPT_V1.format_messages(
            paper_info = paper_info,
            keyword_graph=json.dumps(
                keyword_graph, ensure_ascii=False
            ),
            reason=input["keyword_expand_reason"],
            keyword_ids = input["missing_concepts"]
        )

        # agent 실행
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
        
        # llm 결과 parsing
        expanded_graph = self._parse_response(response)
        
        # normalization
        expanded_graph = self._normalize_expanded_graph(
            base_graph=keyword_graph,
            expanded_graph=expanded_graph,
        )
        
        # 기존 그래프와 병합
        expanded_graph = self._merge_graph(keyword_graph, expanded_graph)
        
        # 기존 커리큘럼과 병합
        merged_curriculum = self._merge_expansion_into_curriculum(input["curriculum"], expanded_graph)
        
        result: ConceptExpansionOutput = {
            "curriculum": merged_curriculum
        }

        return result

    def _parse_response(self, response) -> Dict[str, Any]:
        ai_message = get_last_ai_message(response)
        
        try:
            parsed = json.loads(ai_message.content)
            expanded_graph = parsed.get("expanded_graph")
        except Exception:
            return {"nodes": [], "edges": []}

        if not self._is_valid_expanded_graph(expanded_graph):
            return {"nodes": [], "edges": []}
        
        return expanded_graph

    def _normalize_expanded_graph(
        self,
        base_graph: Dict[str, Any],
        expanded_graph: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        - keyword_id 재부여
        - edge 재매핑
        """
        if not expanded_graph.get("nodes"):
            return {"nodes": [], "edges": []}

        return self._reassign_keyword_ids(
            base_graph=base_graph,
            expanded_graph=expanded_graph,
        )
    
    def _extract_keyword_graph(self, curriculum_graph: CurriculumGraph) -> Dict[str, Any]:
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

    def _reassign_keyword_ids(
        self,
        base_graph: Dict[str, Any],
        expanded_graph: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        base_graph의 keyword_id를 기준으로
        expanded_graph의 node들에 새로운 keyword_id를 순차적으로 부여한다.
        """

        # base_graph에서 마지막 keyword 번호 찾기
        max_index = -1
        for node in base_graph.get("nodes", []):
            match = KEYWORD_ID_PATTERN.match(node.get("keyword_id", ""))
            if match:
                max_index = max(max_index, int(match.group(1)))

        next_index = max_index + 1

        # expanded_graph node에 새 keyword_id 부여
        id_mapping: Dict[str, str] = {}
        new_nodes: List[Dict[str, Any]] = []

        for node in expanded_graph.get("nodes", []):
            old_id = node.get("keyword_id")

            new_id = f"key-{next_index:03d}"
            next_index += 1

            id_mapping[old_id] = new_id

            new_node = dict(node)
            new_node["keyword_id"] = new_id
            new_node.setdefault("description", None)

            new_nodes.append(new_node)

        # edge 재매핑
        new_edges = []
        for edge in expanded_graph.get("edges", []):
            start = edge.get("start")
            end = edge.get("end")

            if start in id_mapping and end in id_mapping:
                new_edges.append(
                    {
                        "start": id_mapping[start],
                        "end": id_mapping[end],
                    }
                )

        return {
            "nodes": new_nodes,
            "edges": new_edges,
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

    def _merge_expansion_into_curriculum(
        self,
        curriculum: CurriculumGraph,
        expansion_result: Dict[str, Any]
    ) -> CurriculumGraph:
        """
        CurriculumGraph 업데이트 한다.
        """

        expanded_nodes = expansion_result.get("nodes", [])
        expanded_edges = expansion_result.get("edges", [])

        # ---- 기존 노드 맵 ----
        node_map: Dict[str, KeywordNode] = {
            node["keyword_id"]: node
            for node in curriculum["nodes"]
        }

        # ---- 새 노드만 추가 ----
        for raw_node in expanded_nodes:
            kid = raw_node.get("keyword_id")
            if not kid:
                continue

            if kid not in node_map:
                node_map[kid] = {
                    "keyword_id": kid,
                    "keyword": raw_node.get("keyword", ""),
                    "description": "",
                    "keyword_importance": None,
                    "is_resource_sufficient": False,
                    "is_necessary": None,
                    "resources": []
                }

        merged_nodes = list(node_map.values())

        # ---- Edge 병합 ----
        edge_set: set[Tuple[str, str]] = {
            (edge["start"], edge["end"])
            for edge in curriculum["edges"]
        }

        for edge in expanded_edges:
            start, end = edge.get("start"), edge.get("end")
            if not start or not end:
                continue
            edge_set.add((start, end))

        merged_edges = [
            {"start": start, "end": end}
            for start, end in edge_set
        ]

        return {
            "graph_meta": curriculum["graph_meta"],
            "nodes": merged_nodes,
            "edges": merged_edges
        }
