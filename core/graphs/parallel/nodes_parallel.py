import json
from core.contracts.concept_expansion import ConceptExpansionInput
from core.graphs.parallel.state_parallel import CreateCurriculumOverallState
from core.llm.solar_pro_2_llm import get_solar_model


from core.agents.curriculum_orchestrator import CurriculumOrchestrator
from core.agents.resource_discovery_agent import ResourceDiscoveryAgent
from core.agents.study_load_estimation_agent import StudyLoadEstimationAgent
from core.agents.curriculum_compose_agent import CurriculumComposeAgent
from core.agents.paper_concept_alignment_agent import PaperConceptAlignmentAgent
from core.agents.concept_expansion_agent import ConceptExpansionAgent
from core.agents.first_node_order_agent import FirstNodeOrderAgent

async def curriculum_orchestrator_node(state: CreateCurriculumOverallState):
    """
    curriculum_orchestrator를 호출하여 curriculum의 상태를 진단하고 다음 task를 결정
    """
    llm = get_solar_model(temperature=0.1) 
    agent = CurriculumOrchestrator(llm)

    # 에이전트 실행 
    result = await agent.run({
        "paper_content": state["paper_content"],
        "curriculum": state["curriculum"],
        "user_info": state["user_info"],
        "is_keyword_sufficient": state.get("is_keyword_sufficient", True),
        "is_resource_sufficient": state.get("is_resource_sufficient", True),
        "current_iteration_count":state.get("current_iteration_count", 0)
    })

    insufficient_ids = result.get("insufficient_resource_ids", [])
    current_curriculum = state.get("curriculum", {})
    nodes = current_curriculum.get("nodes", [])
    resource_reason_map = result.get("resource_reasoning", {})


    updated_nodes = []
    for node in nodes:
        new_node = node.copy() 
        kid = new_node["keyword_id"]
        
        # sufficiency 업데이트
        new_node["is_resource_sufficient"] = (kid not in insufficient_ids)

        # resource_reason 업데이트
        # 사전에 키가 있으면 이유를 넣고, 없으면 None을 넣음
        new_node["resource_reason"] = resource_reason_map.get(kid)
        
        updated_nodes.append(new_node)

    # 새로운 curriculum 객체 생성
    updated_curriculum = {
        **current_curriculum,
        "nodes": updated_nodes
    }

    current_count = state.get("current_iteration_count", 0)


    # state 업데이트
    return {
        "curriculum": updated_curriculum,

        "tasks": result.get("tasks", []),
        "is_keyword_sufficient": result.get("is_keyword_sufficient", True),
        "is_resource_sufficient": result.get("is_resource_sufficient", True),
        
        # 상세 id 정보
        "insufficient_resource_ids": result.get("insufficient_resource_ids", []),
        "needs_description_ids": result.get("needs_description_ids", []),
        "missing_concepts": result.get("missing_concepts", []),

        "keyword_expand_reason":result.get('keyword_reasoning',"None"),
        "resource_reasoning":result.get('resource_reasoning',"None"),
        "current_iteration_count": current_count + 1
    }

