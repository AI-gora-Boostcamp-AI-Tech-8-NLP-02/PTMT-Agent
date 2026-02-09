from typing import Annotated
from fastapi import APIRouter, Depends
from app.api.deps import get_token
from app.models.keyword import KeywordExtractRequest, KeywordExtractResponse
from app.services.extract_paper_concept_service import extract_keywords
from app.core.exceptions import (
    MissingSourceDataException,
    InvalidFormatException,
    InternalServerErrorException
)

router = APIRouter(prefix="/api/curr/keywords", tags=["keywords"])


@router.post("/extract", response_model=KeywordExtractResponse)
async def extract_keywords_endpoint(
    request: KeywordExtractRequest,
    _token: Annotated[str, Depends(get_token)]
):
    """
    API-CURR-KWORD-01: 키워드 추출 엔드포인트

    메인 서버에서 전달한 아래 스키마를 기반으로 핵심 키워드를 추출합니다.
    - paper_id: 논문 ID
    - paper_content: title/author/abstract/body 구조화 데이터
    - assigned_key_slot: 사용할 API 키 슬롯(선택)
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
