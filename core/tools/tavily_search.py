import os
import asyncio
from typing import List, Dict, Any
from tavily import TavilyClient
from dotenv import load_dotenv


load_dotenv()

TAVILY_KEY = os.environ.get("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=TAVILY_KEY)

async def search_web_resources(query: str, max_results: int = 2) -> List[Dict[str, Any]]:
    """Tavily를 이용해 웹 서치"""
    try:
        # 동기 함수를 비동기 스레드에서 실행
        result = await asyncio.to_thread(
            tavily_client.search, 
            query=query, 
            max_results=max_results, 
            search_depth="advanced"
        )
        return result.get('results', [])
    except Exception as e:
        print(f"❌ [Tavily Tool Error] {e}")
        return []