from typing import TypedDict, Literal
from core.contracts.types.user_info import UserInfo
from core.contracts.types.curriculum import (
    CurriculumGraph as CurriculumData,
    KeywordNode,
    KeywordEdge
)

class CurriculumComposeInput(TypedDict):
    user_info: UserInfo
    curriculum: CurriculumData

class CurriculumComposeOutput(TypedDict):
    curriculum: CurriculumData

# 에이전트 내부 판단용 타입
class NodeAction(TypedDict):
    keyword_id: str
    action: Literal["DELETE", "PRESERVE", "EMPHASIZE"]
    reason: str
