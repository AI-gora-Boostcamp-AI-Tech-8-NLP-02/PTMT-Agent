from datetime import datetime, timezone
from app.models.keyword import KeywordExtractRequest, KeywordExtractResponse
import uuid

async def extract_keywords(request: KeywordExtractRequest) -> KeywordExtractResponse:
    """
    키워드 추출 서비스 (스텁)
    
    실제 구현은 나중에 services 디렉토리에 추가될 예정입니다.
    현재는 mock 데이터를 반환합니다.
    """
    # TODO: 실제 키워드 추출 로직 구현
    # - PDF 텍스트 처리 (request.pdf_text)
    # - 웹 링크에서 논문 정보 추출 (request.weblink)
    # - 제목으로 웹 검색 (request.paper_title)
    # - AI 모델을 통한 키워드 추출 및 요약 생성
    
    # Mock 데이터 반환
    analysis_id = f"ext-{uuid.uuid4().hex[:12]}"
    
    # 제목 결정 (우선순위: paper_title > 기본값)
    title = request.paper_title or "Unknown Paper"
    
    # Mock 키워드
    mock_keywords = [
        "인공지능",
        "데이터 분석",
        "머신러닝",
        "알고리즘",
        "효율성"
    ]
    
    # Mock 요약
    mock_summary = "이 논문은 인공지능과 머신러닝을 활용한 데이터 분석 방법론을 제시합니다."
    
    return KeywordExtractResponse(
        analysis_id=analysis_id,
        title=title,
        paper_db_id=request.paper_db_id,
        keywords=mock_keywords,
        summary=mock_summary,
        extracted_at=datetime.now(timezone.utc).isoformat(),
        extracted_by="Solar_2_pro"
    )
