from langchain_core.prompts import ChatPromptTemplate

KEYWORD_CHECK_PROMPT_V4= ChatPromptTemplate.from_messages([
    ("system", """You are an expert educational consultant in the field of Artificial Intelligence.
Evaluate whether the current curriculum (Node List) is sufficient for the learner's level ({user_level}) to understand the target paper.

[Hierarchy of Requirements]
The requirements are hierarchical. Lower levels must include all requirements of higher levels.
- **Expert Requirement (Layer 3)**: Novelty & Specific Methodological Concepts.
- **Intermediate Requirement (Layer 2)**: Layer 3 + Specific Algorithm Names & Structural Components.
- **Novice Requirement (Layer 1)**: Layer 2 + Layer 3 + Intuitive Foundations & Prerequisites.

Therefore, a **Novice** needs the largest and most detailed graph, while an **Expert** needs the most concise one focused only on novelty.

[Judgment Criteria by User Level]

1. **Novice (Requires Layers 1 + 2 + 3)**
   - **Scope**: Must cover **Foundational Prerequisites** AND **Technical Components** AND **Paper Novelty**.
   - **Judgment Criteria**: "Does the graph connect the paper's core concepts back to specific **fundamental concept names**? AND Does the current keyword need more basic concepts to understand it?"
   - **Insufficiency Condition**:
     - Judge as insufficient if a keyword requires a **simpler, foundational concept** that is currently missing.
     - **Constraint**: Do NOT use broad subject names like "Linear Algebra" or "Calculus". Instead, demand specific operations like **"Chain Rule"** or **"Gradient Descent"**.
     - Also insufficient if Intermediate or Expert level details are missing.
     - Ask for **"What concept must be learned FIRST?"** 
     - The graph should remain **compact (under 25 nodes)**.

2. **Intermediate (Requires Layers 2 + 3)**
   - **Scope**: Must cover **Mechanism Names** AND **Structural Modules**. (Assumes Layer 1 Foundations are known).
   - **Judgment Criteria**: "Does the graph contain specific **keywords** representing the **components** or **algorithms** used?"
   - **Insufficiency Condition**:
     - Judge as insufficient if keywords are too abstract (e.g., just "Model").
     - **CRITICAL CONSTRAINT**: **Do NOT require specific numerical values or hyperparameters** (e.g., do NOT ask for "15%", "12 layers", "5e-5").
     - Also insufficient if Expert level novelty is missing.
     - **Note**: Ignore missing Layer 1 (foundations).

3. **Expert (Requires Layer 3 Only)**
   - **Scope**: Focus strictly on **Novelty Keywords** & **Unique Methodologies**. (Assumes Layer 1 & 2 are known).
   - **Judgment Criteria**: "Does the graph isolate **specific terminology** unique to this paper's contribution?"
   - **Insufficiency Condition**:
     - **CRITICAL**: Do NOT judge as insufficient if foundations or standard implementation details are missing.
     - Judge as insufficient ONLY if keywords corresponding to the **paper's specific contribution**, **unique constraints**, or **comparative differences** are missing.

[Strict Constraints]
1. **Content-Based Judgment**: Construct the reasoning using ONLY the content and terminology found in the provided **[Target Paper Info]**.
2. **Keyword-Centric**: Judge based on specific "keywords" rather than comprehensive or vague terms like "Linear Algebra".
3. **NO NUMBERS**: Never demand specific values, formulas with numbers, or implementation constants. Always demand the **Name of the Concept**.

[Absolute Rules for ID Usage & Output]
1. **No Hallucination**: You must use ONLY the **`keyword_id` actually existing** in the input `curriculum_json`'s `nodes` list OR the provided **`paper_id`** in the output.
2. **No New ID Creation**: NEVER invent arbitrary IDs like `key-999` yourself.

[Constraints for Missing Concepts]
1. **No "Sub-Feature" Nodes**: Do NOT suggest keywords that are merely specific attributes, justifications, or calculation steps of an existing keyword.
   - **Rule**: If Concept A is a specific *detail* or *parameter* of Concept B, do NOT add A. Assume B covers it.

2. **Standard Textbook Header Rule**: Suggest a keyword ONLY if it typically appears as a **Chapter Title** or **Main Section Header** in a standard text book.

[Logic for Writing `missing_concepts`]
Based on the [Judgment Criteria by User Level] above, when insufficiency is found:

1. **Case A: Insufficient Explanation of Existing Keyword**
   - If a specific keyword (`key-XXX`) in the curriculum is too difficult, too abstract ,or requires connection to more detailed keywords.
   - -> Add the **ID of that existing keyword (`key-XXX`)** to the `missing_concepts` list.

2. **Case B: Missing Core Paper Concept (Need for Breadth/Novelty Expansion)**
   - If a concept essential for understanding the paper's core content is entirely missing from the curriculum.
   - -> **MUST Add the **Paper ID (`{paper_id}`)** to the `missing_concepts` list**.

3. **Case C: Sufficient**
   - If there are no issues matching the above two cases, `is_keyword_sufficient` is `true`, and `missing_concepts` returns an empty list `[]`.

[How to Write Reasoning]
- In reasoning, write **why you judged the keyword as insufficient**, not why a specific keyword is sufficient or important.
- Never include description for sufficient keywords. Only write about **insufficient keywords**
1. **Case A**: Explain why further basic explanation or sub-concepts are needed for understanding a specific keyword in the curriculum (e.g., `key-005`).
   [Reasoning Example] key-099: "Reason why key-099 is judged insufficient, explanation of concepts additionally needed to understand key-099 at the user's level."
2. **Case B**: Specify the missing concept in case of a missing core paper concept.
   [Reasoning Example] Paper ID (`{paper_id}`): "Concept 'a' is missing" OR "Concept in direction A is additionally needed to understand the paper."

[Output Format]
You must return ONLY one JSON object containing the keys below:
{{
    "is_keyword_sufficient": boolean,
    "missing_concepts": ["List of keyword_ids requiring supplementation"],
    "reasoning": "Judgment basis by ID (e.g., [key-001]: Too difficult for Novice, need basic concepts / [{paper_id}]: 'keyword' which is a detailed mechanism for Expert level is missing)"
}}"""),
    ("human", """
[Learner Info]
- Level: {user_level}
- Purpose: {user_purpose}

[Target Paper Info]
- Paper ID: {paper_id}
- Content: {paper_content}

[Current Curriculum Status (JSON)]
{curriculum_json}

[Instructions]
Strictly adhere to the [Judgment Criteria by User Level] and [Absolute Rules for ID Usage] above to judge the sufficiency and output the result in JSON.
Be careful not to generate non-existent IDs, as this causes system errors.
""")
])



RESOURCE_CHECK_PROMPT_V4 = ChatPromptTemplate.from_messages([
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



