# core/utils/resource_planner.py

from __future__ import annotations
from typing import Dict, List, Any

def plan_tools(pref_types: List[str] | None) -> List[Dict[str, Any]]:
    """
    - Tavily는 항상 포함
    - 최대 5개
    - pref_types: ["paper","web_doc","video"]

    출력 예시:
    [
      {"tool": "tavily", "max_results": 2},
      {"tool": "serper_web", "max_results": 1},
      {"tool": "serper_video", "max_results": 1},
      {"tool": "semantic_scholar", "max_results": 1},
    ]
    """
    P = set((pref_types or []))

    # 3종류 모두
    if "paper" in P and "web_doc" in P and "video" in P:
        return [
            {"tool": "tavily", "max_results": 2},
            {"tool": "serper_web", "max_results": 1},
            {"tool": "serper_video", "max_results": 1},
            {"tool": "semantic_scholar", "max_results": 1},
        ]

    # paper + web_doc
    if "paper" in P and "web_doc" in P:
        return [
            {"tool": "tavily", "max_results": 1},
            {"tool": "semantic_scholar", "max_results": 2},
            {"tool": "serper_web", "max_results": 2},
        ]

    # paper + video
    if "paper" in P and "video" in P:
        return [
            {"tool": "tavily", "max_results": 1},
            {"tool": "semantic_scholar", "max_results": 2},
            {"tool": "serper_video", "max_results": 2},
        ]

    # web_doc + video
    if "web_doc" in P and "video" in P:
        return [
            {"tool": "tavily", "max_results": 1},
            {"tool": "serper_web", "max_results": 2},
            {"tool": "serper_video", "max_results": 2},
        ]

    # paper only
    if "paper" in P:
        return [
            {"tool": "tavily", "max_results": 1},
            {"tool": "semantic_scholar", "max_results": 4},
        ]

    # web_doc only
    if "web_doc" in P:
        return [
            {"tool": "tavily", "max_results": 1},
            {"tool": "serper_web", "max_results": 4},
        ]

    # video only
    if "video" in P:
        return [
            {"tool": "tavily", "max_results": 1},
            {"tool": "serper_video", "max_results": 4},
        ]

    # 아무 선호도 없으면 tavily 5개
    return [{"tool": "tavily", "max_results": 5}]