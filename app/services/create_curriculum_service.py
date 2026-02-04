from datetime import datetime, timezone
from typing import List
import os
import aiohttp
import asyncio
import json
from dotenv import load_dotenv

load_dotenv()

from app.models.curriculum import (
    CurriculumGenerateRequest,
    CurriculumGenerateResponse
)
from app.models.graph import Graph, GraphNode, GraphEdge
import uuid

# Core Imports
from core.agents.keyword_graph_agent import KeywordGraphAgent
from core.llm.solar_pro_2_llm import get_solar_model
from core.graphs.parallel.graph_parallel import create_initial_state, run_langgraph_workflow
from core.contracts.keywordgraph import KeywordGraphInput

async def generate_curriculum(request: CurriculumGenerateRequest) -> CurriculumGenerateResponse:
    """
    커리큘럼 생성 서비스 (스텁)
    
    실제 구현은 나중에 services 디렉토리에 추가될 예정입니다.
    현재는 mock 그래프를 반환합니다.
    """

    # Mock 데이터 반환
    asyncio.create_task(_generate_curriculum_graph(request))
    return CurriculumGenerateResponse(success=True)


async def _generate_curriculum_graph(request: CurriculumGenerateRequest):
    """
    커리큘럼 그래프 생성 (Background Task)
    1. KeywordGraphAgent를 통해 초기 Subgraph 생성
    2. LangGraph 워크플로우를 실행하여 커리큘럼 완성
    3. 결과 JSON을 메인 백엔드 서버로 POST 전송
    """
    try:
        author_data = request.paper_content.author
        if isinstance(author_data, str):
            author_list = [author_data]
        elif author_data is None:
            author_list = []
        else:
            author_list = author_data # 이미 리스트

        paper_info = {
            "title": request.paper_content.title,
            "author": author_list,
            "abstract": request.paper_content.abstract,
            "body": [part.model_dump() for part in request.paper_content.body]
        }
        
        # User Info 변환
        user_info = request.user_traits.model_dump(by_alias=True)
        
        # 1. KeywordGraphAgent 실행 -> Subgraph 생성
        llm = get_solar_model()
        keyword_agent = KeywordGraphAgent(llm=llm)
        
        # KeywordGraphInput 구성
        initial_keywords = request.initial_keyword
        
        keyword_input = {
            "paper_id": request.paper_id,
            "paper_info": paper_info,
            "user_info": user_info,
            "initial_keyword": initial_keywords
        }

        # Subgraph 생성 
        keyword_result = await keyword_agent.run(KeywordGraphInput(**keyword_input))
        subgraph = keyword_result.get("subgraph")
        
        if not subgraph:
            print("❌ Subgraph 생성 실패")
            return

        paper_meta_data = {
            "paper_id": request.paper_id,
            "title": request.paper_title,
            "summarize": request.paper_summary
        }

        # 2. LangGraph 워크플로우 실행
        initial_state = create_initial_state(
            subgraph_data=subgraph,
            user_info_data=user_info,
            paper_raw_data=paper_info,
            paper_meta_data=paper_meta_data,
            initial_keywords=initial_keywords
        )
        
        app_workflow = run_langgraph_workflow()
        
        # 워크플로우 실행
        final_state = await app_workflow.ainvoke(initial_state)
        final_curriculum = final_state.get("final_curriculum")
        
        if not final_curriculum:
            print("❌ 커리큘럼 생성 실패 (LangGraph)")
            return

        # 3. 메인 백엔드로 전송
        backend_url = os.getenv("MAIN_BACKEND_SERVER_PATH")
        if not backend_url:
            print("⚠️ MAIN_BACKEND_SERVER_PATH not set")
            return
            
        target_url = f"{backend_url}/api/curriculums/import"
        print(f"🚀 Sending results to {target_url}...")
        
        # Payload 구성
        # 422 Error Fix: Title must be a string (not None). Ensure fallback.
        graph_title = request.paper_title or request.paper_content.title or "Untitled Curriculum"
        
        payload = {
            "curriculum_id": request.curriculum_id,
            "title": graph_title, 
            "graph": final_curriculum, 
            "created_at": datetime.now(timezone.utc).isoformat()
        }


        # /api/auth/login
        email = os.getenv("MAIN_BACKEND_SERVER_EMAIL", "") 
        password = os.getenv("MAIN_BACKEND_SERVER_PASSWORD", "") 

        login_payload = {
            "email": email,
            "password": password
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f"{backend_url}/api/auth/login", json=login_payload) as resp:
                if resp.status == 200:
                    resp_json = await resp.json()
                    token = resp_json["data"]["access_token"]
                else:
                    print(f"❌ 로그인 실패: {resp.status}, {await resp.text()}")
                    return

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(target_url, json=payload, headers=headers) as resp:
                if resp.status == 201:
                    print("✅ 커리큘럼 전송 성공")
                else:
                    print(f"❌ 전송 실패: {resp.status}, {await resp.text()}")
        # import json
        # save_path = f"curriculum_{request.curriculum_id}.json"
        # with open(save_path, "w", encoding="utf-8") as f:
        #     json.dump(payload, f, ensure_ascii=False, indent=4)
        # print(f"💾 백엔드 미구현으로 인해 JSON 파일로 임시 저장되었습니다: {save_path}")

    except Exception as e:
        print(f"❌ Background Task Error: {e}")

    

    
    
