import pytest

# FastAPI app import를 조건부로 처리 (일부 모듈이 없을 수 있음)
try:
    from fastapi.testclient import TestClient
    from app.main import app
    
    @pytest.fixture
    def client():
        """테스트용 FastAPI 클라이언트"""
        return TestClient(app)
except ImportError:
    # app 모듈 관련 의존성이 없는 경우 무시
    pass
