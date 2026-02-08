# core/agents/resource_discovery_agent.py

import asyncio
import json
import re
import time
from typing import List, Dict, Any, Optional
from langsmith import traceable

from core.contracts.resource_discovery import ResourceDiscoveryAgentInput, ResourceDiscoveryAgentOutput
from core.prompts.resource_discovery.v6 import QUERY_GEN_PROMPT_V6

from core.tools.tavily_search import search_web_resources
from core.tools.serper_web_search import search_web_resources_serper
from core.tools.serper_video_search import search_video_resources
from core.tools.semantic_scholar_paper_search import search_paper_resources

from core.agents.study_load_estimation_agent import StudyLoadEstimationAgent
from core.utils.resource_planner import plan_tools
from core.utils.resource_ranker import select_top_resources
from core.utils.timeout import async_timeout


class ResourceDiscoveryAgent:
    """
    목표:
    - 키워드별로:
      1) 쿼리 생성(기존 v3 유지: web/video용 1개)
      2) paper_query는 f"{keyword} survey"
      3) pref_types에 따라 planner가 tool 조합/분배
      4) tool 실행 -> 후보 수집 -> url dedupe
      5) 키워드 단위 배치 평가(StudyLoadEstimationAgent)
      6) 랭킹/리랭킹 -> 최종 N=3, min_pref=1
    """
    def __init__(self, llm_discovery, llm_estimation):
        # 검색용 LLM (쿼리 재생성)
        self.llm_discovery = llm_discovery
        self.query_chain = QUERY_GEN_PROMPT_V6 | llm_discovery
        
        # 평가용 LLM 
        self.llm_estimation = llm_estimation
        
        self.sem = asyncio.Semaphore(5)

    @async_timeout(90)
    @traceable(run_type="chain", name="Resource Discovery Agent") 
    async def run(self, input_data: ResourceDiscoveryAgentInput) -> ResourceDiscoveryAgentOutput:
        """에이전트의 메인 실행 로직"""
        all_resources = []
        tasks = []

        for node in input_data["nodes"]:
            if node.get("is_resource_sufficient", False):
                continue
            
            # 디버깅
            k_id=node.get("keyword_id")
            is_resource_sufficient=node.get("is_resource_sufficient", False)
            print(f"{k_id} -> Searching Resources : 충분 정도 : {is_resource_sufficient}")

            # 중복 URL 수집
            existing_urls = {res.get("url") for res in node.get("resources", []) if res.get("url")}
            
            # 검색 태스크 생성
            tasks.append(self.process_single_node(
                paper_name=input_data["paper_name"],
                node=node,
                user_level=input_data["user_level"],
                pref_types=input_data["pref_types"],
                excluded_urls=existing_urls
            ))

        # 병렬 검색 수행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, Exception):
                print(f"❌ [ResourceDiscoveryAgent] Task Error: {res}")
                import traceback
                traceback.print_exception(type(res), res, res.__traceback__)
            else:
                all_resources.extend(res)

        return {"evaluated_resources": all_resources}

    async def process_single_node(
        self,
        paper_name: str,
        node: Dict[str, Any],
        user_level: str,
        pref_types: List[str],
        excluded_urls: set,
    ) -> List[Dict[str, Any]]:
        """
        단일 키워드에 대해:
        - tool plan 생성
        - 후보 수집 및 dedupe
        - 키워드 단위 배치 평가
        - 랭킹 후 top3 반환
        """
        async with self.sem:
            keyword = node.get("keyword", "")
            keyword_id = node.get("keyword_id", "")
            description = node.get("description", "")
            search_direction = node.get("resource_reason") or ""

            time.sleep(1)

            # web/video 공용 쿼리 생성
            web_query = await self._generate_web_query(
                paper_name=paper_name,
                keyword=keyword,
                description=description,
                search_direction=search_direction,
            )

            # paper 쿼리: keyword + survey (고정)
            paper_query = f"{keyword} survey".strip()

            # Rule-based tool plan
            tool_plan = plan_tools(pref_types)

            # tool별 검색 실행 -> candidate 수집
            candidates: List[Dict[str, Any]] = []
            seen_urls = set()

            for step in tool_plan:
                tool = step["tool"]
                max_results = int(step["max_results"])

                if tool == "tavily":
                    # Tavily는 공통: web_query 사용
                    results = await search_web_resources(web_query, max_results=max_results)
                    candidates.extend(
                        self._normalize_generic_results(
                            results=results,
                            keyword_id=keyword_id,
                            keyword=keyword,
                            query=web_query,
                            default_type="web_doc",
                            source_tool="tavily",
                        )
                    )

                elif tool == "serper_web":
                    results = await search_web_resources_serper(web_query, max_results=max_results)
                    candidates.extend(
                        self._normalize_generic_results(
                            results=results,
                            keyword_id=keyword_id,
                            keyword=keyword,
                            query=web_query,
                            default_type="web_doc",
                            source_tool="serper_web",
                        )
                    )

                elif tool == "serper_video":
                    results = await search_video_resources(web_query, max_results=max_results)
                    candidates.extend(
                        self._normalize_video_results(
                            results=results,
                            keyword_id=keyword_id,
                            keyword=keyword,
                            query=web_query,
                            source_tool="serper_video",
                        )
                    )

                elif tool == "semantic_scholar":
                    results = await search_paper_resources(paper_query, max_results=max_results)
                    candidates.extend(
                        self._normalize_paper_results(
                            results=results,
                            keyword_id=keyword_id,
                            keyword=keyword,
                            query=paper_query,
                            source_tool="semantic_scholar",
                        )
                    )

            # url 기준 중복 제거
            deduped: List[Dict[str, Any]] = []
            for c in candidates:
                url = c.get("url")
                if not url:
                    continue
                if url in seen_urls or url in excluded_urls:
                    continue
                seen_urls.add(url)
                deduped.append(c)

            if not deduped:
                return []

            # 키워드 단위 배치 평가
            estimation_agent = StudyLoadEstimationAgent(self.llm_estimation)

            # StudyLoadEstimationAgent는 keyword 기준 그룹핑을 내부에서 하므로
            # 여기서는 해당 keyword의 리스트만 넣으면 됨
            estimation_input = {
                "resources": deduped,
                "user_level": user_level, 
                "purpose": ""
            }
            estimation_result = await estimation_agent.run(estimation_input)
            evaluated = estimation_result.get("evaluated_resources", [])

            # 리소스 랭킹 및 top3 (기본값: N=3, min_pref=1)
            top3 = select_top_resources(evaluated, pref_types=pref_types, top_n=3, min_pref=1)

            return top3

    @staticmethod
    def _extract_first_json_object(text: str) -> Optional[str]:
        """응답에서 첫 번째 완전한 JSON 객체만 추출 (JSON 뒤에 Explanation 등이 붙은 경우 대비)."""
        if not text or "{" not in text:
            return None
        start = text.index("{")
        depth = 0
        in_string = False
        escape = False
        quote_char = None
        i = start
        while i < len(text):
            c = text[i]
            if escape:
                escape = False
                i += 1
                continue
            if c == "\\" and in_string:
                escape = True
                i += 1
                continue
            if in_string:
                if c == quote_char:
                    in_string = False
                i += 1
                continue
            if c in ('"', "'"):
                in_string = True
                quote_char = c
                i += 1
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
            i += 1
        return None

    async def _generate_web_query(
        self,
        paper_name: str,
        keyword: str,
        description: str,
        search_direction: str,
    ) -> str:
        response = await self.query_chain.ainvoke(
            {
                "paper_name": paper_name,
                "keyword": keyword,
                "search_direction": search_direction,
            },
            config={"tags": ["rs-discovery-querygen"]},
        )

        raw = (response.content or "").strip()
        # v5 프롬프트: JSON {"query": "..."} 형식 파싱
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw)
        cleaned = re.sub(r"\s*```\s*$", "", cleaned).strip()
        # LLM이 JSON 뒤에 Explanation 등 부가 설명을 붙이는 경우 대비: 첫 번째 완전한 JSON 객체만 추출
        json_str = self._extract_first_json_object(cleaned)
        if json_str is None:
            json_str = cleaned
        try:
            data = json.loads(json_str)
            if isinstance(data, dict) and data.get("query"):
                return data["query"].strip() or keyword
        except (json.JSONDecodeError, TypeError):
            print(f"⚠️ [ResourceDiscoveryAgent] JSON 파싱 실패: {cleaned[:500]}")
            pass
        # JSON 파싱 실패 시 첫 줄에서 쿼리 추출 (폴백)
        lines = [ln.strip() for ln in raw.split("\n") if ln.strip()][:1]
        if lines:
            q = re.sub(r"^\d+[\.\s\-]+", "", lines[0]).strip()
            if q:
                return q
        return keyword

    def _normalize_generic_results(
        self,
        results: List[Dict[str, Any]],
        keyword_id: str,
        keyword: str,
        query: str,
        default_type: str,
        source_tool: str,
    ) -> List[Dict[str, Any]]:
        """
        Tavily/Serper web처럼 title/url/content 형태를 공통 정규화
        """
        out: List[Dict[str, Any]] = []
        for r in results or []:
            url = r.get("url")
            if not url:
                continue
            title = r.get("title") or "Untitled Resource"
            content = (r.get("content") or "")[:2000]

            # 간단 url 규칙으로 video 감지(혼합 결과 대비)
            r_type = default_type
            if "youtube.com" in url or "youtu.be" in url:
                r_type = "video"

            out.append({
                "keyword_id": keyword_id,
                "keyword": keyword,
                "resource_name": title,
                "url": url,
                "raw_content": content,
                "query": query,
                "type": r_type,
                "type_hint": r_type,
                "source_tool": source_tool,
            })
        return out

    def _normalize_video_results(
        self,
        results: List[Dict[str, Any]],
        keyword_id: str,
        keyword: str,
        query: str,
        source_tool: str,
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for r in results or []:
            url = r.get("url")
            if not url:
                continue
            title = r.get("title") or "Untitled Video"
            content = (r.get("content") or "")[:2000]
            duration = r.get("duration")

            out.append({
                "keyword_id": keyword_id,
                "keyword": keyword,
                "resource_name": title,
                "url": url,
                "raw_content": content,
                "query": query,
                "type": "video",
                "type_hint": "video",
                "duration": duration,
                "source_tool": source_tool,
            })
        return out

    def _normalize_paper_results(
        self,
        results: List[Dict[str, Any]],
        keyword_id: str,
        keyword: str,
        query: str,
        source_tool: str,
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for r in results or []:
            url = r.get("url")
            if not url:
                continue
            title = r.get("title") or "Untitled Paper"
            content = (r.get("content") or "")[:2000]
            citation_count = r.get("citationCount")

            out.append({
                "keyword_id": keyword_id,
                "keyword": keyword,
                "resource_name": title,
                "url": url,
                "raw_content": content,
                "query": query,
                "type": "paper",
                "type_hint": "paper",
                "citationCount": citation_count,
                "source_tool": source_tool,
            })
        return out