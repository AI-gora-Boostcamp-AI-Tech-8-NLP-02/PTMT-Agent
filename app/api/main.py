from fastapi import APIRouter

from app.api.routes import keywords, curriculum

# API 라우터 통합 관리
# 각 라우터에 이미 prefix가 포함되어 있으므로 여기서는 prefix를 추가하지 않음
api_router = APIRouter()

# 라우터 등록
api_router.include_router(keywords.router)
api_router.include_router(curriculum.router)
