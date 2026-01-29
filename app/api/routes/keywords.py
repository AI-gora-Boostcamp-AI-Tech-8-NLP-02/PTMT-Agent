from fastapi import APIRouter
from app.models.keyword import KeywordExtractRequest, KeywordExtractResponse
from app.services.extract_paper_concept_service import extract_keywords
from app.core.exceptions import (
    MissingSourceDataException,
    InvalidFormatException,
    InternalServerErrorException
)

router = APIRouter(prefix="/api/curr/keywords", tags=["keywords"])


@router.post("/extract", response_model=KeywordExtractResponse)
async def extract_keywords_endpoint(request: KeywordExtractRequest):
    """
    API-CURR-KWORD-01: 키워드 추출 엔드포인트
    
    논문 파일(PDF를 텍스트로 변환한 값), 웹 링크, 또는 제목을 전송하여 핵심 키워드를 추출합니다.
    pdf_text, weblink, paper_title 중 적어도 하나는 필수입니다.
    """
    try:
        if not request.paper_content:
             raise MissingSourceDataException("Paper content is missing")

        
        # 서비스 호출
        result = await extract_keywords(request)
        
        return result
        
    except (MissingSourceDataException, InvalidFormatException):
        raise
    except Exception as e:
        raise InternalServerErrorException(f"서버 오류가 발생했습니다: {str(e)}")
