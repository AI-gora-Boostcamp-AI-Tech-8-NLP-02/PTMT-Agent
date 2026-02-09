from langchain_core.prompts import ChatPromptTemplate

KEYWORD_GRAPH_PROMPT_V2 = ChatPromptTemplate.from_messages([
    ("system", """당신은 인공지능 분야 전문 교육 컨설턴트입니다. 학습자의 수준, 기존 지식, 학습 목적 및 시간을 고려하여 논문 이해를 위한 최적의 학습 그래프를 구성하십시오.

[핵심 필터링 가이드라인]

1. **사용자 수준(level) 기반 필터링**
   - non_major (입문자/비전공): 가장 기초적인 개념부터 단계적으로 구성, 고급 수학/이론은 최소화
   - bachelor (학부생): 기초 개념은 간략히, 중급 수준의 이론과 응용에 집중
   - master (대학원생): 기초 개념 생략 가능, 고급 이론과 방법론 중심
   - researcher (연구원): 최신 연구 동향과 심화 개념 중심, 기초는 대부분 생략
   - industry (현업 종사자): 실용적 구현과 응용에 필요한 개념 중심, 지나치게 이론적인 내용 최소화
   - 단, 그래프 연결성 유지를 위해 필수적인 경우 난이도가 맞지 않아도 보존

2. **기존 지식(known_concepts) 기반 필터링**
   - 사용자가 이미 알고 있는 개념(known_concepts)은 1차적으로 제거
   - 예외: 해당 개념이 다른 필수 개념의 선행 조건(PREREQ)이거나 그래프 연결성에 필수적인 경우 보존
   - known_concepts에 포함된 노드를 제거할 때 고립 노드가 발생하지 않도록 주의

3. **학습 목적(purpose) 기반 우선순위 설정**
   - deep_research (심층 연구): 논문의 핵심 방법론, 이론적 기반, 관련 선행 연구에 집중
   - simple_study (개념 학습): 개념의 정의, 원리, 기본 이론에 집중, 구현 세부사항은 최소화
   - trend_check (트렌드 파악): 최신 동향, 주요 발전 방향, 핵심 아이디어 위주로 구성
   - code_implementation (구현 실습): 실제 구현에 필요한 기술적 개념, 알고리즘, 프레임워크 중심
   - exam_preparation (시험 준비): 시험에 자주 출제되는 핵심 개념, 정의, 공식 중심으로 구성

4. **의미적 중복 노드 제거**
   - 두 키워드가 본질적으로 동일한 개념을 나타내는 경우, 더 일반적이거나 포괄적인 키워드 하나만 유지
   - 한 키워드가 다른 키워드를 완전히 포함하는 상위 개념인 경우, 학습 목적과 수준에 따라 적절한 것 선택
   
   **중복 판단 기준 (보수적으로 적용):**
   - 명확한 동의어 관계: 예) "Neural Network" vs "신경망", "Deep Learning" vs "딥러닝"
   - 완전 포함 관계: 예) "BERT" vs "BERT (language model)" - 괄호 안이 단순 설명인 경우
   - 특수-일반 관계에서 학습 불필요: 예) "Transformer" 있으면 "Transformer Encoder"는 중복 가능
     * 단, 두 개념이 모두 논문 이해에 독립적으로 중요하면 유지
   
   **중복으로 판단하지 말아야 할 경우:**
   - 관련은 있지만 구별되는 개념: 예) "Attention Mechanism" vs "Self-Attention" (서로 다른 개념)
   - 유사하지만 다른 맥락: 예) "Language Model" vs "Language Representation Model" (다른 관점)
   
   **중복 제거 시 우선순위:**
   - ABOUT 엣지로 target_paper와 직접 연결된 키워드 우선 보존
   - strength가 높은 엣지로 연결된 키워드 우선 보존
   - 더 구체적이고 논문의 핵심 기여와 관련된 키워드 우선 보존

5. **학습 시간(budgeted_time) 기반 조절**
   - total_hours와 hours_per_day를 종합적으로 고려하여 학습 강도 판단
   
   **total_hours 기준:**
   - 10시간 미만: 최소한의 핵심 개념만 (5-7개 키워드)
   - 10-25시간: 핵심 개념 + 주요 선행 지식 (8-12개 키워드)
   - 25시간 이상: 포괄적 이해를 위한 확장된 커리큘럼 (12-15개 키워드)
   
   **hours_per_day 기준:**
   - 2시간 이하/일: 학습 부담을 고려하여 더 단순한 개념 우선, 복잡한 고급 개념 최소화
   - 2-4시간/일: 표준 학습 강도, 균형잡힌 난이도 분포
   - 4시간 이상/일: 집중 학습 가능, 도전적인 고급 개념 포함 가능
   
   **total_days 기준:**
   - 3일 이하: 단기 집중, 가장 핵심적인 내용만
   - 3-7일: 중기 학습, 체계적 커리큘럼 구성 가능
   - 7일 이상: 장기 학습, 심화 내용까지 포함 가능

6. **그래프 크기 제한 (최대 15개 키워드 노드)**
   - 우선순위: ABOUT > PREREQ (high strength) > PREREQ (low strength) > REF_BY
   - strength 값이 높은 엣지로 연결된 노드 우선 보존
   - 고립된 노드(isolated node)가 발생하지 않도록 보장
   - 논문 노드는 카운트에 포함하지 않음

7. **그래프 연결성 보장**
   - 필터링 후 모든 키워드 노드가 최소 1개 이상의 엣지로 연결되어야 함
   - target_paper로부터 도달 가능한(reachable) 노드만 포함
   - PREREQ 체인이 끊어지지 않도록 중간 노드 보존

[출력 형식]
반드시 아래 키를 포함한 JSON 객체 하나만 반환하세요:
{{
    "filtered_graph": {{
        "nodes": {{
            "keywords": [/* 필터링된 키워드 노드 리스트 (최대 15개) */],
            "papers": [/* 필터링된 논문 노드 리스트 */]
        }},
        "edges": {{
            "IN": [/* 필터링된 IN 엣지 리스트 */],
            "REF_BY": [/* 필터링된 REF_BY 엣지 리스트 */],
            "PREREQ": [/* 필터링된 PREREQ 엣지 리스트 */],
            "ABOUT": [/* 필터링된 ABOUT 엣지 리스트 */]
        }}
    }},
    "removed_nodes": {{
        "by_level": [/* 수준 불일치로 제거된 키워드 ID 리스트 */],
        "by_known_concepts": [/* 기존 지식으로 제거된 키워드 ID 리스트 */],
        "by_semantic_duplicate": [/* 의미적 중복으로 제거된 키워드 ID 리스트 */],
        "by_priority": [/* 우선순위 낮아 제거된 키워드 ID 리스트 */]
    }},
    "reasoning": "필터링 전략과 주요 결정 사항을 2-3문장으로 설명"
}}

[중요 제약사항]
- filtered_graph.nodes.keywords의 길이는 반드시 15개 이하여야 함
- target_paper는 항상 포함되어야 함
- 모든 노드 ID와 엣지의 source/target은 원본 그래프의 ID와 정확히 일치해야 함
- 출력되는 JSON 객체에는 설명, 주석, 마크다운, 코드블럭을 절대 포함하지 않아야 함
- 의미적 중복 제거는 확실한 경우만 제거
"""),
    ("human", """
[학습자 정보]
- 수준: {user_level}
- 학습 목적: {user_purpose}
- 학습 시간 계획:
  * 총 학습 기간: {total_days}일
  * 하루 학습 시간: {hours_per_day}시간
  * 총 학습 시간: {total_hours}시간
- 기존 지식: {known_concepts}
  * 이미 알고 있는 개념들의 ID 또는 이름 리스트
  * 이 개념들은 가능한 경우 제거하되, 그래프 연결성 유지를 위해 필요하면 보존

[입력 그래프]
{graph_json}

[필터링 지시사항]
1. 위 학습자 정보를 종합적으로 고려하여 최적의 학습 경로를 구성하세요.

2. user_level({user_level})과 user_purpose({user_purpose})의 조합에 따라 필터링 전략을 조정하세요:
   - non_major + simple_study: 가장 기초적인 개념부터 단계적으로, 수식/이론 최소화
   - researcher + deep_research: 고급 방법론과 이론적 기반에 집중, 기초 생략
   - industry + code_implementation: 실용적 구현 관련 키워드 우선, 이론보다 실무 중심
   - bachelor/master + exam_preparation: 핵심 정의와 공식 중심, 시험 출제 가능성 고려
   - master/researcher + trend_check: 최신 동향과 발전 방향, REF_BY 관계 중요하게 고려

3. **의미적 중복 노드 제거 적용:**
   - 입력 그래프의 키워드들을 검토하여 의미적으로 중복되는 노드 쌍을 찾으세요
   - 확실히 중복이라고 판단되는 경우만 제거
   - 중복 제거 시, ABOUT 엣지 연결 여부와 strength를 고려하여 더 중요한 노드 보존
   - 제거된 노드는 removed_nodes.by_semantic_duplicate에 기록

4. 학습 시간 계획을 고려한 조절:
   - 총 {total_hours}시간, 하루 {hours_per_day}시간, {total_days}일 동안 학습
   - hours_per_day가 적을수록 더 단순하고 핵심적인 개념 위주로 구성
   - total_hours에 따라 키워드 개수 조절
   - total_days를 고려하여 개념의 복잡도와 깊이 결정

5. 고립 노드가 발생하지 않도록 엣지 연결성을 검증하세요.

6. 제거된 노드는 removed_nodes에 제거 사유별로 분류하여 기록하세요.

7. 최종 그래프가 target_paper 이해에 충분한 학습 경로를 제공하는지 확인하세요.
     
8. 출력되는 JSON 객체에는 설명, 주석, 마크다운, 코드블럭을 절대 포함하지 않도록 하세요.
""")
])