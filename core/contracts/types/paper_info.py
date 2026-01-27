from typing import List, TypedDict

class PaperBodySection(TypedDict):
    """논문 본문 섹션"""
    subtitle: str
    text: str

class PaperInfo(TypedDict):
    """논문 정보"""
    title: str
    author: List[str]
    abstract: str
    body: List[PaperBodySection]