async def resource_discovery_agent_node(state: CreateCurriculumOverallState):
    """
    Resource Discovery Agent를 호출하여 웹 서치를 통해 자료를 탐색하고 자료를 평가
    """

    llm_for_search = get_solar_model(temperature=0.7, reasoning_effort='low')
    llm_for_eval = get_solar_model(temperature=0.1)

    agent = ResourceDiscoveryAgent(
        llm_discovery=llm_for_search, 
        llm_estimation=llm_for_eval
    )

    estimation_agent = StudyLoadEstimationAgent(llm=llm_for_eval)

    curriculum = state.get("curriculum", {})
    nodes_list = curriculum.get("nodes", [])
    user_info = state.get("user_info", {})

    # 에이전트 실행 
    try:
        result = await agent.run({
            "paper_name":curriculum["graph_meta"]["title"],
            "nodes": nodes_list,
            "user_level": user_info.get("level"),
            "purpose": user_info.get("purpose"),
            "pref_types": user_info.get("resource_type_preference", [])
        })
    except Exception as e:
        print(e)
        result = {}

    new_resources = result.get("evaluated_resources", [])
    resources_to_estimate = []

    current_count = state.get("current_iteration_count", 0)
    if current_count <= 2:
        estimation_inputs = []   # Agent에게 보낼 입력용
        resources_to_update = [] # 실제 업데이트할 원본 객체 참조
        
        for node in nodes_list:
            node_keyword = node.get("keyword", "")
            existing_res = node.get("resources", [])
            
            for res in existing_res:
                # 평가가 필요한지 검사 
                if (res.get("difficulty") is None or 
                    res.get("importance") is None or 
                    res.get("study_load") is None):
                    
                    temp_input = res.copy()
                    
                    temp_input["keyword"] = node_keyword
                    # resource_description을 raw_content로 매핑하여 에이전트가 읽을 수 있게 함
                    temp_input["raw_content"] = res.get("resource_description", "")
                    
                    estimation_inputs.append(temp_input)
                    resources_to_update.append(res) # 원본은 여기에 따로 저장

        # 에이전트 실행 및 결과 반영
        if estimation_inputs:
            print(f"🔄 Re-estimating {len(estimation_inputs)} resources...")
        
            estimation_input_data = {
                "resources": estimation_inputs, # 복사본 전달
                "user_level": user_info.get("level"),
                "purpose": user_info.get("purpose")
            }

            # 에이전트 실행
            try:
                estimation_result = await estimation_agent.run(estimation_input_data)
            except Exception as e:
                print(e)
                estimation_result = {}

            evaluated_updates = estimation_result.get("evaluated_resources", [])

            # 결과 반영 (원본 리스트 + 결과 리스트)
            if len(resources_to_update) == len(evaluated_updates):
                for original, updated in zip(resources_to_update, evaluated_updates):
                    
                    # Pydantic 모델인 경우 딕셔너리로 변환
                    if hasattr(updated, 'dict'):
                        updated_dict = updated.dict()
                    else:
                        updated_dict = updated

                    if "difficulty" in updated_dict:
                        original["difficulty"] = updated_dict["difficulty"]
                    if "importance" in updated_dict:
                        original["importance"] = updated_dict["importance"]
                    if "study_load" in updated_dict:
                        original["study_load"] = updated_dict["study_load"]
                    if "type" in updated_dict:
                        original["type"] = updated_dict["type"]
            else:
                print("⚠️ Warning: Estimation count mismatch. Updates might be inaccurate.")

    resource_map = {}
    all_current_res_count = sum(len(n.get("resources", [])) for n in nodes_list)

    for i, res in enumerate(new_resources):
        kid = res["keyword_id"]
        if kid not in resource_map:
            resource_map[kid] = []
        
        def get_value(data, key, default):
            val = data.get(key)
            return val if val is not None else default

        res_id_num = all_current_res_count + i + 1
        
        try:
            # None이 들어오면 바로 기본값(5)으로 치환 후 변환
            difficulty = int(float(get_value(res, "difficulty", 5)))
            importance = int(float(get_value(res, "importance", 5)))
            study_load = float(get_value(res, "study_load", 1)) 
        except (ValueError, TypeError):
            difficulty, importance, study_load = 5, 5, 1


        formatted_res = {
            "resource_id": f"res-{res_id_num:03d}", # res-001 형태
            "resource_name": res.get("resource_name"),
            "url": res.get("url"),
            "type": res.get("type", "web_doc"),
            "resource_description": res.get("resource_description"),
            "difficulty": difficulty,  
            "importance": importance,  
            "study_load": study_load,
            "is_necessary": None                    
        }
        resource_map[kid].append(formatted_res)

    updated_nodes = []
    for node in nodes_list:
        new_node = node.copy()
        kid = node["keyword_id"]
        
        if kid in resource_map:
            # 기존 리소스 유지 + 새 리소스 추가
            current_res = new_node.get("resources", [])
            new_node["resources"] = current_res + resource_map[kid]

        updated_nodes.append(new_node)
    

    # state 업데이트
    return {
        "curriculum": {"nodes":updated_nodes},
        "insufficient_resource_ids": []
    }

