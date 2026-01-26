"""
Paper-Concept Alignment 프롬프트 모듈
"""
from core.prompts.paper_concept_alignment.v1 import (
    SYSTEM_PROMPT,
    ALIGNMENT_PROMPT_TEMPLATE,
    OUTPUT_FORMAT_INSTRUCTIONS,
    format_paper_body,
    format_keywords_list,
)

__all__ = [
    "SYSTEM_PROMPT",
    "ALIGNMENT_PROMPT_TEMPLATE",
    "OUTPUT_FORMAT_INSTRUCTIONS",
    "format_paper_body",
    "format_keywords_list",
]
