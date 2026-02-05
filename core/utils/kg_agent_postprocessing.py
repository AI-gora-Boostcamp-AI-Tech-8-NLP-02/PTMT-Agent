from collections import defaultdict

def transform_graph_data(
        raw_data,
        agent_output,
        keyword_name_to_property,
        target_paper_id
    ):
    raw_graph = raw_data['graph']
    selected_keyword_names = set(agent_output['nodes'])

    # Paper ID를 통해 Property를 바로 찾을 수 있게 정의
    paper_id_to_property = {}
    for paper in raw_graph['nodes']['papers']:
        paper_id_to_property[paper['id']] = {
            'id': paper['id'],
            'name': paper['name'],
            'description': paper.get('description', ''),
            'url': paper.get('link', ''),
            'abstract': paper.get('abstract', paper.get('description', ''))
        }
    
    # Target paper 정보도 추가
    paper_id_to_property[target_paper_id] = {
        'id': target_paper_id,
        'name': raw_graph['target_paper']['name'],
        'description':raw_graph['target_paper'].get('description', ''),
        'url': '',  # target paper URL은 별도 처리 필요
        'abstract': raw_graph['target_paper'].get('abstract', '')
    }

    # 1. Keyword-Paper 매핑
    keyword_to_paper = defaultdict(list)
    used_paper = set()
    for edge in raw_graph['edges'].get('ABOUT', []):
        paper_id = edge['source']
        keyword_id = edge['target']

        if paper_id == target_paper_id:
            continue
        keyword_to_paper[keyword_id].append(paper_id)
        used_paper.add(paper_id)

    for edge in raw_graph['edges'].get('IN', []):
        keyword_id = edge['source']
        paper_id = edge['target']

        if paper_id == target_paper_id or paper_id in used_paper:
            continue
        keyword_to_paper[keyword_id].append(paper_id)
        used_paper.add(paper_id)

    # 2. edges 생성
    ## 2-1. 특정 Keyword로 PREREQ 관계로 들어오는 모든 다른 Keyword의 Property 수집
    keyword_income_edge = defaultdict(list)
    for agent_edge in agent_output['edges']:
        start_name = agent_edge['start']
        end_name = agent_edge['end']
        type = agent_edge['type']

        if type == "PREREQ":
            keyword_income_edge[end_name.lower()].append({
                'name': start_name,
                'type': type,
                'reason': agent_edge['reason'],
                'strength': agent_edge['strength']
            })

    ## 2-2. Agent Ouput으로 나온 Edge를 2차 Sub-graph의 Edge로 변형
    edges, about_node = [], []
    for agent_edge in agent_output['edges']:
        start_name = agent_edge['start']
        end_name = agent_edge['end']
        type = agent_edge['type']

        if type == 'PREREQ':
            edges.append({
                'start': keyword_name_to_property[start_name.lower()]['id'],
                'end': keyword_name_to_property[end_name.lower()]['id'] if end_name.lower() in keyword_name_to_property else end_name,
                'type': type,
                'reason': agent_edge['reason'],
                'strength': agent_edge['strength']
            })
        elif type == "ABOUT":
            ## 2-3. ABOUT으로 연결된 Keyword-Paper를 분해
            about_node.append(end_name.lower())

            for income_keyword_property in keyword_income_edge[end_name.lower()]:
                income_keyword_name = income_keyword_property['name']
                edges.append({
                    'start': keyword_name_to_property[income_keyword_name.lower()]['id'],
                    'end': target_paper_id,
                    'type': "IN",
                    'reason': income_keyword_property['reason'],
                    'strength': income_keyword_property['strength']
                })
        elif type == "IN":
            edges.append({
                'start': keyword_name_to_property[start_name.lower()]['id'],
                'end': target_paper_id,
                'type': type,
                'reason': agent_edge['reason'],
                'strength': agent_edge['strength']
            })
        else:
            raise ValueError(f"type {type} is not allowed.")

    # 3. nodes 생성
    nodes = []
    for keyword_name in selected_keyword_names:
        if keyword_name.lower() in about_node:
            continue

        if keyword_name.lower() not in keyword_name_to_property:
            raise KeyError(f"{keyword_name} not found in GraphDB data")
        
        keyword_property = keyword_name_to_property[keyword_name.lower()]
        keyword_id = keyword_property['id']
        
        # 3-1. 해당 keyword_id와 연결된 paper_id를 찾아 resource로 구성
        resources = []
        # for paper_id in keyword_to_paper.get(keyword_id, []):
        #     paper_property = paper_id_to_property[paper_id]
        #     resources.append({
        #         "resource_id": paper_property['id'],
        #         'resource_name': paper_property['name'],
        #         'url': paper_property['url'],
        #         'type': 'paper',
        #         'description': paper_property['description']
        #     })

        nodes.append({
            "keyword_id": keyword_id,
            "keyword": keyword_name,
            "resources": resources
        })

    # 4. 최종적으로 삭제된 Node를 참고하고 있는 Edge 존재시 삭제
    all_node_id = [target_paper_id]
    for node in nodes:
        all_node_id.append(node['keyword_id'])

    for edge in edges:
        start_id = edge['start']
        end_id = edge['end']

        if start_id in all_node_id and end_id in all_node_id:
            continue
        else:
            edges.remove(edge)

    # 5. 고립 노드 제거, Start로 한 번도 되지 않은 키워드 노드 페이퍼와 IN으로 엣지 연결
    all_start_id = []
    all_end_id = []
    for edge in edges:
        all_start_id.append(edge['start'])
        all_end_id.append(edge['end'])

    for node in nodes:
        node_id = node['keyword_id']

        if node_id in all_start_id:
            continue
        elif node_id in all_end_id:
            edges.append({
                'start': node_id,
                'end': target_paper_id,
                'type': "IN",
                'reason': "",
                'strength': ""
            })
        else:
            nodes.remove(node)

    return {
        "paper_id": target_paper_id,
        "nodes": nodes,
        "edges": edges
    }