# core/tools/semantic_scholar_paper_search.py

import os
from typing import Any, Dict, List, Optional

import httpx
import random
import asyncio
from dotenv import load_dotenv
from langsmith import traceable

load_dotenv()

S2_API_KEY = os.environ.get("S2_API_KEY")  # optional
S2_ENDPOINT = "https://api.semanticscholar.org/graph/v1/paper/search"


def _paper_fallback_url(paper: Dict[str, Any]) -> Optional[str]:
    """
    Semantic Scholar 응답에 url이 없을 때(혹은 null) paperId로 페이지 URL 구성 -> 혹시 몰라 구성
    """
    paper_id = paper.get("paperId")
    if not paper_id:
        return None
    return f"https://www.semanticscholar.org/paper/{paper_id}"


def _normalize_s2_paper_item(paper: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    title = paper.get("title") or "Untitled Paper"
    url = paper.get("url") or _paper_fallback_url(paper)
    if not url:
        return None

    abstract = paper.get("abstract") or ""
    content = abstract if abstract.strip() else ""

    return {
        "title": title,
        "url": url,
        "content": content,
        "citationCount": paper.get("citationCount"),  # 필요 없지만 혹시 몰라 반환
    }


@traceable(run_type="tool", name="Semantic Scholar Paper Search")
async def search_paper_resources(
    query: str,
    max_results: int = 2,
    offset: int = 0,
    fields: str = "title,url,abstract,citationCount",
    # Semantic Scholar search에서 제공하는 필터링 파라미터
    year: Optional[str] = None, 
    fields_of_study: Optional[List[str]] = None, # ["Computer Science", "Mathematics", "Engineering", "Linguistics", "Psychology"],
    min_citation_count: Optional[int] = None,
    timeout_sec: float = 15.0,
    max_retries: int = 3, 
) -> List[Dict[str, Any]]:
    """
    Semantic Scholar Graph API /paper/search 를 이용해 논문 검색
    """
    # API는 limit <= 100 제약
    limit = max(1, min(int(max_results), 100))

    params: Dict[str, Any] = {
        "query": query,
        "offset": offset,
        "limit": limit,
        "fields": fields,
    }

    # optional filters
    if year:
        params["year"] = year
    if fields_of_study:
        params["fieldsOfStudy"] = ",".join(fields_of_study)
    if min_citation_count is not None:
        params["minCitationCount"] = str(int(min_citation_count))

    headers = {}
    if S2_API_KEY:
        headers["x-api-key"] = S2_API_KEY 

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout_sec) as client:
                resp = await client.get(S2_ENDPOINT, params=params, headers=headers)

            # 429 처리
            if resp.status_code == 429:
                retry_after = resp.headers.get("Retry-After")
                if retry_after:
                    wait_s = float(retry_after)
                else:
                    # exponential backoff + jitter
                    wait_s = min(2 ** attempt, 30) + random.random()
                print(f"[Semantic Scholar] 429 rate-limited. sleep {wait_s:.1f}s (attempt {attempt}/{max_retries})")
                await asyncio.sleep(wait_s)
                continue

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
                if len(normalized) >= max_results:
                    break

            return normalized

        except httpx.HTTPStatusError as e:
            # 5xx 등도 재시도할지 여부
            status = e.response.status_code if e.response else None
            if status and 500 <= status < 600 and attempt < max_retries:
                wait_s = min(2 ** attempt, 10) + random.random()
                print(f"[Semantic Scholar] {status} server error. sleep {wait_s:.1f}s (attempt {attempt}/{max_retries})")
                await asyncio.sleep(wait_s)
                continue
            print(f"[Semantic Scholar Tool Error] {e}")
            return []
        except Exception as e:
            print(f"[Semantic Scholar Tool Error] {e}")
            return []

    return []


# uv run python -m core.tools.semantic_scholar_paper_search
if __name__ == "__main__":
    import asyncio
    import json

    async def _test():
        q = "transformer survey"
        results = await search_paper_resources(
            q,
            max_results=3,
        )
        print(f"\nQuery: {q}")
        print(f"Returned: {len(results)} items\n")
        print(json.dumps(results, ensure_ascii=False, indent=2))

    asyncio.run(_test())
