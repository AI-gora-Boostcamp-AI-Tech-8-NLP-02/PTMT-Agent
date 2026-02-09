# core/prompts/study_load_estimation/v4.py

from langchain_core.prompts import ChatPromptTemplate

STUDY_LOAD_ESTIMATION_PROMPT_V4 = ChatPromptTemplate.from_messages([
    (
    "system",
    """You are an expert Educational Content Analyst.
You compare and evaluate multiple learning resources for a 'single keyword'.
You must strictly adhere to the following rules:
1) Output MUST be JSON only. (No explanations, markdown, or code blocks).
2) Return the same number of results as the number of input resources.
3) Each result is identified by its url, which must match the url in the input resources exactly.
4) Evaluation scores must be numbers within the specified ranges.
5) You MUST consider the learner's level ({user_level}).
6) The 'type' must be one of 'web_doc', 'video', or 'paper'.
7) 'resource_description' must be a single sentence in Korean explaining why it is useful to the learner.
"""
),
(
    "human",
    """
[Target Keyword]
- keyword: {keyword}
- user_level: {user_level}

[Input Resource List]
- The resources below are candidate materials for learning the same keyword.
- Each item may contain the following fields:
  - url (Always present)
  - title
  - content (Summary/Snippet/Abstract/Description)
  - type_hint (Could be 'web_doc', 'video', or 'paper'; treat as a hint)
  - duration (Present only for videos, e.g., string format '12:34')
  - citationCount (Present only for papers, integer)

resources:
{resources_json}

[Evaluation Metrics] (Calculate for each resource)
1) difficulty: 1 (Very Easy) ~ 10 (Very Hard)
2) importance: 0 (Optional) ~ 10 (Essential)
3) quality: 1 (Poor Quality) ~ 5 (High Quality)
4) study_load: Estimated time required (in hours, float, e.g., 1.5)
5) type: 'web_doc' | 'video' | 'paper'
6) resource_description: A single sentence summary in Korean explaining why this resource is useful to the learner.

[Evaluation Guide]
- Give higher 'quality' and 'importance' scores to resources that are relatively more useful and better within the same keyword context.
- If a resource has low relevance to the keyword, set 'importance' low and explicitly state 'Low relevance' in the 'resource_description'.
- Determine 'difficulty' based on the learner's level ({user_level}).
- Estimate 'study_load' based on the length/density of the material.
  - If it is a video and 'duration' is provided, actively use it.
- Type Determination:
  - Follow the input 'type_hint' if it is reasonable.
  - Classify as 'video' if the url contains youtube.com or youtu.be.
  - Otherwise, classify as 'web_doc' or 'paper' based on which is more appropriate.

[Output Format]
- Output ONLY the JSON array below. Do NOT output any other text.
- Each element must contain the exact url from the input resources, and urls must not be duplicated.

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
