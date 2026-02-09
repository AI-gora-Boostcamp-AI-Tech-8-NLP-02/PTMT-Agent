# PTMT-Agent

페튜와 매튜(Paper Tutor & Map Tutor) 커리큘럼 생성 FastAPI 서버입니다.

논문 본문에서 핵심 개념(키워드)을 추출하고, 사용자 학습 정보와 결합해 커리큘럼 생성 워크플로우를 비동기로 실행합니다.

## 주요 기능

- `POST /api/curr/keywords/extract`
    - 논문 구조화 본문(`paper_content`)을 입력받아 키워드/요약 추출
- `POST /api/curr/curr/generate`
    - 키워드 + 사용자 정보를 입력받아 커리큘럼 생성 작업 시작
    - 응답은 즉시 반환되고, 실제 결과는 메인 백엔드로 전송됨

## Agent 구조

### Concept Extraction Agent 흐름

<img width="500" height="1633" alt="image" src="https://github.com/user-attachments/assets/a6eabdf9-6a1d-40ac-8ff9-c8f42fcb1989" />

<br></br>
### Curriculum 생성 Multi-Agent 흐름

<img width="3103" height="1389" alt="image" src="https://github.com/user-attachments/assets/9878e7ec-202e-40a1-9c17-5bb2af6e0bb0" />


## 기술 스택

- Python 3.12+
- FastAPI
- LangChain / Upstage LLM
- Neo4j

## 실행 방법

### 의존성 설치

`uv` 기준: 

```bash
uv sync
```

`pip` 기준:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 환경 변수 설정

`.env_example`을 복사해 `.env`를 만듭니다.

API 키 값을 설정합니다.

### 서버 실행

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

또는

```bash
./scripts/run_server.sh
```

## 프로젝트 구조

```bash
├── README.md
├── app                      # FastAPI 서버 관련 디렉토리
│   ├── __init__.py
│   ├── api
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   ├── main.py
│   │   └── routes
│   │       ├── __init__.py
│   │       ├── curriculum.py
│   │       └── keywords.py
│   ├── core
│   │   ├── __init__.py
│   │   └── exceptions.py
│   ├── main.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── curriculum.py
│   │   ├── graph.py
│   │   └── keyword.py
│   └── services
│       ├── __init__.py
│       ├── create_curriculum_service.py
│       └── extract_paper_concept_service.py
├── assets
│   └── sample_asset
├── core                    # Agent 코드 디렉토리
│   ├── __init__.py
│   ├── agents
│   │   ├── __init__.py
│   │   ├── concept_expansion_agent.py
│   │   ├── concept_extraction_agent.py
│   │   ├── curriculum_compose_agent.py
│   │   ├── curriculum_orchestrator.py
│   │   ├── first_node_order_agent.py
│   │   ├── keyword_graph_agent.py
│   │   ├── paper_concept_alignment_agent.py
│   │   ├── resource_discovery_agent.py
│   │   └── study_load_estimation_agent.py
│   ├── contracts                       # Input/Output 타입 정의
│   │   ├── __init__.py
│   │   ├── concept_expansion.py
│   │   ├── concept_extraction.py
│   │   ├── curriculum_compose.py
│   │   ├── curriculum_orchestrator.py
│   │   ├── first_node_order_agent.py
│   │   ├── keywordgraph.py
│   │   ├── paper_concept_alignment.py
│   │   ├── resource_discovery.py
│   │   ├── study_load_estimation.py
│   │   └── types
│   │       ├── curriculum.py
│   │       ├── paper_info.py
│   │       ├── subgraph.py
│   │       └── user_info.py
│   ├── graphs                       # LangGraph 그래프 정의
│   │   ├── parallel
│   │   │   ├── graph_parallel.py
│   │   │   ├── nodes_parallel.py
│   │   │   └── state_parallel.py
│   │   ├── series
│   │   │   ├── create_curriculum_graph.py
│   │   │   ├── nodes.py
│   │   │   └── state_definition.py
│   │   └── subgraph_to_curriculum.py
│   ├── llm
│   │   ├── __init__.py
│   │   └── solar_pro_2_llm.py
│   ├── prompts                # Agent 별 프롬프트 버전 관리
│   │   ├── concept_expansion
│   │   ├── concept_extraction
│   │   ├── curriculum_compose
│   │   ├── curriculum_orchestrator
│   │   ├── first_node_order
│   │   ├── keyword_graph
│   │   ├── paper_concept_alignment
│   │   ├── resource_discovery
│   │   └── study_load_estimation
│   ├── tests                 # Agent 개별 테스트 코드
│   ├── tools
│   │   ├── __init__.py
│   │   ├── gdb_search.py
│   │   ├── semantic_scholar_paper_search.py
│   │   ├── semantic_scholar_paper_search_bulk.py
│   │   ├── serper_video_search.py
│   │   ├── serper_web_search.py
│   │   └── tavily_search.py
│   └── utils
│       ├── __init__.py
│       ├── get_message.py
│       ├── kg_agent_postprocessing.py
│       ├── kg_agent_preprocessing.py
│       ├── resource_planner.py
│       ├── resource_ranker.py
│       └── timeout.py
├── docs
│   └── document.md
├── main.py
├── pyproject.toml
├── pytest.ini
├── scripts
│   ├── cloudflare_setting.sh
│   └── run_server.sh
├── tests
└── uv.lock

```
