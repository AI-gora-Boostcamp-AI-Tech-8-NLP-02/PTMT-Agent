from typing import List, TypedDict, Optional
from core.contracts.types.paper_info import PaperInfo
from core.contracts.types.curriculum import CurriculumGraph
from core.contracts.types.user_info import UserInfo


class FirstNodeOrderAgentInput(TypedDict):
    paper_content: PaperInfo
    curriculum: CurriculumGraph
    user_info: UserInfo

class FirstNodeOrderAgentOutput(TypedDict):
    curriculum: CurriculumGraph
