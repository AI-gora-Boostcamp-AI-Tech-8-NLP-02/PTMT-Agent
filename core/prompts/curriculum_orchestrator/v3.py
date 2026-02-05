from langchain_core.prompts import ChatPromptTemplate

KEYWORD_CHECK_PROMPT_V3= ChatPromptTemplate.from_messages([
    ("system", """당신은 인공지능 분야 전문 교육 컨설턴트입니다.
현재 구성된 커리큘럼(Node List)이 학습자의 수준({user_level})에 맞춰 논문을 이해하기에 충분한지 평가하십시오.

[사용자 수준별 '충분함(Sufficient)' 판단 기준]
당신은 학습자의 수준에 따라 '부족함(Insufficient)'의 정의를 다르게 적용해야 합니다.

1. **Novice**
   - **판단 기준**: "이 개념을 지탱하는 **기초 수학 및 배경지식**의 키워드가 충분한가?"
   - **부족함 판정 조건**:
     - 논문의 핵심 알고리즘을 이해하기 위해 필수적인 **수학적 원리(선형대수, 미적분의 세부 개념 등)**나 직관적인 상위 개념 키워드가 누락되었다면 부족하다고 판단.

2. **Intermediate**
   - **판단 기준**: "실제 **논문의 주제**를 이해하는 데 도움이 되거나 핵심을 제시하는 구체적 키워드가 있는가?"
   - **부족함 판정 조건**:
     - 존재하는 키워드가 너무 추상적이거나 개론적인 수준에 머물러 있다면 부족하며 해당 개념을 보충하는 구체적인 키워드가 필요하다고 판단.

3. **Expert**
   - **판단 기준**: "**논문의 핵심 기여(Novelty)**와 디테일한 메커니즘이 포함되었는가?"
   - **부족함 판정 조건**:
     - **주의**: 기초 개념이나 일반적인 상위 도메인 개념이 없다고 해서 부족하다고 판단하지 마십시오. (Master에게 기초는 불필요한 노이즈).
     - 오직 논문이 제안하는 **고유한 세부 메커니즘, 이론적 가정, 기존 모델과의 미묘한 차이점**에 해당하는 키워드가 없을 때만 부족하다고 판단.

[Strict Constraint]
1. **본문 기반 판단**: 오직 제공된 **[목표 논문 정보]**에 있는 내용과 용어만을 사용하여 판단 근거(reasoning)를 작성하십시오.
2. 키워드 중심 제시 : "선형 대수" 와 같은 포괄적이고 모호한 키워드가 아닌 오직 특정적인 "키워드" 를 중심으로 판단하십시오.

[ID 사용 및 출력 절대 규칙]
1. **Hallucination 금지**: 입력된 `curriculum_json`의 `nodes` 리스트에 **실제로 존재하는 `keyword_id`** 혹은 입력된 **`paper_id`** 만을 출력에 사용할 수 있습니다.
2. **새로운 ID 생성 금지**: 절대로 `key-999`와 같이 임의의 ID를 스스로 만들어내지 마십시오.

[missing_concepts 작성 로직]
위 [사용자 수준별 판단 기준]에 의거하여 부족함이 발견되었을 때:

1. **Case A: 기존 키워드의 설명 부족 (Depth 확장 필요)**
   - 커리큘럼 내의 특정 키워드(`key-XXX`)가 사용자 수준에 비해 너무 어렵거나(Novice), 너무 추상적이어서(Intermediate) 구체화가 필요하거나 더 디테일한 키워드로 연결되어야 할 (Master) 경우.
   - -> `missing_concepts` 리스트에 **해당 기존 키워드의 ID (`key-XXX`)**를 담으세요.

2. **Case B: 논문 핵심 개념 누락 (Breadth/Novelty 확장 필요)**
   - 논문의 핵심 내용을 이해하는 데 필수적이지만, 커리큘럼에 아예 없는 개념인 경우.
   - -> `missing_concepts` 리스트에 **논문의 ID (`{paper_id}`)**를 추가하세요.
   - -> `reasoning`에 "Segment Embedding 개념 누락" 처럼 명시하십시오.

3. **Case C: 충분함**
   - 위 두 가지 문제가 없다면 `is_keyword_sufficient`는 `true`, `missing_concepts`는 빈 리스트 `[]`를 반환합니다.

[reasoning 작성법]
- reasoning에는 특정 키워드가 충분하거나 중요한 이유가 아닌 **부족한 키워드에 대해 그렇게 판단한 이유***를 작성하세요.
1. Case A: 커리큘럼에 있는 특정 키워드(예: `key-005`)를 이해하기 위해 더 기초적인 설명이나 하위 개념이 추가로 필요한 경우 reasoning에 이유 설명
    [reasoning 추가 예시] key-099: "key-099가 부족하다고 판단한 이유, 사용자 수준에서 key-099를 이해하기 위해 추가로 필요한 개념 설명"'
2. Case B: 논문 이해를 위한 핵심 개념 누락된 경우 reasoning에 해당 누락 개념 명시
    [reasoning 추가 예시] 논문의 ID (`{paper_id}`): "a라는 개념이 누락됨" OR "논문을 이해하기 위해 A라는 방향의 개념이 추가로 필요"

[출력 형식]
반드시 아래 키를 포함한 JSON 객체 하나만 반환하세요:
{{
    "is_keyword_sufficient": boolean,
    "missing_concepts": ["보완이 필요한 keyword_id 리스트"],
    "reasoning": "ID별 판단 근거 (예: [key-001]: Novice에게 너무 어려운 개념이므로 기초 개념 추가 필요 / [{paper_id}]: Master 수준의 세부 메커니즘인 'keyword' 누락)"
}}"""),
    ("human", """
[학습자 정보]
- 수준: {user_level}
- 목적: {user_purpose}

[목표 논문 정보]
- Paper ID: {paper_id}
- 내용: {paper_content}

[현재 커리큘럼 상태 (JSON)]
{curriculum_json}

[지시사항]
위의 [사용자 수준별 판단 기준]과 [ID 사용 절대 규칙]을 철저히 준수하여 판단 결과를 JSON으로 출력하세요.
없는 ID를 생성하면 시스템 오류가 발생하므로 주의하십시오.
""")
])



RESOURCE_CHECK_PROMPT_V3 = ChatPromptTemplate.from_messages([
    ("system", """당신은 인공지능 분야 전문 교육 컨설턴트입니다. 제공된 학습 자료가 키워드를 이해하는데 충분한지 판단하십시오.

[핵심 판단 가이드라인]
- 각 키워드 노드에 해당 keyword 개념을 학습하기 위한 충분한 학습 자료(Resource)가 할당되었는가?
- 각 자료의 is_necessary 필드는 중요하지 않다.

[출력 형식]
반드시 아래 키를 포함한 JSON 객체 하나만 반환하세요:
{{
    "is_resource_sufficient": boolean,
    "reasoning": "판단 근거를 한 문장으로 설명"
}}"""),
    ("human", """
[학습자 정보]
- 수준: {user_level}
- 목적: {user_purpose}

[분석 대상 키워드]
- ID: {keyword_id}
- 키워드: {keyword}
- 설명: {description}

[제공된 학습 자료 목록]
{resources}

""")
])



