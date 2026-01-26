import json
from dotenv import load_dotenv

from core.contracts.concept_extraction import ConceptExtractionInput, ConceptExtractionOutput
from core.prompts.concept_extraction.v1 import CONCEPT_EXTRACTION_PROMPT_V1

load_dotenv()

class ConceptExtractionAgent:
    def __init__(self, llm):
        self.llm = llm
        self.chain = CONCEPT_EXTRACTION_PROMPT_V1 | llm
    
    def run(self, paper: ConceptExtractionInput) -> ConceptExtractionOutput:
        response = self.chain.invoke(
            {
                "paper_name": paper["paper_name"],
                "paper_content": paper["paper_content"],
            },
            config={
                "max_tokens": 512,
                "tags": ["concept-extraction"]
            }
        )

        return self._parse_response(
            paper_id=paper["paper_id"],
            paper_name=paper["paper_name"],
            text=response.content
        )
    
    def _parse_response(
        self,
        paper_id: str,
        paper_name: str,
        text: str
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
            "paper_summary": parsed["paper_summary"],
            "paper_concepts": parsed["paper_concepts"],
        }