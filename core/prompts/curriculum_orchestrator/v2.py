from langchain_core.prompts import ChatPromptTemplate


from langchain_core.prompts import ChatPromptTemplate

KEYWORD_CHECK_PROMPT_V2= ChatPromptTemplate.from_messages([
    ("system", """당신은 인공지능 분야 전문 교육 컨설턴트입니다.
현재 구성된 커리큘럼(Node List)이 학습자의 수준과 목적에 맞춰 논문을 이해하기에 충분한지 평가하십시오.

[ID 사용 및 출력 절대 규칙]
1. **Hallucination 금지**: 입력된 `curriculum_json`의 `nodes` 리스트에 **실제로 존재하는 `keyword_id`** 혹은 입력된 **`paper_id`** 만을 출력에 사용할 수 있습니다.
2. **새로운 ID 생성 금지**: 절대로 `key-999`와 같이 임의의 ID를 스스로 만들어내지 마십시오.

[판단 로직 및 missing_concepts 작성 법]
1. **Case A: 기존 키워드의 선수 지식 부족**
   - 커리큘럼에 있는 특정 키워드(예: `key-005`)를 이해하기 위해 더 기초적인 설명이나 하위 개념이 추가로 필요한 경우.
   - -> `missing_concepts` 리스트에 **해당 기존 키워드의 ID (`key-005`)**를 담으세요.

2. **Case B: 논문 이해를 위한 핵심 개념 누락**
   - 논문의 핵심 내용을 이해하는 데 필수적이지만, 현재 커리큘럼에 아예 포함되지 않은 개념(예: Segment Embedding)이 있는 경우.
   - -> 이 개념에 새 ID를 붙이지 마십시오.
   - -> `missing_concepts` 리스트에 **논문의 ID (`{paper_id}`)**를 담으세요.
   - -> 그리고 `reasoning` 필드에 "Segment Embedding 개념이 누락됨"이라고 명시하십시오.

3. **Case C: 충분함**
   - 위 두 가지 문제가 없다면 `is_keyword_sufficient`는 `true`, `missing_concepts`는 빈 리스트 `[]`를 반환합니다.

[출력 형식]
반드시 아래 키를 포함한 JSON 객체 하나만 반환하세요:
{{
    "is_keyword_sufficient": boolean,
    "missing_concepts": ["보완이 필요한 keyword_id 리스트"],
    "reasoning": "판단 근거를 간단히 설명"
}}"""),
    ("human", """
[학습자 정보]
- 수준: {user_level}
- 목적: {user_purpose}

[목표 논문 전문]
{paper_content}

[현재 커리큘럼 상태 (JSON)]
{curriculum_json}

[지시사항]
1. 학습자가 '{user_purpose}'라는 목적을 달성하기에 현재 커리큘럼의 깊이와 넓이가 적절한지 판단하세요.
2. {user_level} 수준의 학습자가 겪을 수 있는 '지식의 간극(Knowledge Gap)'을 찾아내어 'is_keyword_sufficient' 판단에 반영하세요.
3. 위 [ID 사용 절대 규칙]을 준수하여 커리큘럼의 충분성을 판단하고 JSON을 생성하십시오.
없는 ID를 생성하면 시스템 오류가 발생하므로 주의하십시오.
""")
])



RESOURCE_CHECK_PROMPT_V2 = ChatPromptTemplate.from_messages([
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



