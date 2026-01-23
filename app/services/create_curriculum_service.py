from datetime import datetime, timezone
from typing import List
from app.models.curriculum import (
    CurriculumGenerateRequest,
    CurriculumGenerateResponse
)
from app.models.graph import Graph, GraphNode, GraphEdge
import uuid

async def generate_curriculum(request: CurriculumGenerateRequest) -> CurriculumGenerateResponse:
    """
    커리큘럼 생성 서비스 (스텁)
    
    실제 구현은 나중에 services 디렉토리에 추가될 예정입니다.
    현재는 mock 그래프를 반환합니다.
    """
    # TODO: 실제 커리큘럼 생성 로직 구현
    # - analysis_id로 이전 분석 데이터 조회
    # - 사용자 특성과 키워드 기반으로 학습 경로 생성
    # - 그래프 구조 생성 (노드와 엣지)
    # - 최적화된 학습 순서 결정
    
    # Mock 데이터 반환
    
    curriculum_id = f"curr-{datetime.now().strftime('%Y')}-{uuid.uuid4().hex[:4]}"
    
    # Mock 그래프 생성
    nodes = [
        GraphNode(id="n1", label="기초 개념", type="concept"),
        GraphNode(id="n2", label="중급 개념", type="concept"),
        GraphNode(id="n3", label="고급 개념", type="concept"),
        GraphNode(id="n4", label="실습", type="practice"),
    ]
    
    edges = [
        GraphEdge(from_node="n1", to_node="n2", weight=1.0),
        GraphEdge(from_node="n2", to_node="n3", weight=1.0),
        GraphEdge(from_node="n3", to_node="n4", weight=1.0),
    ]
    
    graph = Graph(nodes=nodes, edges=edges)
    
    return CurriculumGenerateResponse(
        curriculum_id=curriculum_id,
        title=f"{request.paper_title} 학습 커리큘럼",
        graph=graph,
        created_at=datetime.now(timezone.utc).isoformat()
    )
