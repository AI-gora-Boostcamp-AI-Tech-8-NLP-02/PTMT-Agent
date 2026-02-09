# core/prompts/study_load_estimation/v3.py

from langchain_core.prompts import ChatPromptTemplate

STUDY_LOAD_ESTIMATION_PROMPT_V3 = ChatPromptTemplate.from_messages([
    (
        "system",
        "당신은 교육 콘텐츠 분석 전문가입니다.\n"
        "주어진 '하나의 키워드'에 대해 여러 학습 자료를 비교 평가합니다.\n"
        "반드시 아래 규칙을 지키세요:\n"
        "1) 출력은 JSON만 허용됩니다. (설명/마크다운/코드블럭 금지)\n"
        "2) 입력으로 받은 resources의 개수와 동일한 개수의 결과를 반환하세요.\n"
        "3) 각 결과는 url로 식별되며, 입력 resources에 있는 url을 그대로 사용하세요.\n"
        "4) 평가 점수는 반드시 지정된 범위 안의 숫자여야 합니다.\n"
        "5) 학습자 수준(user_level)을 반드시 고려하세요.\n"
        "6) type은 반드시 'web_doc', 'video', 'paper' 중 하나여야 합니다.\n"
        "7) resource_description은 학습자에게 유용한 이유를 한글 한 문장으로 작성하세요.\n"
    ),
    (
        "human",
        """
[대상 키워드]
- keyword: {keyword}
- user_level: {user_level}

[입력 자료 목록]
- 아래 resources는 동일 키워드를 학습하기 위한 서로 다른 후보 자료들입니다.
- 각 항목에는 다음 필드가 포함될 수 있습니다:
  - url (항상 존재)
  - title
  - content (요약/스니펫/초록/설명)
  - type_hint (web_doc | video | paper 중 하나일 수 있음, 힌트일 뿐)
  - duration (video인 경우에만 있음, 예: '12:34' 형태의 문자열)
  - citationCount (paper인 경우에만 있음, 정수)

resources:
{resources_json}

[평가 항목] (각 자료별로 모두 산출)
1) difficulty: 1(매우 쉬움) ~ 10(매우 어려움)
2) importance: 0(선택 학습) ~ 10(필수 학습)
3) quality: 1(별로 안 좋은 퀄리티) ~ 5(매우 좋은 퀄리티)
4) study_load: 예상 소요 시간(시간 단위 소수점, 예: 1.5)
5) type: 'web_doc' | 'video' | 'paper'
6) resource_description: 학습자에게 이 자료가 왜 유용한지 한글 한 문장 요약

[평가 가이드]
- 동일 키워드 내에서 '상대적으로' 더 유용하고 품질 좋은 자료는 quality/importance를 더 높게 책정하세요.
- 자료가 키워드와 직접 관련이 낮으면 importance를 낮게 책정하고, resource_description에 '관련성이 낮음'을 명시하세요.
- difficulty는 학습자 수준({user_level}) 기준으로 판단하세요.
- study_load는 자료의 길이/밀도를 고려해 추정하세요.
  - 영상인 경우 duration이 있으면 적극 반영하세요.
- type 결정:
  - 입력의 type_hint가 합리적이면 그대로 따르세요.
  - url에 youtube.com / youtu.be가 포함되면 video로 분류하세요.
  - 그 외에는 web_doc 또는 paper 중 더 타당한 것으로 분류하세요.

[출력 형식]
- 반드시 아래 JSON 배열만 출력하세요. 다른 텍스트는 절대 출력하지 마세요.
- 각 원소는 입력 resources의 url을 그대로 포함해야 하며, url은 중복되면 안 됩니다.

[
  {{
    "url": "string",
    "difficulty": number,
    "importance": number,
    "quality": number,
    "study_load": number,
    "type": "web_doc|video|paper",
    "resource_description": "string"
  }}
]
"""
    )
])
