from langchain_core.prompts import ChatPromptTemplate

FIRST_CONCEPT_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
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
        논문을 대표하는 핵심 개념(Concept) 단어를 3~5개 추출하라.
        paper_summary는 한글로, paper_concepts는 영어로 추출하라.
        
        ### 논문 제목
        {paper_name}

        ### 논문 내용
        #### Abstract
        {paper_abstract}
        
        #### Body
        {paper_body}

        반드시 아래 JSON 형식으로만 출력하라.
        설명, 주석, 마크다운, 코드블록(```)은 절대 포함하지 마라.

        {{
            "paper_summary": string,
            "paper_concepts": string[]
        }}
        """
    )
])

FINAL_CONCEPT_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "너는 AI 연구 논문을 분석하는 전문 리서치 어시스턴트다. "
        "반드시 지시를 정확히 따르고 JSON 형식으로만 출력해야 한다."
    ),
    (
        "human",
        """
        아래는 구조화된 논문 요약 및 전체 내용 이다.
        1차 추출 핵심 개념과 관련 위키 표제어를 바탕으로
        주어진 논문을 대표하는 핵심 개념(Concept) 단어를 3~5개를 위키 표제어 형태로 추출하라.
        paper_concepts는 영어로 추출하라.
        
        ### 논문 제목
        {paper_name}
        
        ### 논문 요약
        {paper_summary}

        ### 논문 내용
        #### Abstract
        {paper_abstract}
        
        #### Body
        {paper_body}
        
        ### 1차 핵심 개념
        {initial_concepts}
        
        ### 위키 표제어
        {wiki_words}

        반드시 아래 JSON 형식으로만 출력하라.
        설명, 주석, 마크다운, 코드블록(```)은 절대 포함하지 마라.

        {{
            "paper_concepts": string[]
        }}
        """
    )
])