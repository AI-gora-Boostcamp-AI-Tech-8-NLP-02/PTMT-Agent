import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_root(client: TestClient):
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "PTMT-Agent API"
    assert data["version"] == "0.1.0"


def test_health_check(client: TestClient):
    """Health check 엔드포인트 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
