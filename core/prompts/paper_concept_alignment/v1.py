"""
Paper-Concept Alignment Agent 프롬프트 정의 (v1)
"""

SYSTEM_PROMPT = """당신은 학술 논문과 학습 개념(키워드) 간의 연관성을 분석하는 전문가입니다.
주어진 논문의 내용을 깊이 이해하고, 각 키워드가 해당 논문의 커리큘럼에 왜 포함되어야 하는지를 
명확하고 교육적인 관점에서 설명해야 합니다.

분석 시 다음 사항을 고려하세요:
1. 키워드가 논문의 핵심 개념, 방법론, 또는 배경 지식과 어떻게 연결되는지
2. 해당 키워드를 이해하는 것이 논문 이해에 어떤 도움이 되는지
3. 논문에서 해당 키워드가 직접적으로 언급되거나 암시적으로 사용되는 부분

응답은 한국어로 작성하며, 학습자가 이해하기 쉬운 언어를 사용하세요."""


ALIGNMENT_PROMPT_TEMPLATE = """## 논문 정보

### 제목
{paper_title}

### 저자
{paper_authors}

### 초록 (Abstract)
{paper_abstract}

### 본문 요약
{paper_body_summary}

---

## 분석할 키워드 목록

{keywords_list}

---

## 작업 지시

위 논문의 내용을 바탕으로, 각 키워드가 이 논문의 학습 커리큘럼에 포함된 이유를 설명해주세요.

각 키워드에 대해 다음을 포함하는 설명을 작성해주세요:
1. 해당 키워드와 논문의 구체적인 연관성
2. 논문 이해를 위해 이 키워드가 필요한 이유
3. 논문에서 이 개념이 어떻게 활용되거나 언급되는지 (해당되는 경우)

응답 형식:
각 키워드 ID에 대해 2-4문장의 간결하고 명확한 설명을 제공해주세요.

{format_instructions}"""


def format_paper_body(body_sections: list) -> str:
    """논문 본문을 요약 형태로 포맷팅"""
    if not body_sections:
        return "본문 정보 없음"
    
    formatted_sections = []
    for section in body_sections[:10]:  # 최대 10개 섹션만 포함
        subtitle = section.get("subtitle", section.subtitle if hasattr(section, "subtitle") else "")
        text = section.get("text", section.text if hasattr(section, "text") else "")
        # 각 섹션의 텍스트를 500자로 제한
        truncated_text = text[:500] + "..." if len(text) > 500 else text
        formatted_sections.append(f"**{subtitle}**\n{truncated_text}")
    
    return "\n\n".join(formatted_sections)


def format_keywords_list(nodes: list) -> str:
    """키워드 리스트를 포맷팅"""
    if not nodes:
        return "키워드 없음"
    
    formatted = []
    for node in nodes:
        keyword_id = node.get("keyword_id", node.keyword_id if hasattr(node, "keyword_id") else "")
        keyword = node.get("keyword", node.keyword if hasattr(node, "keyword") else "")
        formatted.append(f"- **{keyword}** (ID: {keyword_id})")
    
    return "\n".join(formatted)


OUTPUT_FORMAT_INSTRUCTIONS = """
응답은 반드시 다음 JSON 형식으로 작성해주세요:
```json
{
    "alignments": {
        "keyword_id_1": "키워드 1과 논문의 연관성 설명...",
        "keyword_id_2": "키워드 2와 논문의 연관성 설명...",
        ...
    }
}
```

모든 키워드 ID에 대해 빠짐없이 설명을 작성해주세요.
"""
