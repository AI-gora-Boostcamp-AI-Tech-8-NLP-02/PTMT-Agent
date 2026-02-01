from langchain_core.prompts import ChatPromptTemplate

CONCEPT_EXPANSION_PROMPT_V2 = ChatPromptTemplate.from_messages([
    (
        "system",
        "너는 학습 커리큘럼과 개념 구조를 설계하는 전문 AI 리서치 어시스턴트다. "
        "입력된 키워드 그래프를 분석하여 학습 흐름상 누락된 개념이 있는지 판단하고, "
        "필요한 경우에만 새로운 개념을 추가한다. "
        "반드시 제공된 tool(웹 검색)을 활용해 "
        "개념 간 선후관계나 포함 관계를 검증한다. "
        "반드시 지시를 정확히 따르고 JSON 형식으로만 출력해야 한다."
    ),
    (
        "human",
        """
        아래는 현재 학습 키워드 그래프이다.
        이 그래프를 기반으로 학습 흐름을 개선하기 위해
        추가로 필요한 개념이 있는지 판단하라.

        ### 목표 논문
        {paper_info}

        ### 이미 사용자가 알고 있는 개념
        {known_concept}

        ### 현재 키워드 그래프 (JSON)
        {keyword_graph}

        ### 개념 확장 요청 이유
        {reason}
        
        ### 보충이 필요한 개념 키워드 ID 리스트
        {keyword_ids}

        다음 규칙을 반드시 지켜라.

        1. 기존 키워드 그래프의 노드와 엣지는 절대 다시 출력하지 마라.
        2. 이미 사용자가 알고 있는 개념과 일치하거나 매우 유사한 개념은 절대 출력하지 마라.
        3. 새롭게 추가해야 한다고 판단한 개념만 노드로 출력하라.
        4. 새 노드는 기존 키워드 또는 새 키워드와의 관계를 나타내는 엣지를 반드시 포함해야 한다.
        5. 엣지는 반드시 keyword_id 기반으로 연결하라.
        6. 키워드 간 선후 관계 edge를 생성하는 경우 반드시 tool(웹 검색)을 사용하여
           개념 간 관계를 검증한 뒤 edge를 생성하라. (키워드 간 선후 관계를 판단한 이유를 reason에 작성한다.)
        7. 추가할 개념이 전혀 없다고 판단되면 nodes와 edges를 빈 배열로 출력하라.

        반드시 아래 JSON 형식으로만 출력하라.
        설명, 주석, 마크다운, 코드블록(```)은 절대 포함하지 마라.

        {{
          "expanded_graph": {{
            "nodes": [
              {{
                "keyword_id": string,
                "keyword": string,
              }}
            ],
            "edges": [
              {{
                "start": string,
                "end": string,
                "reason": string
              }}
            ]
          }}
        }}
        """
    )
])
