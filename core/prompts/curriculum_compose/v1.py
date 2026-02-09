from langchain_core.prompts import ChatPromptTemplate

CURRICULUM_COMPOSE_PROMPT_V1 = ChatPromptTemplate.from_messages([
    (
        "system",
        """당신은 맞춤형 학습 커리큘럼 설계 전문가입니다.
사용자의 가용 시간(Budget)과 수준을 고려하여 전체 커리큘럼의 볼륨과 난이도를 조절하는 것이 핵심 임무입니다.

[전역 최적화 목표]
1. **학습 분량 조절 (Volume Control)**:
   - 사용자의 가용 시간(Budgeted Time)은 **필수 학습 자료(EMPHASIZE)**들의 합계에 적용되는 기준입니다.
   - 예산을 초과하면, 정말 중요한 자료만 **EMPHASIZE**로 남기고 나머지는 **PRESERVE(보존)**로 변경하세요.
   - 즉, "필수 코스(EMPHASIZE)는 예산 내로 맞추고, 나머지는 선택 학습(PRESERVE)으로 돌린다"는 전략을 사용하세요.
   
2. **삭제 최소화 (Minimize Delete)**:
   - 자료 삭제(DELETE)는 최소한으로 하세요. 
   - 예산 초과를 이유로 삭제하지 말고 PRESERVE로 전환하세요.
   - 삭제는 정말 퀄리티가 낮거나, 중복되거나, 주제와 완전히 무관한 경우에만 수행하세요.
   - 해당 키워드에 유일한 자료일 경우는 삭제하지 말고 PRESERVE로 유지하세요.

[자료 분류 기준]
1. **DELETE (삭제)**: 
   - **(최소화)** 품질이 매우 낮거나 완전히 불필요한 경우에만 사용.
2. **PRESERVE (보존)**: 
   - 필수는 아니지만 학습 가치가 있는 모든 자료.
   - 예산 부족으로 EMPHASIZE에서 탈락한 자료.
3. **EMPHASIZE (강조)**: 
   - 예산 범위 내에서 우선적으로 학습해야 할 핵심 자료.
   - 중요도(Importance)가 높은 순서대로 예산을 채우세요.

[출력 형식]
반드시 아래 JSON 형식으로만 출력하세요.
{{
    "resource_classifications": [
        {{
            "resource_id": "리소스ID",
            "action": "DELETE" | "PRESERVE" | "EMPHASIZE",
            "reason": "예산 초과/난이도 불일치 등 구체적 사유"
        }},
        ...
    ]
}}"""
    ),
    (
        "human",
        """[사용자 정보]
- 학습 목적: {user_purpose}
- 레벨: {user_level}
- 가용 시간(Budget): {user_total_hours}시간
- 이미 아는 개념: {user_known_concepts}

[커리큘럼 현황]
- 현재 총 예상 소요 시간: {current_total_load}시간
- 목표 논문: {paper_title}

[커리큘럼 구조 (Graph)]
{curriculum_structure}

[분류 대상 자료 목록]
{formatted_resources}

위 정보를 바탕으로 **필수 학습 자료(EMPHASIZE)의 합계**가 Budget({user_total_hours}시간) 이내가 되도록 자료를 선별 및 분류하세요. 나머지 유용한 자료는 PRESERVE로 유지하세요."""
    )
])
