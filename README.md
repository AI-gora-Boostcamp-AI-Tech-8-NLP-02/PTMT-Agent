# PTMT-Agent

Paper-based Teaching Material Agent API

## 개요

논문을 분석하여 키워드를 추출하고, 사용자의 학습 특성에 맞는 커리큘럼을 생성하는 API 서버입니다.

## 설치

```bash
# 의존성 설치
uv install

# 또는 pip 사용
pip install -e .
```

## 실행

### 로컬 개발 서버

```bash
# 방법 1: 스크립트 사용
./scripts/run_server.sh

# 방법 2: 직접 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

서버가 실행되면 다음 URL에서 접근할 수 있습니다:
- API 문서: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Cloudflare Tunnel 설정

프로덕션 환경에서 외부 접근을 위해 Cloudflare Tunnel을 설정할 수 있습니다.

**사전 준비**:
1. `.env` 파일에 `TUNNEL_TOKEN` 설정
   ```bash
   # .env_example을 참고하여 .env 파일 생성
   TUNNEL_TOKEN=<your-tunnel-token>
   ```

**설정 스크립트 실행**:
```bash
# Cloudflare Tunnel 설정 및 실행
source ./scripts/cloudflare_setting.sh
```

이 스크립트는 다음 작업을 수행합니다:
- `.env` 파일에서 `TUNNEL_TOKEN` 로드 및 검증
- 필수 패키지 설치 (`curl`, `sudo`, `tmux`)
- `cloudflared` 설치 (미설치 시)
- `tmux` 세션(`cf-tunnel`)에서 Cloudflare Tunnel 실행

**Tunnel 로그 확인**:
```bash
# tmux 세션에 연결하여 로그 확인
tmux attach -t cf-tunnel

# 세션에서 나오려면: Ctrl+B, D
```

**참고사항**:
- Tunnel은 백그라운드(`tmux`)에서 실행됩니다
- 기존 `cf-tunnel` 세션이 있으면 자동으로 종료 후 재시작합니다
- 클라우드 플레어 서버를 재시작하려면 `./scripts/cloudflare_setting.sh`를 다시 실행하세요

## API 엔드포인트

### 1. 키워드 추출 (API-CURR-KWORD-01)

**POST** `/api/curr/keywords/extract`

논문 파일(PDF를 텍스트로 변환한 값), 웹 링크, 또는 제목을 전송하여 핵심 키워드를 추출합니다.

**요청 형식**: `application/json`

**파라미터**:
- `pdf_text` (Optional): PDF를 텍스트로 변환한 값 (문자열)
- `weblink` (Optional): 논문 웹 링크
- `paper_title` (Optional): 논문 제목
- `paper_db_id` (Optional): 논문 DB ID

**참고**: `pdf_text`, `weblink`, `paper_title` 중 적어도 하나는 필수입니다.

**예시**:
```bash
curl -X POST http://localhost:8000/api/curr/keywords/extract \
  -H "Content-Type: application/json" \
  -d '{
    "paper_title": "Test Paper",
    "paper_db_id": "test_01"
  }'
```

**PDF 텍스트 사용 예시**:
```bash
curl -X POST http://localhost:8000/api/curr/keywords/extract \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_text": "This is the parsed PDF content...",
    "paper_title": "Sample Paper"
  }'
```

### 2. 커리큘럼 생성 (API-CURR-CURR-01)

**POST** `/api/curr/curr/generate`

추출된 키워드와 사용자의 학습 특성을 기반으로 커리큘럼 그래프를 생성합니다.

**요청 형식**: `application/json`

**예시**:
```bash
curl -X POST http://localhost:8000/api/curr/curr/generate \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": "ext-7721-b4c9-4a12",
    "paper_title": "Test Paper",
    "keywords": ["RNN", "Attention", "Encoder"],
    "user_traits": {
      "goal": "개념 파악",
      "level": "비전공자",
      "understood_keywords": ["Encoder", "Attention"],
      "investment_time": [5, 3],
      "preferred_format": ["논문", "동영상"]
    }
  }'
```

## 프로젝트 구조

```
app/
├── main.py                    # FastAPI 앱 인스턴스
├── api/
│   ├── routes/
│   │   ├── keywords.py       # 키워드 추출 엔드포인트
│   │   └── curriculum.py     # 커리큘럼 생성 엔드포인트
├── models/
│   └── schemas.py            # Pydantic 모델
├── services/
│   ├── keyword_service.py    # 키워드 추출 서비스 (스텁)
│   └── curriculum_service.py # 커리큘럼 생성 서비스 (스텁)
└── core/
    └── exceptions.py         # 커스텀 예외
```

## 테스트

### 테스트 의존성 설치

```bash
# 테스트 의존성 포함하여 설치
uv install --extra test

# 또는 pip 사용
pip install -e ".[test]"
```

### 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 테스트 파일 실행
pytest tests/test_keywords.py

# 상세 출력과 함께 실행
pytest -v

# 커버리지 포함 실행
pytest --cov=app
```

### 테스트 구조

- `tests/test_main.py`: 기본 엔드포인트 테스트 (root, health)
- `tests/test_keywords.py`: 키워드 추출 API 테스트
- `tests/test_curriculum.py`: 커리큘럼 생성 API 테스트
- `tests/test_exceptions.py`: 에러 핸들링 테스트

## 개발 참고사항

- 현재 서비스 로직은 스텁으로 구현되어 있습니다. 실제 AI/ML 로직은 `app/services/` 디렉토리에 추가 구현 예정입니다.
- API 명세서에 따라 모든 에러 케이스가 구현되어 있습니다.
- FastAPI 자동 문서화 기능을 통해 `/docs`에서 API를 테스트할 수 있습니다.
