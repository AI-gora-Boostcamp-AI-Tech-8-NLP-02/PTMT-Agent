"""
Paper-Concept Alignment Agent
LangGraph 기반으로 논문과 키워드 간의 연관성을 분석하는 에이전트

Upstage Solar LLM을 사용하여 각 키워드가 논문 학습 커리큘럼에 
포함된 이유를 설명합니다.
"""
import json
import os
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_upstage import ChatUpstage
from langgraph.graph import END, StateGraph

from core.contracts.paper_alignment import (
    KeywordAlignment,
    PaperConceptAlignmentInput,
    PaperConceptAlignmentOutput,
)
from core.prompts.paper_concept_alignment.v1 import (
    ALIGNMENT_PROMPT_TEMPLATE,
    OUTPUT_FORMAT_INSTRUCTIONS,
    SYSTEM_PROMPT,
    format_keywords_list,
    format_paper_body,
)
from core.llm.solar_pro_2_llm import get_solar_model


# ============== State 정의 ==============

class AlignmentState(TypedDict):
    """LangGraph State"""
    # 입력
    paper_info: Dict[str, Any]
    subgraph: Dict[str, Any]
    
    # 중간 처리
    formatted_prompt: str
    llm_response: str
    
    # 출력
    alignments: Dict[str, str]
    detailed_alignments: List[Dict[str, Any]]
    
    # 메타데이터
    paper_id: str
    paper_title: str
    error: Optional[str]


# ============== 노드 함수들 ==============

def prepare_prompt_node(state: AlignmentState) -> AlignmentState:
    """입력 데이터를 기반으로 프롬프트를 준비하는 노드"""
    try:
        paper_info = state["paper_info"]
        subgraph = state["subgraph"]
        
        # 논문 정보 추출
        paper_title = paper_info.get("title", "제목 없음")
        paper_authors = ", ".join(paper_info.get("author", []))
        paper_abstract = paper_info.get("abstract", "초록 없음")
        paper_body = paper_info.get("body", [])
        
        # 키워드 정보 추출
        nodes = subgraph.get("nodes", [])
        paper_id = subgraph.get("paper_id", "")
        
        # 프롬프트 포맷팅
        formatted_prompt = ALIGNMENT_PROMPT_TEMPLATE.format(
            paper_title=paper_title,
            paper_authors=paper_authors if paper_authors else "저자 정보 없음",
            paper_abstract=paper_abstract,
            paper_body_summary=format_paper_body(paper_body),
            keywords_list=format_keywords_list(nodes),
            format_instructions=OUTPUT_FORMAT_INSTRUCTIONS
        )
        
        return {
            **state,
            "formatted_prompt": formatted_prompt,
            "paper_id": paper_id,
            "paper_title": paper_title,
            "error": None
        }
    except Exception as e:
        return {
            **state,
            "error": f"프롬프트 준비 중 오류 발생: {str(e)}"
        }


def call_llm_node(state: AlignmentState) -> AlignmentState:
    """Upstage Solar LLM을 호출하는 노드"""
    if state.get("error"):
        return state
    
    try:
        llm = get_solar_model(
            model_name="solar-pro2",
            temperature=0.1
        )
        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=state["formatted_prompt"])
        ]
        
        response = llm.invoke(
                messages,    
                config={
                    "max_tokens": 1024,
                    "tags": ["paper-concept-alignment"]
                }
            )
        
        return {
            **state,
            "llm_response": response.content,
            "error": None
        }
    except Exception as e:
        return {
            **state,
            "error": f"LLM 호출 중 오류 발생: {str(e)}"
        }


def parse_response_node(state: AlignmentState) -> AlignmentState:
    """LLM 응답을 파싱하는 노드"""
    if state.get("error"):
        return state
    
    try:
        llm_response = state["llm_response"]
        
        # JSON 블록 추출
        json_str = llm_response
        if "```json" in llm_response:
            json_str = llm_response.split("```json")[1].split("```")[0].strip()
        elif "```" in llm_response:
            json_str = llm_response.split("```")[1].split("```")[0].strip()
        
        # JSON 파싱
        parsed = json.loads(json_str)
        alignments = parsed.get("alignments", {})
        
        # 상세 alignments 생성
        subgraph = state["subgraph"]
        nodes = subgraph.get("nodes", [])
        keyword_map = {
            node.get("keyword_id", node.keyword_id if hasattr(node, "keyword_id") else ""): 
            node.get("keyword", node.keyword if hasattr(node, "keyword") else "")
            for node in nodes
        }
        
        detailed_alignments = []
        for keyword_id, description in alignments.items():
            detailed_alignments.append({
                "keyword_id": keyword_id,
                "keyword": keyword_map.get(keyword_id, ""),
                "description": description,
                "relevance_score": None,
                "evidence_sections": None
            })
        
        return {
            **state,
            "alignments": alignments,
            "detailed_alignments": detailed_alignments,
            "error": None
        }
    except json.JSONDecodeError as e:
        return {
            **state,
            "error": f"JSON 파싱 오류: {str(e)}. 응답: {state.get('llm_response', '')[:200]}"
        }
    except Exception as e:
        return {
            **state,
            "error": f"응답 파싱 중 오류 발생: {str(e)}"
        }


def should_continue(state: AlignmentState) -> str:
    """에러 여부에 따라 다음 노드를 결정"""
    if state.get("error"):
        return "error"
    return "continue"


