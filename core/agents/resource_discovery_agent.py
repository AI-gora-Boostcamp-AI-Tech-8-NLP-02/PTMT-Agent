import asyncio
import re
from typing import List, Dict, Any
from core.contracts.types.curriculum import KeywordNode, Resource
from core.contracts.resource_discovery import ResourceDiscoveryAgentInput, ResourceDiscoveryAgentOutput
from core.prompts.resource_discovery.v1 import QUERY_GEN_PROMPT_V1
from core.tools.tavily_search import search_web_resources
from core.agents.study_load_estimation_agent import StudyLoadEstimationAgent

class ResourceDiscoveryAgent:
    def __init__(self, llm_discovery, llm_estimation):
        # 검색용 LLM 
        self.llm_discovery = llm_discovery
        self.query_chain = QUERY_GEN_PROMPT_V1 | llm_discovery
        
        # 평가용 LLM
        self.llm_estimation = llm_estimation
        
        self.sem = asyncio.Semaphore(5)

    async def run(self, input_data: ResourceDiscoveryAgentInput) -> ResourceDiscoveryAgentOutput:
        """에이전트의 메인 실행 로직"""
        all_resources = []
        tasks = []

        for node in input_data["nodes"]:
            if node.get("is_resource_sufficient", False):
                continue
            
            # 디버깅
            is_resource_sufficient=node.get("is_resource_sufficient", False)
            k_id=node.get("keyword_id")
            print(f"✅{k_id} -> Searching Resources : 충분 정도 : {is_resource_sufficient}")

            # 중복 URL 수집
            existing_urls = {res.get("url") for res in node.get("resources", []) if res.get("url")}
            
            # 검색 태스크 생성
            tasks.append(self.process_single_node(
                node=node,
                user_level=input_data["user_level"],
                pref_types=input_data["pref_types"],
                excluded_urls=existing_urls
            ))

        # 병렬 검색 수행
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res in results:
            if not isinstance(res, Exception):
                all_resources.extend(res)

        # Estimation 호출
        estimation_agent = StudyLoadEstimationAgent(self.llm_estimation)
        estimation_input = {
            "resources": all_resources,
            "user_level": input_data["user_level"],
            "purpose": input_data["purpose"]
        }
        
        # 에이전트의 run 메서드 호출
        estimation_result = await estimation_agent.run(estimation_input)
        
        # 최종 결과 반환
        return {"evaluated_resources": estimation_result["evaluated_resources"]}

    async def process_single_node(self, node, user_level, pref_types, excluded_urls):
        """단일 키워드 자료 검색"""
        async with self.sem:
            # 쿼리 생성
            response = await self.query_chain.ainvoke({
                "keyword": node["keyword"],
                "description": node["description"]
            },config={"tags": ["rs-discovery"]})
            
            raw_queries = response.content.strip().split('\n')

            queries = [
                re.sub(r'^\d+[\.\s\-]+', '', q).strip() 
                for q in raw_queries if q.strip()
            ][:1] # 두 개만 사용
            keyword_resources = []
            seen_urls = set()

            for query in queries:
                # Tavily 검색
                search_results = await search_web_resources(query, max_results=1)
                for res in search_results:
                    url = res.get("url")
                    if not url or url in seen_urls or url in excluded_urls:
                        continue
                    
                    seen_urls.add(url)
                    keyword_resources.append({
                        "keyword_id": node["keyword_id"],
                        "keyword": node["keyword"],
                        "resource_name": res.get("title", "Untitled Resource"),
                        "url": url,
                        "raw_content": (res.get("content") or "")[:1000],
                        "query": query
                    })
            return keyword_resources


