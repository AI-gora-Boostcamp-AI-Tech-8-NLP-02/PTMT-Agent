import json
import re
from typing import Dict, Any, List
from core.contracts.paper_concept_alignment import (
    PaperConceptAlignmentInput,
    PaperConceptAlignmentOutput,
    CurriculumNode,
    CurriculumEdge,
    PaperInfo
)
from core.prompts.paper_concept_alignment.v1 import PAPER_CONCEPT_ALIGNMENT_PROMPT_V1


class PaperConceptAlignmentAgent:
    """논문 내용과 커리큘럼 구조를 기반으로 각 키워드가 논문 이해에 필요한 이유를 설명하는 에이전트"""

    def __init__(self, llm, max_body_chars: int = 4000):
        """
        Args:
            llm: LangChain 호환 LLM 인스턴스
            max_body_chars: 논문 본문의 최대 문자 수
        """
        self.llm = llm
        self.chain = PAPER_CONCEPT_ALIGNMENT_PROMPT_V1 | llm
        self.max_body_chars = max_body_chars

    async def run(self, input_data: PaperConceptAlignmentInput) -> PaperConceptAlignmentOutput:
        """에이전트 실행

        Args:
            input_data: 논문 정보와 커리큘럼 데이터

        Returns:
            description이 없는 노드들에 대한 설명 딕셔너리 (왜 필요한지 근거 포함)
        """
        paper_info = input_data["paper_info"]
        curriculum = input_data["curriculum"]
        nodes = curriculum.get("nodes", [])
        edges = curriculum.get("edges", [])

        # description이 없거나 빈 노드 필터링
        nodes_without_desc = self._filter_nodes_without_description(nodes)

        if not nodes_without_desc:
            print("✅ 모든 노드에 description이 이미 존재합니다.")
            return {"descriptions": {}}

        print(f"📝 설명이 필요한 키워드 수: {len(nodes_without_desc)}")
        print(f"📊 전체 커리큘럼: 노드 {len(nodes)}개, 엣지 {len(edges)}개")

        # 논문 본문 생성
        paper_body_summary = self._format_paper_body(paper_info)

        # 전체 커리큘럼 구조 포맷팅
        curriculum_nodes = self._format_all_nodes(nodes)
        curriculum_edges = self._format_edges(edges)

        # 설명이 필요한 키워드 목록
        keywords_to_describe = self._format_keywords_to_describe(nodes_without_desc)

        try:
            response = await self.chain.ainvoke({
                "paper_title": paper_info.get("title", ""),
                "paper_abstract": paper_info.get("abstract", ""),
                "paper_body_summary": paper_body_summary,
                "curriculum_nodes": curriculum_nodes,
                "curriculum_edges": curriculum_edges,
                "keywords_to_describe": keywords_to_describe
            },
            config={
                "tags": ["paper-concept-alignment"]
            }   
            )

            descriptions = self._parse_response(response.content)
            
            print(f"✅ 생성된 설명 수: {len(descriptions)}")
            for kw_id, desc in descriptions.items():
                print(f"  - {kw_id}: {desc[:50]}...")

            return {"descriptions": descriptions}

        except Exception as e:
            print(f"❌ LLM 호출 중 오류 발생: {e}")
            return {"descriptions": {}}

    def _filter_nodes_without_description(self, nodes: List[CurriculumNode]) -> List[CurriculumNode]:
        """description이 없거나 빈 노드 필터링"""
        return [
            node for node in nodes
            if not node.get("description") or node.get("description", "").strip() == ""
        ]

    def _format_paper_body(self, paper_info: PaperInfo) -> str:
        """논문 본문을 포맷팅"""
        body = paper_info.get("body", [])
        if not body:
            return "본문 내용이 없습니다."

        body_parts = []
        total_chars = 0

        for section in body:
            subtitle = section.get("subtitle", "")
            text = section.get("text", "")
            
            section_text = f"### {subtitle}\n{text}"
            
            if total_chars + len(section_text) > self.max_body_chars:
                # 남은 공간만큼만 추가
                remaining = self.max_body_chars - total_chars
                if remaining > 100:
                    body_parts.append(f"### {subtitle}\n{text[:remaining]}...")
                break
            
            body_parts.append(section_text)
            total_chars += len(section_text)

        return "\n\n".join(body_parts)

    def _format_all_nodes(self, nodes: List[CurriculumNode]) -> str:
        """전체 노드 목록 포맷팅"""
        formatted = []
        for node in nodes:
            keyword_id = node.get("keyword_id", "")
            keyword = node.get("keyword", "")
            importance = node.get("keyword_importance", 0)
            has_desc = "✓" if node.get("description") else "✗"
            formatted.append(f"- [{keyword_id}] {keyword} (중요도: {importance}, 설명 존재: {has_desc})")
        
        return "\n".join(formatted)

    def _format_edges(self, edges: List[CurriculumEdge]) -> str:
        """엣지(학습 순서) 포맷팅"""
        if not edges:
            return "엣지 정보가 없습니다."
        
        formatted = []
        for edge in edges:
            start = edge.get("start", "")
            end = edge.get("end", "")
            formatted.append(f"- {start} → {end}")
        
        return "\n".join(formatted)

    def _format_keywords_to_describe(self, nodes: List[CurriculumNode]) -> str:
        """설명이 필요한 키워드 목록 포맷팅"""
        formatted = []
        for node in nodes:
            keyword_id = node.get("keyword_id", "")
            keyword = node.get("keyword", "")
            importance = node.get("keyword_importance", 0)
            formatted.append(f"- ID: {keyword_id}, 키워드: {keyword}, 중요도: {importance}")
        
        return "\n".join(formatted)

    def _parse_response(self, text: str) -> Dict[str, str]:
        """LLM 응답에서 JSON 추출 및 파싱"""
        try:
            # 중첩된 JSON 객체 처리를 위해 더 정교한 패턴 사용
            # 가장 바깥쪽 중괄호 찾기
            start_idx = text.find('{')
            end_idx = text.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                clean_json = text[start_idx:end_idx + 1]
                return json.loads(clean_json)
            
            # 전체 텍스트를 JSON으로 파싱 시도
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON 파싱 오류: {e}")
            print(f"원본 응답: {text[:500]}...")
            return {}
