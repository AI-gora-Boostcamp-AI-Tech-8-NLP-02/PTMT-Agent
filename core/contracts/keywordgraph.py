from typing import TypedDict, List
from core.contracts.types.paper_info import PaperInfo
from core.contracts.types.user_info import UserInfo
from core.contracts.types.subgraph import Subgraph

class KeywordGraphInput(TypedDict):
    """Keyword Graph Agent 입력"""
    paper_info: PaperInfo
    user_info: UserInfo
    initial_keyword: List[str]


class KeywordGraphOutput(TypedDict):
    """Keyword Graph Agent 출력 - 키워드 ID와 설명 매핑"""
    subgraph: Subgraph
