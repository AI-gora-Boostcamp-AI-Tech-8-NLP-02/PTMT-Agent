# PTMT-Agent

Paper-based Teaching Material Agent API

## 개요

논문을 분석하여 핵심 개념(키워드)을 추출하고, 사용자 학습 특성에 맞는 커리큘럼 그래프를 생성하는 API 서버입니다.

- **키워드 추출**: `ConceptExtractionAgent`(LLM)로 논문에서 개념·요약 추출
- **커리큘럼 생성**: `KeywordGraphAgent`로 서브그래프 생성 후 LangGraph 워크플로우로 커리큘럼 완성, 메인 백엔드로 비동기 전송

## 요구사항

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) 또는 pip

## 설치

```bash
# 의존성 설치 (uv 권장)
uv sync

```

## 환경 변수

`.env_example`을 복사해 `.env`를 만들고 값을 채웁니다.

```bash
cp .env_example .env
```

## 실행

### 로컬 개발 서버

```bash
# 방법 1: 스크립트 사용
./scripts/run_server.sh

# 방법 2: 직접 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API 문서: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

### Cloudflare Tunnel (프로덕션)

```bash
# .env에 TUNNEL_TOKEN 설정 후
source ./scripts/cloudflare_setting.sh
```

- 터널 로그: `tmux attach -t cf-tunnel` (종료: Ctrl+B, D)
- 기존 `cf-tunnel` 세션 있으면 재시작됨

## API 엔드포인트

모든 `/api/*` 요청에는 **Authorization: Bearer &lt;AUTHORIZATION_TOKEN&gt;** 헤더가 필요합니다.

### 1. 키워드 추출 (API-CURR-KWORD-01)

**POST** `/api/curr/keywords/extract`

논문 구조화 데이터(`paper_content`)를 받아 핵심 개념(키워드)과 요약을 추출합니다.


### 2. 커리큘럼 생성 (API-CURR-CURR-01)


추출된 키워드·논문 정보·사용자 특성을 바탕으로 커리큘럼 그래프를 생성합니다.  
생성은 **백그라운드**에서 이루어지며, 완료 시 메인 백엔드 `MAIN_BACKEND_SERVER_PATH`의 `/api/curriculums/import`로 전송됩니다.




## 프로젝트 구조

```
PTMT-Agent/
├── app/
│   ├── main.py                 # FastAPI 앱, 예외 핸들러
│   ├── api/
│   │   ├── main.py             # 라우터 통합
│   │   ├── deps.py             # 인증 (Bearer 토큰)
│   │   └── routes/
│   │       ├── keywords.py     # 키워드 추출 엔드포인트
│   │       └── curriculum.py  # 커리큘럼 생성 엔드포인트
│   ├── models/
│   │   ├── base.py
│   │   ├── keyword.py          # KeywordExtract 요청/응답
│   │   ├── curriculum.py       # Curriculum 요청/응답, PaperContent, UserTraits
│   │   └── graph.py            # Graph, GraphNode, GraphEdge
│   ├── services/
│   │   ├── extract_paper_concept_service.py  # ConceptExtractionAgent 연동
│   │   └── create_curriculum_service.py    # KeywordGraphAgent + LangGraph, 백엔드 전송
│   └── core/
│       └── exceptions.py       # API 예외 정의
├── core/                       # 에이전트·그래프·LLM 코어
│   ├── agents/                 # ConceptExtraction, KeywordGraph 등
│   ├── contracts/              # 입력/출력 스키마
│   ├── graphs/                 # LangGraph (series, parallel, subgraph→curriculum)
│   ├── llm/                    # Solar Pro 2 LLM 래퍼
│   ├── prompts/                # 에이전트별 프롬프트 버전
│   ├── tools/                  # 검색 (Tavily, Serper, Semantic Scholar 등)
│   └── utils/
├── tests/                      
├── scripts/
├── pyproject.toml
└── .env_example
```

## 개발 참고

- 키워드 추출: `ConceptExtractionAgent` + Upstage Solar (프롬프트: `core/prompts/concept_extraction/`).
- 커리큘럼: `KeywordGraphAgent` → LangGraph (`core/graphs/`) → 결과를 `MAIN_BACKEND_SERVER_PATH/api/curriculums/import`로 POST. 실패 시 `/api/curriculums/import_failed`로 알림.
- `/docs`에서 스키마와 예시로 API 호출 가능.
