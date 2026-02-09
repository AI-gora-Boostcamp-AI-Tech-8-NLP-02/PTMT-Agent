# core/tools/semantic_scholar_paper_search_bulk.py

import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv
from langsmith import traceable

load_dotenv()

S2_API_KEY = os.environ.get("S2_API_KEY")
S2_BULK_ENDPOINT = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"


def _paper_fallback_url(paper: Dict[str, Any]) -> Optional[str]:
    paper_id = paper.get("paperId")
    if not paper_id:
        return None
    return f"https://www.semanticscholar.org/paper/{paper_id}"


def _normalize_s2_paper_item(paper: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    title = paper.get("title") or "Untitled Paper"
    url = paper.get("url") or _paper_fallback_url(paper)
    if not url:
        return None

    content = (paper.get("abstract") or "")
    citation_count = paper.get("citationCount") or 0

    return {
        "title": title,
        "url": url,
        "content": content,
        "citationCount": int(citation_count),
    }


@traceable(run_type="tool", name="Semantic Scholar Paper Bulk Search")
async def search_paper_resources(
    query: str,
    max_results: int = 2,
    fields: str = "title,url,abstract,citationCount",
    token: Optional[str] = None,
    year: Optional[str] = None,
    fields_of_study: Optional[List[str]] = None,
    min_citation_count: Optional[int] = None,
    timeout_sec: float = 15.0,
) -> List[Dict[str, Any]]:
    """
    Semantic Scholar Graph API /paper/search/bulk 를 이용해 논문 검색
    - sort=citationCount:desc 로 서버에서 정렬
    - 결과는 max_results만 반환
    """
    limit = max(1, min(int(max_results), 100))

    params: Dict[str, Any] = {
        "query": query,
        "limit": limit,
        "fields": fields,
        "sort": "citationCount:desc",  # 인용 수 내림차순 정렬 (bulk에서 지원)
    }

    if token:
        params["token"] = token 

    # optional filters
    if year:
        params["year"] = year
    if fields_of_study:
        params["fieldsOfStudy"] = ",".join(fields_of_study)
    if min_citation_count is not None:
        params["minCitationCount"] = str(int(min_citation_count))

    headers: Dict[str, str] = {}
    if S2_API_KEY:
        headers["x-api-key"] = S2_API_KEY

    try:
        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            resp = await client.get(S2_BULK_ENDPOINT, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        papers = data.get("data", [])
        if not isinstance(papers, list):
            return []

        normalized: List[Dict[str, Any]] = []
        for p in papers:
            if not isinstance(p, dict):
                continue
            n = _normalize_s2_paper_item(p)
            if n:
                normalized.append(n)

        return normalized[:max_results]

    except Exception as e:
        print(f"[Semantic Scholar Tool Error] {e}")
        return []

# uv run python -m core.tools.semantic_scholar_paper_search_bulk
if __name__ == "__main__":
    import asyncio
    import json

    async def _test():
        q = "transformer survey"
        results = await search_paper_resources(q, max_results=3)
        print(json.dumps(results, ensure_ascii=False, indent=2))

    asyncio.run(_test())
