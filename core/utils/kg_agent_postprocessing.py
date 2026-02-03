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

    # 2. nodes 생성
    nodes = []
    for keyword_name in selected_keyword_names:
        if keyword_name.lower() not in keyword_name_to_property:
            raise KeyError(f"{keyword_name} not found in GraphDB data")
        
        keyword_property = keyword_name_to_property[keyword_name.lower()]
        keyword_id = keyword_property['id']

        # 2-1. 해당 keyword_id와 연결된 paper_id를 찾아 resource로 구성
        resources = []
        for paper_id in keyword_to_paper.get(keyword_id, []):
            paper_property = paper_id_to_property[paper_id]
            resources.append({
                "resource_id": paper_property['id'],
                'resource_name': paper_property['name'],
                'url': paper_property['url'],
                'type': 'paper',
                'description': paper_property['description']
            })

        nodes.append({
            "keyword_id": keyword_id,
            "keyword": keyword_name,
            "resources": resources
        })

    # 3. edges 생성
    edges = []
    for agent_edge in agent_output['edges']:
        start_name = agent_edge['start']
        end_name = agent_edge['end']
        type = agent_edge['type']

        if type == 'PREREQ':
            edges.append({
                'start': keyword_name_to_property[start_name.lower()]['id'],
                'end': keyword_name_to_property[end_name.lower()]['id'],
                'type': type,
                'reason': agent_edge['reason'],
                'strength': agent_edge['strength']
            })
        elif type == "ABOUT":
            edges.append({
                'start': target_paper_id,
                'end': keyword_name_to_property[end_name.lower()]['id'],
                'type': type,
                'reason': agent_edge['reason'],
                'strength': agent_edge['strength']
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


    return {
        "paper_id": target_paper_id,
        "nodes": nodes,
        "edges": edges
    }