# core/tools/serper_video_search.py

import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv
from langsmith import traceable

load_dotenv()

SERPER_API_KEY = os.environ.get("SERPER_API_KEY")
SERPER_ENDPOINT = "https://google.serper.dev/videos"


def _normalize_serper_video_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    url = item.get("link")
    if not url:
        return None

    return {
        "title": item.get("title") or "Untitled Video",
        "url": url,
        "content": item.get("snippet") or "",
        "duration": item.get("duration"),  # tavily엔 없지만 영상 길이는 있으면 좋을 것 같음
        "raw": item,
    }


@traceable(run_type="tool", name="Serper Video Search")
async def search_video_resources(
    query: str,
    max_results: int = 2,
    gl: str = "kr",
    hl: str = "ko",
    timeout_sec: float = 15.0,
) -> List[Dict[str, Any]]:
    """
    Serper Video API를 이용해 영상 검색
    Tavily와 유사한 List[{"title","url","content",...}] 형태로 반환
    """
    if not SERPER_API_KEY:
        print("[Serper Tool Error] SERPER_API_KEY is missing")
        return []

    payload = {"q": query, "gl": gl, "hl": hl}
    headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            resp = await client.post(SERPER_ENDPOINT, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        videos = data.get("videos", [])
        if not isinstance(videos, list):
            return []

        normalized: List[Dict[str, Any]] = []
        for item in videos:
            if not isinstance(item, dict):
                continue
            n = _normalize_serper_video_item(item)
            if n:
                normalized.append(n)
            if len(normalized) >= max_results:
                break

        return normalized

    except Exception as e:
        print(f"[Serper Tool Error] {e}")
        return []



# uv run python -m core.tools.serper_video_search
if __name__ == "__main__":
    import asyncio
    import json

    async def _test():
        query = "Self-Attention 개념"
        results = await search_video_resources(query, max_results=3, gl="kr", hl="ko")

        print(f"\nQuery: {query}")
        print(f"Returned: {len(results)} items\n")
        print(json.dumps(results, ensure_ascii=False, indent=2))

    asyncio.run(_test())
