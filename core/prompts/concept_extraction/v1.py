from langchain_core.prompts import ChatPromptTemplate

CONCEPT_EXTRACTION_PROMPT_V1 = ChatPromptTemplate.from_messages([
    (
        "system",
        "너는 AI 연구 논문을 분석하는 전문 리서치 어시스턴트다. "
        "반드시 지시를 정확히 따르고 JSON 형식으로만 출력해야 한다."
    ),
    (
        "human",
        """
        아래는 구조화된 논문 전체 내용이다.
        논문의 핵심 기여와 목적이 잘 드러나도록 요약하고,
        논문을 대표하는 핵심 개념(Concept) 3~5개를 추출하라.

        ### 논문 내용
        {paper_content}

        반드시 아래 JSON 형식으로만 출력하라.
        설명, 주석, 마크다운, 코드블록(```)은 절대 포함하지 마라.

        {{
        "paper_summary": string,
        "paper_concepts": string[]
        }}
        """
    )
])
