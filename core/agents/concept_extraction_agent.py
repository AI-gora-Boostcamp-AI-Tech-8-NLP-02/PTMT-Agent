from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import re
from typing import Optional
from dotenv import load_dotenv
import requests

from core.contracts.concept_extraction import ConceptExtractionInput, ConceptExtractionOutput
from core.prompts.concept_extraction.v1 import FINAL_CONCEPT_EXTRACTION_PROMPT, FIRST_CONCEPT_EXTRACTION_PROMPT
from core.utils.timeout import async_timeout

load_dotenv()

class ConceptExtractionAgent:
    def __init__(self, llm):
        self.llm = llm
        self.first_concept_chain = FIRST_CONCEPT_EXTRACTION_PROMPT | llm
        self.final_concept_chain = FINAL_CONCEPT_EXTRACTION_PROMPT | llm
    
    @async_timeout(30)
    async def run(self, paper: ConceptExtractionInput) -> ConceptExtractionOutput:
        response = await self.first_concept_chain.ainvoke(
            {
                "paper_name": paper["paper_name"],
                "paper_abstract": paper["paper_content"]["abstract"],
                "paper_body": paper["paper_content"]["body"],
            },
            config={
                "max_tokens": 512,
                "tags": ["concept-extraction"]
            }
        )
        
        first_concept_result = self._parse_response(
            paper_id=paper["paper_id"],
            paper_name=paper["paper_name"],
            text=response.content
        )
        
        first_concepts = first_concept_result["paper_concepts"]
        
        print(f"Initial Concepts: {first_concepts}")
        
        wiki_concepts = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._search_wikipedia, concept): concept
                for concept in first_concepts
            }

            for future in as_completed(futures):
                concept = futures[future]
                try:
                    search_results = future.result()

                    print(f"Search Word: {concept}")
                    for result in search_results:
                        print(f"Title: {result['title']}")
                        title = re.sub(r"\s*\(.*?\)$", "", result['title'])
                        wiki_concepts.append(title)
                    print("------------------------------")

                except Exception as e:
                    print(f"[ERROR] {concept}: {e}")
        
        response = await self.final_concept_chain.ainvoke(
            {
                "paper_name": paper["paper_name"],
                "paper_abstract": paper["paper_content"]["abstract"],
                "paper_body": paper["paper_content"]["body"],
                "paper_summary": first_concept_result["paper_summary"],
                "initial_concepts": first_concept_result["paper_concepts"],
                "wiki_words": wiki_concepts
            },
            config={
                "max_tokens": 512,
                "tags": ["concept-extraction"]
            }
        )
        
        result = self._parse_response(
            paper_id=paper["paper_id"],
            paper_name=paper["paper_name"],
            text=response.content,
            paper_summary=first_concept_result["paper_summary"],
        )
        
        return result
    
    def _parse_response(
        self,
        paper_id: str,
        paper_name: str,
        text: str,
        paper_summary: str | None = None,
    ) -> ConceptExtractionOutput:
        """
        LLM이 반환한 JSON 문자열을 파싱하여
        최종 ConceptExtractionOutput을 생성한다.
        """

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM output is not valid JSON: {text}") from e

        return {
            "paper_id": paper_id,
            "paper_name": paper_name,
            "paper_summary": paper_summary if paper_summary is not None else parsed["paper_summary"],
            "paper_concepts": parsed["paper_concepts"],
        }
    
    def _search_wikipedia(self, keyword):
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Papers Category Extractor/1.0 (Educational Purpose)',
            'Accept-Encoding': 'gzip'
        })

        url = os.environ.get("WIKI_API_URL")
        params = {
            "action": "query",
            "list": "search",
            "srsearch": keyword,
            "format": "json",
            "srlimit": 3  # 상위 3개 결과
        }
        response = session.get(url, params=params)
        data = response.json()
        return data['query']['search']

    