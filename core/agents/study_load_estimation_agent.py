import json
import re
import asyncio
from typing import List, Dict, Any
from core.contracts.study_load_estimation import StudyLoadEstimationInput, StudyLoadEstimationOutput, ResourceData
from core.prompts.study_load_estimation.v1 import STUDY_LOAD_ESTIMATION_PROMPT_V1

class StudyLoadEstimationAgent:
    def __init__(self, llm):
        self.llm = llm
        self.chain = STUDY_LOAD_ESTIMATION_PROMPT_V1 | llm
        self.sem = asyncio.Semaphore(5)  # 병렬 실행 제한

    async def run(self, input_data: StudyLoadEstimationInput) -> StudyLoadEstimationOutput:
        """에이전트 실행"""
        resources = input_data["resources"]
        user_level = input_data["user_level"]
        purpose = input_data["purpose"]

        if not resources:
            return {"evaluated_resources": []}

        tasks = [
            self._estimate_single(res, user_level, purpose)
            for res in resources
        ]
        
        evaluated_resources = await asyncio.gather(*tasks)
        return {"evaluated_resources": evaluated_resources}

    async def _estimate_single(self, resource: ResourceData, user_level: str, purpose: str) -> ResourceData:
        async with self.sem:
            try:
                response = await self.chain.ainvoke({
                    "keyword": resource.get("keyword"),
                    "title": resource.get("resource_name"),
                    "content": resource.get("raw_content", "")[:800],
                    "user_level": user_level,
                    "purpose": purpose
                }, config={"tags": ["load-estmination"]})
                
                parsed_data = self._parse_response(response.content)
                
                # 결과 업데이트
                resource.update({
                    "difficulty": str(parsed_data.get("difficulty", "3")),
                    "importance": str(parsed_data.get("importance", "3")),
                    "study_load": str(parsed_data.get("study_load", "0.5")),
                    "type": parsed_data.get("type", "web_doc"),
                    "resource_description": parsed_data.get("resource_description", "자료에 대한 설명이 없습니다.")
                })
                # 디버깅용 프린트
                print(f"✅ [Estimated] {resource.get('resource_name')}")
                print(response.content)

            except Exception as e:
                print(f"⚠️ [Estimation Error] {resource.get('resource_name')}: {e}")
                # 에러 발생 시 기본값
                resource.update({"difficulty": "3", "importance": "3", "study_load": "0.5", "type": "web_doc"})

            return resource

    def _parse_response(self, text: str) -> Dict[str, Any]:
        """JSON 추출 및 파싱"""
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            clean_json = match.group() if match else text
            return json.loads(clean_json)
        except Exception:
            return {}