import pytest
from fastapi.testclient import TestClient


def test_error_response_format(client: TestClient):
    """에러 응답 형식 검증"""
    # MISSING_SOURCE_DATA 에러 테스트
    # 모든 필드가 None인 유효한 JSON 요청
    response = client.post(
        "/api/curr/keywords/extract",
        json={
            "pdf_text": None,
            "weblink": None,
            "paper_title": None,
            "paper_db_id": None
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert "error_code" in data
    assert "message" in data
    assert isinstance(data["error_code"], str)
    assert isinstance(data["message"], str)
    assert data["error_code"] == "MISSING_SOURCE_DATA"


def test_missing_traits_error_format(client: TestClient):
    """MISSING_TRAITS 에러 형식 테스트"""
    request_data = {
        "analysis_id": "ext-123",
        "paper_title": "Test",
        "keywords": ["test"]
        # user_traits 누락
    }
    response = client.post(
        "/api/curr/curr/generate",
        json=request_data
    )
    # Pydantic validation error (422) 또는 custom error (400)
    assert response.status_code in [400, 422]
    if response.status_code == 400:
        data = response.json()
        assert "error_code" in data
        assert "message" in data
