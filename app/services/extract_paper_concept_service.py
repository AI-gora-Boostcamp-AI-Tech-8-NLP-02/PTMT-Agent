import uuid
from datetime import datetime, timezone
from app.models.keyword import KeywordExtractRequest, KeywordExtractResponse
from core.agents.concept_extraction_agent import ConceptExtractionAgent
from core.llm.solar_pro_2_llm import get_solar_model
from dotenv import load_dotenv
load_dotenv()

async def extract_keywords(request: KeywordExtractRequest) -> KeywordExtractResponse:
    """
    키워드 추출 서비스
    
    ConceptExtractionAgent를 사용하여 논문의 개념(키워드)과 요약을 추출합니다.
    """
    try:
        # 1. LLM 및 Agent 초기화
        llm = get_solar_model()
        agent = ConceptExtractionAgent(llm=llm)
        
        # 2. 입력 데이터 구성
        # request.paper_content를 바로 활용
        
        paper_input = {
            "paper_id": request.paper_id,
            "paper_name": request.paper_content.title,
            "paper_content": request.paper_content.model_dump()
        }
        
        # 3. Agent 실행
        # ConceptExtractionAgent.run 비동기 실행
        result = await agent.run(paper_input)
        
        # analysis_id = f"ext-{uuid.uuid4().hex[:12]}" # Deprecated but might be needed for internal tracking
        analysis_id = f"ext-{uuid.uuid4().hex[:12]}"

        return KeywordExtractResponse(
            paper_id=result["paper_id"],
            keywords=result["paper_concepts"],
            summary=result["paper_summary"],
            extracted_at=datetime.now(timezone.utc).isoformat(),
            extracted_by="Solar_2_pro"
        )
        
    except Exception as e:
        print(f"❌ Keyword Extraction Failed: {e}")
        # 실패 시 에러를 던지거나 Mock/Error Response 반환
        # 여기서는 에러 발생 시 빈 값 반환하도록 처리
        return KeywordExtractResponse(
            paper_id=request.paper_id or "error",
            keywords=[],
            summary=f"Extraction failed: {str(e)}",
            extracted_at=datetime.now(timezone.utc).isoformat(),
            extracted_by="System"
        )
