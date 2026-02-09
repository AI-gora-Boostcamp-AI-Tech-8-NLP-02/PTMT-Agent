from langchain_core.prompts import ChatPromptTemplate

FIRST_CONCEPT_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "너는 AI 연구 논문을 분석하는 전문 리서치 어시스턴트다. "
        "논문의 핵심 기여와 연구 목적을 정확히 파악하는 것이 목표다. "
        "반드시 지시를 정확히 따르고 JSON 형식으로만 출력해야 한다."
    ),
    (
        "human",
        """
        아래는 하나의 AI 연구 논문의 전체 내용이다.
        논문의 핵심 기여와 연구 목적이 잘 드러나도록 요약하고,
        **논문을 대표하는 핵심 개념(Concept)** 을 3~5개 추출하라.

        ### 추출 기준
        - paper_summary는 한글로 작성할 것
        - paper_concepts는 영어 단어 또는 짧은 구문으로 작성할 것

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
        "너의 역할은 '개념을 설명하는 것'이 아니라 "
        "'하나의 명확한 개념을 대표하는 위키 표제어 수준의 용어'를 선택하는 것이다. "
        "반드시 지시를 정확히 따르고 JSON 형식으로만 출력해야 한다."
    ),
    (
        "human",
        """
        아래는 하나의 AI 연구 논문에 대한 정보이다.
        이 논문을 이해하기 위해 사용자가 **사전에 학습해야 할 핵심 개념들**을 추출하라.

        다음 정보를 종합적으로 고려하라:
        - 논문의 주제와 연구 목적
        - 1차로 추출된 논문 대표 핵심 개념
        - 해당 개념들과 연관된 위키 표제어

        ### 추출 기준
        - 논문을 읽기 위해 알고 있어야 하는 개념일 것
        - 의미가 중복되는 개념은 하나로 정리할 것
        - 최종 개념 개수는 3~5개로 제한할 것
        - 모든 개념은 영어로 출력할 것
        - 각 항목은 **위키 문서의 표제어가 될 수 있는 단일 개념 명사**여야 한다.
        - 설명 문장, 수식, 복합 표현, 서술형 문구는 절대 허용하지 않는다.
        - 불필요한 형용사나 수식어는 제거하고 가장 기본적인 개념명으로 정규화하라.

        ### 논문 제목
        {paper_name}
        
        ### 논문 요약
        {paper_summary}

        ### 논문 내용
        #### Abstract
        {paper_abstract}
        
        #### Body
        {paper_body}
        
        ### 1차 핵심 개념 (논문 대표 개념)
        {initial_concepts}
        
        ### 관련 위키 표제어
        {wiki_words}

        반드시 아래 JSON 형식으로만 출력하라.
        설명, 주석, 마크다운, 코드블록(```)은 절대 포함하지 마라.

        {{
            "paper_concepts": string[]
        }}
        """
    )
])