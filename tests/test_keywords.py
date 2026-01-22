import pytest
from fastapi.testclient import TestClient


def test_extract_keywords_with_title(client: TestClient):
    """제목으로 키워드 추출 테스트"""
    response = client.post(
        "/api/curr/keywords/extract",
        json={
            "paper_title": "Test Paper Title",
            "paper_db_id": "test_01"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data
    assert data["title"] == "Test Paper Title"
    assert data["paper_db_id"] == "test_01"
    assert "keywords" in data
    assert isinstance(data["keywords"], list)
    assert len(data["keywords"]) > 0
    assert "summary" in data
    assert "extracted_at" in data
    assert "extracted_by" in data
    assert data["extracted_by"] == "Solar_2_pro"


def test_extract_keywords_with_weblink(client: TestClient):
    """웹 링크로 키워드 추출 테스트"""
    response = client.post(
        "/api/curr/keywords/extract",
        json={
            "weblink": "https://example.com/paper.pdf",
            "paper_title": "Web Paper"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data
    assert "keywords" in data
    assert "summary" in data


def test_extract_keywords_with_pdf_text(client: TestClient):
    """PDF 텍스트로 키워드 추출 테스트"""
    # PDF를 텍스트로 변환한 값 (파싱된 텍스트)
    pdf_text = "This is a sample paper about machine learning and artificial intelligence..."
    response = client.post(
        "/api/curr/keywords/extract",
        json={
            "pdf_text": pdf_text,
            "paper_db_id": "test_02"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data
    assert "keywords" in data
    assert "summary" in data


def test_extract_keywords_missing_source_data(client: TestClient):
    """소스 데이터 누락 에러 테스트"""
    response = client.post(
        "/api/curr/keywords/extract",
        json={}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "MISSING_SOURCE_DATA"
    assert "필수" in data["message"]


def test_extract_keywords_all_fields_empty(client: TestClient):
    """모든 필드가 None인 경우 에러 테스트"""
    response = client.post(
        "/api/curr/keywords/extract",
        json={
            "pdf_text": None,
            "weblink": None,
            "paper_title": None,
            "paper_db_id": "test_03"
        }
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "MISSING_SOURCE_DATA"


def test_extract_keywords_with_all_fields(client: TestClient):
    """모든 필드가 제공된 경우 테스트"""
    pdf_text = "Sample paper content about deep learning..."
    response = client.post(
        "/api/curr/keywords/extract",
        json={
            "pdf_text": pdf_text,
            "weblink": "https://example.com/paper",
            "paper_title": "Complete Test Paper",
            "paper_db_id": "test_04"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Complete Test Paper"
    assert data["paper_db_id"] == "test_04"
    assert "keywords" in data
    assert "summary" in data
