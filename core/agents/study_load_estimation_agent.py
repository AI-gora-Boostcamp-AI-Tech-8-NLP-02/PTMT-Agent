# core/agents/study_load_estimation_agent.py

import json
import re
import asyncio
from typing import List, Dict, Any
from core.contracts.study_load_estimation import StudyLoadEstimationInput, StudyLoadEstimationOutput
from core.contracts.types.curriculum import Resource
from core.prompts.study_load_estimation.v4 import STUDY_LOAD_ESTIMATION_PROMPT_V4
from core.utils.timeout import async_timeout

class StudyLoadEstimationAgent:
    def __init__(self, llm):
        self.llm = llm
        self.chain = STUDY_LOAD_ESTIMATION_PROMPT_V4 | llm
        self.sem = asyncio.Semaphore(5)  # 병렬 실행 제한

    @async_timeout(90)
    async def run(self, input_data: StudyLoadEstimationInput) -> StudyLoadEstimationOutput:
        """에이전트 실행"""
        resources = input_data["resources"]
        user_level = input_data["user_level"]
        purpose = input_data["purpose"]  ## 입력으로만 받고 무시

        if not resources:
            return {"evaluated_resources": []}

        # keyword 기준 그룹핑 (없으면 "unknown"에 모아버림)
        grouped: Dict[str, List[Resource]] = {}
        for r in resources:
            kw = (r.get("keyword") or "unknown").strip()
            grouped.setdefault(kw, []).append(r)

        tasks = [
            self.estimate_batch_for_keyword(keyword=kw, user_level=user_level, resources=res_list)
            for kw, res_list in grouped.items()
        ]

        batch_results = await asyncio.gather(*tasks)

        # flatten
        evaluated_resources: List[Resource] = []
        for chunk in batch_results:
            evaluated_resources.extend(chunk)

        return {"evaluated_resources": evaluated_resources}
    
    async def estimate_batch_for_keyword(self, keyword: str, user_level: str, resources: List[Resource]) -> List[Resource]:
        """
        동일 keyword에 대한 resources를 한 번에 LLM에 넣고,
        url 기준으로 평가 결과를 원본 resources에 merge하여 반환
        """
        async with self.sem:
            try:
                resources_payload = []
                for r in resources:
                    resources_payload.append({
                        "url": r.get("url"),
                        "title": r.get("resource_name") or r.get("title") or "Untitled Resource",
                        "content": (r.get("raw_content") or r.get("content") or "")[:2000],
                        "type_hint": r.get("type") or r.get("type_hint") or None,
                        "duration": r.get("duration"),
                        "citationCount": r.get("citationCount"),
                    })

                response = await self.chain.ainvoke(
                    {
                        "keyword": keyword,
                        "user_level": user_level,
                        "resources_json": json.dumps(resources_payload, ensure_ascii=False)
                    },
                    config={"tags": ["load-estimation-batch"]}
                )

                parsed_list = self.parse_response_list(response.content)

                # url -> 평가 결과 매핑
                eval_map: Dict[str, Dict[str, Any]] = {}
                for item in parsed_list:
                    url = (item or {}).get("url")
                    if url:
                        eval_map[url] = item

                # 원본 업데이트
                for r in resources:
                    url = r.get("url")
                    ev = eval_map.get(url, {})

                    # 기본값 (파싱 실패/누락 대비)
                    difficulty = self._safe_int(ev.get("difficulty"), default=3, lo=1, hi=10)
                    importance = self._safe_int(ev.get("importance"), default=3, lo=0, hi=10)
                    quality = self._safe_int(ev.get("quality"), default=3, lo=1, hi=5)
                    study_load = self._safe_float(ev.get("study_load"), default=0.5, lo=0.0, hi=100.0)

                    r.update({
                        "difficulty": str(difficulty),
                        "importance": str(importance),
                        "quality": str(quality),
                        "study_load": str(study_load),
                        "type": (ev.get("type") or r.get("type") or "web_doc"),
                        "resource_description": (ev.get("resource_description") or "자료에 대한 설명이 없습니다.")
                    })

                return resources

            except Exception as e:
                print(f"[Batch Estimation Error] keyword={keyword}: {e}")
                # 에러 발생 시 기본값 채워서 그대로 반환
                for r in resources:
                    r.update({
                        "difficulty": "3",
                        "importance": "3",
                        "quality": "3",
                        "study_load": "0.5",
                        "type": r.get("type") or "web_doc",
                        "resource_description": r.get("resource_description") or "자료에 대한 설명이 없습니다."
                    })
                return resources

        
    def parse_response_list(self, text: str) -> List[Dict[str, Any]]:
        """
        JSON 배열 추출 및 파싱
        - 모델이 앞뒤 텍스트를 섞어도 최대한 JSON array만 뽑아냄
        """
        try:
            # 가장 바깥 array만 추출 시도
            match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
            clean_json = match.group() if match else text
            data = json.loads(clean_json)

            if isinstance(data, list):
                # list 내부가 dict가 아닐 수 있으니 정리
                return [x for x in data if isinstance(x, dict)]
            return []
        except Exception:
            return []
        
    def _safe_int(self, val: Any, default: int, lo: int, hi: int) -> int:
        try:
            n = int(float(val))
            if n < lo:
                return lo
            if n > hi:
                return hi
            return n
        except Exception:
            return default

    def _safe_float(self, val: Any, default: float, lo: float, hi: float) -> float:
        try:
            n = float(val)
            if n < lo:
                return lo
            if n > hi:
                return hi
            return n
        except Exception:
            return default