# core/prompts/study_load_estimation/v2.py

from langchain_core.prompts import ChatPromptTemplate

STUDY_LOAD_ESTIMATION_PROMPT_V2 = ChatPromptTemplate.from_messages([
    (
        "system",
        "당신은 교육 콘텐츠 분석 전문가입니다. 주어진 학습 자료를 분석하여 "
        "반드시 지시사항에 따라 JSON 형식으로만 평가를 반환하세요."
    ),
    (
        "human",
        """
        [대상 정보]
        - 키워드: {keyword}
        - 자료명: {title}
        - 내용 요약: {content}
        - 학습자 수준: {user_level}

        [평가 항목]
        1. difficulty: 1(매우 쉬움) ~ 10(매우 어려움)
        2. importance: 0(선택 학습) ~ 10(필수 학습)
        3. study_load: 예상 소요 시간 (1시간 단위 소수점, 예: 1.5)
        4. type: 'web_doc', 'video', 'paper' 중 하나
        5. resource_description: 학습자를 위해 이 자료가 왜 유용한지 설명하는 한 문장 요약 (한글로 작성)

        [평가 가이드]
        - {user_level} 수준의 학습자 입장에서 난이도와 중요도를 판단하세요.
        - study_load는 자료의 실제 길이를 고려하세요. (영상 재생 시간 등)
        - 반드시 아래 JSON 형식으로만 출력하세요. 마크다운 태그(```)는 절대 금지입니다.
        - {keyword}와 자료 간의 관계 정도가 낮을 시 importance를 낮게 책정하고 resource_description에 관계가 낮다는 것을 명시하세요.
        
        {{
            "difficulty": number,
            "importance": number,
            "study_load": number,
            "type": string,
            "resource_description": string
        }}
        """
    )
])