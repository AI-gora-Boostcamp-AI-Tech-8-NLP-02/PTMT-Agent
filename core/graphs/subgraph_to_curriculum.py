import json
import os

def transform_subgraph_to_final_curriculum(subgraph_data, meta_data):
    """
    Subgraph를 최종 Curriculum 포맷으로 변환
    """

    # print(f"subgraph_data in transform_subgraph_to_final_curriculum: {subgraph_data}")
    # print(f"meta_data in transform_subgraph_to_final_curriculum: {meta_data}")
    
    # meta_data의 paper_id를 canonical(기준)으로 사용
    rdb_paper_id = meta_data.get("paper_id", "") if meta_data else ""
    subgraph_paper_id = subgraph_data.get("paper_id", "")
    
    
    # ID 매핑 테이블 생성 & None ID 저장
    id_map = {}
    nodes_with_missing_id = [] 
    
    # Canonical paper ID 매핑
    if rdb_paper_id:
        id_map[rdb_paper_id] = rdb_paper_id
    
    # subgraph의 paper_id가 다르면 canonical로 치환되도록 매핑 추가
    if subgraph_paper_id and subgraph_paper_id != rdb_paper_id:
        id_map[subgraph_paper_id] = rdb_paper_id
    
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
                "resource_description": res.get("description", res.get("resource_description", "")),
                "difficulty": None,
                "importance": None,
                "study_load": None,
                "is_necessary": None
            }
            transformed_resources.append(new_res)

        # Node 생성
        new_node = {
            "keyword_id": new_id,
            "keyword": node["keyword"],
            "description": None, 
            "keyword_importance": None,
            "is_keyword_necessary": None,
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
    if rdb_paper_id:
        for missing_node_new_id in nodes_with_missing_id:
            new_edge = {
                "start": missing_node_new_id,
                "end": rdb_paper_id
            }
            transformed_edges.append(new_edge)

    curriculum = {
        "graph_meta": meta_data,
        "first_node_order": [],
        "nodes": transformed_nodes,
        "edges": transformed_edges
    }
    
    return curriculum

# ==========================================
# 테스트 실행
# ==========================================

if __name__ == "__main__":



    current_dir = os.path.dirname(os.path.abspath(__file__))
    subgraph_path = os.path.join(current_dir, "../../dummy_data/dummy_BERT_novice.json")
    
    # 데이터 로드
    try:
        with open(subgraph_path, "r", encoding="utf-8") as f:
            dummy_subgraph = json.load(f)
    except FileNotFoundError as e:
        print(f"❌ 파일을 찾을 수 없습니다: {e}")


    meta_data_input = {
        "paper_id": "26c69973-02be-4052-a794-6973546e8baf",
        "title" : "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "summarize": "BERT 논문은 Transformer 기반의 양방향 언어 표현 모델을 제안한다. 기존 단방향 언어 모델의 한계를 극복하기 위해 마스크된 언어 모델(MLM)과 다음 문장 예측(NSP) 과제를 결합한 사전 훈련 방식을 도입한다. MLM은 입력 토큰의 일부를 무작위로 마스킹하고 주변 문맥을 활용해 이를 예측하는 방식으로 양방향 표현을 학습한다. NSP는 문장 쌍 간의 관계를 이해하는 능력을 향상시킨다. BERT는 사전 훈련 후 간단한 출력 계층 추가로 다양한 NLP 작업(질문 답변, 언어 추론 등)에 미세 조정될 수 있으며, 11개의 주요 NLP 작업에서 기존 방법을 크게 능가하는 성능을 달성했다. GLUE, SQuAD, SWAG 벤치마크에서 새로운 성능 기록을 수립했다."
    }

    # 함수 실행
    result_json = transform_subgraph_to_final_curriculum(dummy_subgraph, meta_data_input)

    # 결과 출력
    print("=== 변환 결과 ===")
    with open("dummy_initial_novice.json", "w", encoding="utf-8") as f:
        json.dump(result_json, f, indent=2, ensure_ascii=False)
    print("\n✅ '저장 완료.")
