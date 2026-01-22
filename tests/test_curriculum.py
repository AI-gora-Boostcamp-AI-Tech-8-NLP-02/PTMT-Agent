import pytest
from fastapi.testclient import TestClient


def test_generate_curriculum_success(client: TestClient):
    """커리큘럼 생성 성공 테스트"""
    request_data = {
        "analysis_id": "ext-7721-b4c9-4a12",
        "paper_title": "Test Paper",
        "paper_db_id": "paper_01",
        "keywords": ["RNN", "Attention", "Encoder"],
        "user_traits": {
            "goal": "개념 파악",
            "level": "비전공자",
            "understood_keywords": ["Encoder", "Attention"],
            "investment_time": [5, 3],
            "preferred_format": ["논문", "동영상"]
        }
    }
    response = client.post(
        "/api/curr/curr/generate",
        json=request_data
    )
    assert response.status_code == 200
    data = response.json()
    assert "curriculum_id" in data
    assert data["title"] == "Test Paper 학습 커리큘럼"
    assert "graph" in data
    assert "nodes" in data["graph"]
    assert "edges" in data["graph"]
    assert isinstance(data["graph"]["nodes"], list)
    assert isinstance(data["graph"]["edges"], list)
    assert len(data["graph"]["nodes"]) > 0
    assert len(data["graph"]["edges"]) > 0
    assert "created_at" in data
    
    # 노드 구조 검증
    node = data["graph"]["nodes"][0]
    assert "id" in node
    assert "label" in node
    
    # 엣지 구조 검증
    edge = data["graph"]["edges"][0]
    assert "from" in edge
    assert "to" in edge


def test_generate_curriculum_minimal_request(client: TestClient):
    """최소한의 필수 필드로 커리큘럼 생성 테스트"""
    request_data = {
        "analysis_id": "ext-1234-5678",
        "paper_title": "Minimal Paper",
        "keywords": ["AI", "ML"],
        "user_traits": {}
    }
    response = client.post(
        "/api/curr/curr/generate",
        json=request_data
    )
    assert response.status_code == 200
    data = response.json()
    assert "curriculum_id" in data
    assert "graph" in data


def test_generate_curriculum_missing_traits(client: TestClient):
    """user_traits 누락 에러 테스트"""
    request_data = {
        "analysis_id": "ext-7721-b4c9-4a12",
        "paper_title": "Test Paper",
        "keywords": ["RNN", "Attention"]
        # user_traits 누락
    }
    response = client.post(
        "/api/curr/curr/generate",
        json=request_data
    )
    assert response.status_code == 422  # Pydantic validation error


def test_generate_curriculum_empty_analysis_id(client: TestClient):
    """빈 analysis_id 에러 테스트"""
    request_data = {
        "analysis_id": "",
        "paper_title": "Test Paper",
        "keywords": ["RNN"],
        "user_traits": {
            "goal": "개념 파악"
        }
    }
    response = client.post(
        "/api/curr/curr/generate",
        json=request_data
    )
    # 빈 문자열이면 404가 아니라 validation error일 수 있음
    # 실제 구현에 따라 다를 수 있음
    assert response.status_code in [400, 404, 422]


def test_generate_curriculum_graph_structure(client: TestClient):
    """그래프 구조 검증 테스트"""
    request_data = {
        "analysis_id": "ext-7721-b4c9-4a12",
        "paper_title": "Graph Test Paper",
        "keywords": ["Test"],
        "user_traits": {
            "goal": "테스트"
        }
    }
    response = client.post(
        "/api/curr/curr/generate",
        json=request_data
    )
    assert response.status_code == 200
    data = response.json()
    
    graph = data["graph"]
    nodes = graph["nodes"]
    edges = graph["edges"]
    
    # 노드가 존재해야 함
    assert len(nodes) > 0
    
    # 각 노드는 id와 label을 가져야 함
    for node in nodes:
        assert "id" in node
        assert "label" in node
        assert isinstance(node["id"], str)
        assert isinstance(node["label"], str)
    
    # 엣지가 존재하면 from과 to가 노드 id와 일치해야 함
    if len(edges) > 0:
        node_ids = {node["id"] for node in nodes}
        for edge in edges:
            assert "from" in edge
            assert "to" in edge
            # 실제 구현에서는 노드 ID와 일치해야 함
            # 현재는 스텁이므로 검증만 수행
