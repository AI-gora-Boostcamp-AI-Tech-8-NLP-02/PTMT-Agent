import json
import os

def transform_subgraph_to_final_curriculum(subgraph_data, meta_data):
    """
    Subgraph를 최종 Curriculum 포맷으로 변환
    """
    
    paper_id = subgraph_data.get("paper_id", "")
    
    
    # ID 매핑 테이블 생성 & None ID 저장
    id_map = {}
    nodes_with_missing_id = [] 
    
    # Paper ID는 그대로 유지
    if paper_id:
        id_map[paper_id] = paper_id
    
    for idx, node in enumerate(subgraph_data["nodes"]):
        original_id = node.get("keyword_id")
        new_id = f"key-{idx+1:03d}"
        
        # ID 매핑 저장 
        if original_id is not None:
            id_map[original_id] = new_id
            
        if original_id is None or str(original_id).lower() == "none":
            nodes_with_missing_id.append(new_id)

   
    # Nodes 변환
    transformed_nodes = []
    global_resource_counter = 1

    for idx, node in enumerate(subgraph_data["nodes"]):
        new_id = f"key-{idx+1:03d}"
        
        # Resource 변환
        transformed_resources = []
        original_resources = node.get("resources", [])
        
        for res in original_resources:
            res_id = f"res-{global_resource_counter:03d}"
            global_resource_counter += 1
            
            new_res = {
                "resource_id": res_id,
                "resource_name": res.get("resource_name", ""),
                "url": res.get("url", ""),
                "type": res.get("type", "web_doc"),
                "resource_description": res.get("abstract", res.get("resource_description", "")),
                "difficulty": 5,
                "importance": 5,
                "study_load": 1.0,
                "is_necessary": None
            }
            transformed_resources.append(new_res)

        # Node 생성
        new_node = {
            "keyword_id": new_id,
            "keyword": node["keyword"],
            "description": None, 
            "keyword_importance": None,
            "is_resource_sufficient": False,
            "resources": transformed_resources
        }
        transformed_nodes.append(new_node)

    
    # Edges 변환 (None이었던 노드 연결 추가)
    transformed_edges = []
    
    # 기존 엣지 변환
    for edge in subgraph_data["edges"]:
        start_id = edge["start"]
        end_id = edge["end"]
        
        new_start = id_map.get(start_id, start_id)
        new_end = id_map.get(end_id, end_id)
        
        new_edge = {
            "start": new_start,
            "end": new_end
        }
        transformed_edges.append(new_edge)

    #  ID가 'none'이었던 노드들을 Paper와 연결
    if paper_id:
        for missing_node_new_id in nodes_with_missing_id:
            new_edge = {
                "start": missing_node_new_id,
                "end": paper_id
            }
            transformed_edges.append(new_edge)

    curriculum = {
        "graph_meta": meta_data,
        "nodes": transformed_nodes,
        "edges": transformed_edges
    }
    
    return curriculum

# ==========================================
# 테스트 실행
# ==========================================

if __name__ == "__main__":



    current_dir = os.path.dirname(os.path.abspath(__file__))
    subgraph_path = os.path.join(current_dir, "../../dummy_data/dummy_subgraph.json")
    
    # 데이터 로드
    try:
        with open(subgraph_path, "r", encoding="utf-8") as f:
            dummy_subgraph = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ 파일을 찾을 수 없습니다: {e}")


    meta_data_input = {
        "paper_id": "123456",
        "title" : "Attention Is All You Need",
        "summarize": "이 논문은 기존의 RNN이나 CNN을 완전히 배제하고 오로지 어텐션(Attention) 메커니즘만으로 구성된 트랜스포머(Transformer) 아키텍처를 제시하며 딥러닝 연구의 새로운 패러다임을 열었습니다. 연산의 병렬화를 통해 학습 속도를 비약적으로 높였을 뿐만 아니라, 기존 모델들의 고질적인 문제였던 장거리 의존성 문제를 해결함으로써 현재 GPT와 같은 초거대 언어 모델들이 탄생할 수 있는 결정적인 토대를 마련했습니다."
    }

    # 함수 실행
    result_json = transform_subgraph_to_final_curriculum(dummy_subgraph, meta_data_input)

    # 결과 출력
    print("=== 변환 결과 ===")
    with open("sub_to_curr.json", "w", encoding="utf-8") as f:
        json.dump(result_json, f, indent=2, ensure_ascii=False)
    print("\n✅ '저장 완료.")
