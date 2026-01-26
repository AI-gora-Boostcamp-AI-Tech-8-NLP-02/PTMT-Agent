from langchain_core.prompts import ChatPromptTemplate

QUERY_GEN_PROMPT_V1 = ChatPromptTemplate.from_messages([
    (
        "system",
        "당신은 논문 학습에 필요한 핵심 개념을 검색하기 위한 최적의 검색어를 생성하는 에이전트입니다. "
        "설명 없이 검색어만 출력하세요."
        "검색어는 반드시 정확히 2개만 생성하세요."
    ),
    (
        "human",
        "대상 키워드: '{keyword}', 상세 설명: '{description}'. "
        "이 개념을 이해하기 위해 검색해야 할 서로 다른 관점의 검색어 2개를 줄바꿈으로 구분해 생성하세요."
    )
])