# ============== 그래프 빌더 ==============

def build_paper_concept_alignment_graph() -> StateGraph:
    """Paper-Concept Alignment Agent 그래프 빌드"""
    
    # StateGraph 생성
    workflow = StateGraph(AlignmentState)
    
    # 노드 추가
    workflow.add_node("prepare_prompt", prepare_prompt_node)
    workflow.add_node("call_llm", call_llm_node)
    workflow.add_node("parse_response", parse_response_node)
    
    # 엣지 추가
    workflow.set_entry_point("prepare_prompt")
    
    workflow.add_conditional_edges(
        "prepare_prompt",
        should_continue,
        {
            "continue": "call_llm",
            "error": END
        }
    )
    
    workflow.add_conditional_edges(
        "call_llm",
        should_continue,
        {
            "continue": "parse_response",
            "error": END
        }
    )
    
    workflow.add_edge("parse_response", END)
    
    return workflow.compile()


# ============== 에이전트 클래스 ==============

class PaperConceptAlignmentAgent:
    """Paper-Concept Alignment Agent 클래스"""
    
    def __init__(self):
        """에이전트 초기화"""
        self.graph = build_paper_concept_alignment_graph()
    
    def run(
        self, 
        paper_info: Dict[str, Any], 
        subgraph: Dict[str, Any]
    ) -> PaperConceptAlignmentOutput:
        """
        에이전트 실행
        
        Args:
            paper_info: 논문 정보 딕셔너리
            subgraph: Subgraph 정보 딕셔너리
            
        Returns:
            PaperConceptAlignmentOutput: 연관성 분석 결과
        """
        # 초기 상태 설정
        initial_state: AlignmentState = {
            "paper_info": paper_info,
            "subgraph": subgraph,
            "formatted_prompt": "",
            "llm_response": "",
            "alignments": {},
            "detailed_alignments": [],
            "paper_id": subgraph.get("paper_id", ""),
            "paper_title": paper_info.get("title", ""),
            "error": None
        }
        
        # 그래프 실행
        final_state = self.graph.invoke(initial_state)
        
        # 에러 확인
        if final_state.get("error"):
            raise RuntimeError(final_state["error"])
        
        # 결과 반환
        detailed = None
        if final_state.get("detailed_alignments"):
            detailed = [
                KeywordAlignment(**item) 
                for item in final_state["detailed_alignments"]
            ]
        
        return PaperConceptAlignmentOutput(
            paper_id=final_state["paper_id"],
            paper_title=final_state["paper_title"],
            alignments=final_state["alignments"],
            detailed_alignments=detailed
        )
    
    async def arun(
        self, 
        paper_info: Dict[str, Any], 
        subgraph: Dict[str, Any]
    ) -> PaperConceptAlignmentOutput:
        """
        에이전트 비동기 실행
        
        Args:
            paper_info: 논문 정보 딕셔너리
            subgraph: Subgraph 정보 딕셔너리
            
        Returns:
            PaperConceptAlignmentOutput: 연관성 분석 결과
        """
        # 초기 상태 설정
        initial_state: AlignmentState = {
            "paper_info": paper_info,
            "subgraph": subgraph,
            "formatted_prompt": "",
            "llm_response": "",
            "alignments": {},
            "detailed_alignments": [],
            "paper_id": subgraph.get("paper_id", ""),
            "paper_title": paper_info.get("title", ""),
            "error": None
        }
        
        # 그래프 비동기 실행
        final_state = await self.graph.ainvoke(initial_state)
        
        # 에러 확인
        if final_state.get("error"):
            raise RuntimeError(final_state["error"])
        
        # 결과 반환
        detailed = None
        if final_state.get("detailed_alignments"):
            detailed = [
                KeywordAlignment(**item) 
                for item in final_state["detailed_alignments"]
            ]
        
        return PaperConceptAlignmentOutput(
            paper_id=final_state["paper_id"],
            paper_title=final_state["paper_title"],
            alignments=final_state["alignments"],
            detailed_alignments=detailed
        )


# ============== 팩토리 함수 ==============

def create_paper_concept_alignment_agent() -> PaperConceptAlignmentAgent:
    """Paper-Concept Alignment Agent 인스턴스 생성"""
    return PaperConceptAlignmentAgent()


# ============== 직접 실행 함수 ==============

def run_paper_concept_alignment(
    input_data: PaperConceptAlignmentInput
) -> PaperConceptAlignmentOutput:
    """
    Paper-Concept Alignment 실행 (간편 함수)
    
    Args:
        input_data: PaperConceptAlignmentInput 객체
        
    Returns:
        PaperConceptAlignmentOutput: 연관성 분석 결과
    """
    agent = create_paper_concept_alignment_agent()
    return agent.run(
        paper_info=input_data.paper_info.model_dump(),
        subgraph=input_data.subgraph.model_dump()
    )


async def arun_paper_concept_alignment(
    input_data: PaperConceptAlignmentInput
) -> PaperConceptAlignmentOutput:
    """
    Paper-Concept Alignment 비동기 실행 (간편 함수)
    
    Args:
        input_data: PaperConceptAlignmentInput 객체
        
    Returns:
        PaperConceptAlignmentOutput: 연관성 분석 결과
    """
    agent = create_paper_concept_alignment_agent()
    return await agent.arun(
        paper_info=input_data.paper_info.model_dump(),
        subgraph=input_data.subgraph.model_dump()
    )
