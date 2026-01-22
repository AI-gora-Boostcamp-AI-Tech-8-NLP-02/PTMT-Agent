import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """테스트용 FastAPI 클라이언트"""
    return TestClient(app)