async def curriculum_compose_node(state: CreateCurriculumOverallState):
    """
    Curriculum Compose Agent를 호출하여 커리큘럼 리소스를 최적화(삭제/보존/강조)
    """
    llm = get_solar_model(temperature=0.1)
    agent = CurriculumComposeAgent(llm)

    curriculum = state.get("curriculum", {})
    user_info = state.get("user_info", {})

    agent_input = {
        "user_info": user_info,
        "curriculum": curriculum
    }

    result = await agent.run(agent_input)
    new_curriculum = result.get("curriculum", curriculum)

    return {
        "final_curriculum": new_curriculum
    }

async def concept_expansion_node(state: CreateCurriculumOverallState):
    """
    Concept Expansion Agent를 호출하여 추가 키워드를 생성 및 연결
    """
    llm = get_solar_model(model_name="solar-pro2", temperature=0.5)
    
    agent = ConceptExpansionAgent(llm)
    
    input: ConceptExpansionInput = {
        "curriculum": state["curriculum"],
        "keyword_expand_reason": state["keyword_expand_reason"],
        "missing_concepts": state["missing_concepts"],
        "user_info" : state["user_info"]
    }
    
    try:
        result = await agent.run(input)
    except Exception as e:
        print(e)
        result = {
            'curriculum': state['curriculum']
        }

    updated_full_curriculum = result["curriculum"]
    
    existing_node_ids = {n["keyword_id"] for n in state["curriculum"].get("nodes", [])}
    new_nodes = [n for n in updated_full_curriculum.get("nodes", []) 
                 if n["keyword_id"] not in existing_node_ids]
    
    # 엣지도 새로운 연결만 추출 (ID 조합 등으로 체크)
    existing_edge_keys = {f"{e['start']}->{e['end']}" for e in state["curriculum"].get("edges", [])}
    new_edges = [e for e in updated_full_curriculum.get("edges", []) 
                 if f"{e['start']}->{e['end']}" not in existing_edge_keys]
    
    return {
        "curriculum": {"nodes": new_nodes, "edges": new_edges}
    }

async def paper_concept_alignment_node(state: CreateCurriculumOverallState):
    """
    Paper Concept Alignment Agent를 호출하여 노드별 설명(description)을 생성 및 보강
    """
    llm = get_solar_model(temperature=0.1)
    agent = PaperConceptAlignmentAgent(llm)

    curriculum = state.get("curriculum", {})
    paper_info = state.get("paper_content", {})

    agent_input = {
        "paper_info": paper_info,
        "curriculum": curriculum
    }

    try:
        result = await agent.run(agent_input)
    except Exception as e:
        print(e)
        result = {}
    response = result.get("response", {})

    # 커리큘럼 노드에 설명 업데이트
    current_nodes = curriculum.get("nodes", [])
    updated_nodes = []
    
    for node in current_nodes:
        new_node = node.copy()
        kw_id = new_node.get("keyword_id")
        
        # 새로 생성된 설명이 있으면 업데이트
        if kw_id in response:
            new_node["description"] = response[kw_id].get("description", "")
            new_node["keyword_importance"] = response[kw_id].get("importance")
            
        updated_nodes.append(new_node)
    

    return {
        "curriculum": {"nodes": updated_nodes},
        "needs_description_ids": [],
    }


async def first_node_order_node(state: CreateCurriculumOverallState):
    """
    First Node Order Agent를 호출하여 시작 노드의 순서를 결정
    """
    llm = get_solar_model(temperature=0.1)
    agent = FirstNodeOrderAgent(llm)

    curriculum = state.get("final_curriculum", {})
    paper_info = state.get("paper_content", {})
    user_info = state.get("user_info", {})

    agent_input = {
        "paper_content": paper_info,
        "curriculum": curriculum,
        "user_info":user_info
    }

    result = await agent.run(agent_input)

    new_order = result["curriculum"].get("first_node_order", [])

    curriculum["first_node_order"] = new_order


    return {
        "final_curriculum": curriculum
    }
