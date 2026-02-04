from langchain_core.prompts import ChatPromptTemplate


from langchain_core.prompts import ChatPromptTemplate

KEYWORD_CHECK_PROMPT_V1= ChatPromptTemplate.from_messages([
    ("system", """당신은 인공지능 분야 전문 교육 컨설턴트입니다. 커리큘럼을 구성하고 있는 키워드가 논문을 이해하기에 충분한지 판단하십시오.

[핵심 판단 가이드라인]
- 논문을 이해하기 위한 필수 개념이 포함되지 않았다면 충분하지 않다고 판단합니다.
- 판단 기준은 실험이나 실제 케이스가 아닌 개념 keyword 단위이며 이미 유사한 키워드가 있을 경우 충분하다고 가정합니다.
- 학습자({user_level})의 수준을 고려할 때 키워드 자체를 이해하기 위해 curriculum 상에 존재하지 않는 다른 개념이 필요할 경우 is_keyword_sufficient가 false라고 판단하고 해당 해당 키워드의 id를 missing_concepts에 추가한다.
- 논문과 keyword의 직접 연결 여부는 중요하지 않다. 필요한 개념이 curriculum 안에 존재하고 key-000 형태의 아이디가 할당되어 있으면 해당 keyword는 포함된 것으로 판단합니다.
- missing concepts는 curriculum 상에 없는 개념이 아닌 독립적으로 이해할 수 없고 이해하기 위해 타 개념이 추가로 curriculum에 존재해야 하는 curriculum에 이미 존재하는 keyword의 id이다.
- 논문 자체를 이해하기 위해 curriculum에 없는 새로운 keyword가 필요할 경우 missing_concepts에 논문의 id (paper_id)를 넣는다.


[출력 형식]
반드시 아래 키를 포함한 JSON 객체 하나만 반환하세요:
{{
    "is_keyword_sufficient": boolean,
    "missing_concepts": ["보완이 필요한 keyword_id 리스트"],
    "reasoning": "판단 근거를 한 문장으로 설명"
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

""")
])



RESOURCE_CHECK_PROMPT_V1 = ChatPromptTemplate.from_messages([
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



