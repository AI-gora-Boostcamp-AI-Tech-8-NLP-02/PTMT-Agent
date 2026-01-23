from fastapi import APIRouter
from app.models.curriculum import (
    CurriculumGenerateRequest,
    CurriculumGenerateResponse
)
from app.services.curriculum_service import generate_curriculum
from app.core.exceptions import (
    MissingTraitsException,
    AnalysisNotFoundException,
    GenerationFailedException,
    InternalServerErrorException
)

router = APIRouter(prefix="/api/curr/curr", tags=["curriculum"])


@router.post("/generate", response_model=CurriculumGenerateResponse)
async def generate_curriculum_endpoint(request: CurriculumGenerateRequest):
    """
    API-CURR-CURR-01: 커리큘럼 생성 엔드포인트
    
    추출된 키워드와 사용자의 학습 수준, 목표 등 추가 정보를 결합하여
    최적화된 학습 커리큘럼 그래프를 생성합니다.
    """
    try:
        # 필수 필드 검증
        if not request.user_traits:
            raise MissingTraitsException()
        
        # analysis_id 검증 (실제로는 DB에서 확인해야 함)
        # TODO: 실제 구현 시 analysis_id로 이전 분석 데이터 조회
        if not request.analysis_id:
            raise AnalysisNotFoundException()
        
        # 서비스 호출
        result = await generate_curriculum(request)
        
        return result
        
    except (MissingTraitsException, AnalysisNotFoundException):
        raise
    except Exception as e:
        # 예상치 못한 오류는 GENERATION_FAILED로 처리
        raise GenerationFailedException(f"커리큘럼을 생성하는 도중 오류가 발생했습니다: {str(e)}")
