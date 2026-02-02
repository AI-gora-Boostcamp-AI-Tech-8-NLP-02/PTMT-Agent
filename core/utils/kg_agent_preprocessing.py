# core/utils/kg_agent_preprocessing.py 

from __future__ import annotations

from collections import defaultdict, deque


def extract_target_paper(raw_subgraph):
    """
    raw_subgraph에서 target_paper 정보를 agent 입력용으로 변환
    Output: { "title": ..., "id": ..., "describe": ... }
    """
    graph = raw_subgraph.get("graph", raw_subgraph)
    tp = graph.get("target_paper", {}) or {}

    title = tp.get("name", "") or ""
    pid = tp.get("id", "") or ""
    describe = tp.get("description", "") or ""

    return {"title": title, "id": pid, "describe": describe}


def build_keyword_maps(raw_subgraph):
    """
    keyword_id -> keyword_name, keyword_name -> keyword_id 맵 생성
    """
    graph = raw_subgraph.get("graph", raw_subgraph)
    nodes = graph.get("nodes", {}) or {}
    keywords = nodes.get("keywords", []) or []

    id_to_name = {}
    name_to_id = {}

    for kw in keywords:
        kid = kw.get("id")
        name = kw.get("name")
        if isinstance(kid, str) and kid and isinstance(name, str) and name:
            id_to_name[kid] = name
            # name 중복이면 처음 꺼 유지
            if name not in name_to_id:
                name_to_id[name] = kid

    return id_to_name, name_to_id


def get_paper_id_set(raw_subgraph):
    """
    nodes.papers에 포함된 모든 paper id 집합
    """
    graph = raw_subgraph.get("graph", raw_subgraph)
    nodes = graph.get("nodes", {}) or {}
    papers = nodes.get("papers", []) or []

    out = set()
    for p in papers:
        pid = p.get("id")
        if isinstance(pid, str) and pid:
            out.add(pid)
    return out


def flatten_edges(raw_subgraph):
    """
    edges dict(PREREQ/ABOUT/IN/REF_BY/...)을 하나의 리스트로 평탄화
    각 원소는 {type, source, target, reason, strength} 형태
    reason 필드는 없을 수도 있으니 ""로 보정
    """
    graph = raw_subgraph.get("graph", raw_subgraph)
    edges_obj = graph.get("edges", {}) or {}

    flat = []
    for etype, elist in edges_obj.items():
        if not isinstance(elist, list):
            continue
        for e in elist:
            if not isinstance(e, dict):
                continue
            source = e.get("source")
            target = e.get("target")
            if not (isinstance(source, str) and isinstance(target, str) and source and target):
                continue

            strength_raw = e.get("strength", 0)
            try:
                strength = float(strength_raw)
            except Exception:
                strength = 0.0

            reason = e.get("reason", "")
            if not isinstance(reason, str):
                reason = ""

            flat.append(
                {
                    "type": str(etype),
                    "source": source,
                    "target": target,
                    "reason": reason,
                    "strength": strength,
                    # REF_BY 등에서 intents/isInfluential 같은 부가 필드가 있어도
                    # 전처리 단계에서는 일단 무시.
                }
            )

    return flat


## 타겟 paper가 아닌 paper들은 삭제
def remove_non_target_papers_and_edges(flat_edges, paper_ids, target_paper_id, keyword_id_to_name):
    """
    - target_paper를 제외한 paper 노드들과 연결된 edge 제거
    - agent 입력에는 paper를 넣지 않으므로, paper가 source/target인 edge 전부 제거
    - keyword<->keyword edge만 남긴다.
    """
    non_target_paper_ids = {pid for pid in paper_ids if pid and pid != target_paper_id}
    cleaned = []
    for e in flat_edges:
        s = e["source"]
        t = e["target"]

        # target 제외 paper와 연결된 edge 제거
        if s in non_target_paper_ids or t in non_target_paper_ids:
            continue
        # paper가 끼면 제거 (target paper 포함)
        if s in paper_ids or t in paper_ids:
            continue
        # keyword id가 아닌 노드는 제거
        if s not in keyword_id_to_name or t not in keyword_id_to_name:
            continue

        cleaned.append(e)

    return cleaned


## 순환 엣지 삭제를 위한 함수
def compute_keyword_distance_to_target(raw_subgraph, keyword_id_to_name, target_paper_id, keyword_keyword_edges):
    """
    strength 동률일 때 방향 결정을 위해 "target paper와 가까움" 거리를 계산

    거리 seed:
    - raw_subgraph의 edge 중 target_paper_id와 keyword를 연결하는 edge에서 keyword를 seed로 삼는다.
      (예: source=target_paper_id, target=kw_id 또는 반대)

    그래프:
    - keyword<->keyword 엣지를 무방향으로 보고 BFS
    """
    # 1) seed keywords from raw edges that touch target paper
    raw_flat = flatten_edges(raw_subgraph)

    seeds = set()
    for e in raw_flat:
        s = e["source"]
        t = e["target"]
        if s == target_paper_id and t in keyword_id_to_name:
            seeds.add(t)
        elif t == target_paper_id and s in keyword_id_to_name:
            seeds.add(s)

    # seed가 아예 없다면 dist는 비어있고, tie-break는 사전순으로만 감
    if not seeds:
        return {}

    # 2) build undirected adjacency from keyword_keyword_edges
    adj = defaultdict(list)
    for e in keyword_keyword_edges:
        s = e["source"]
        t = e["target"]
        adj[s].append(t)
        adj[t].append(s)

    # 3) BFS
    dist = {}
    q: deque[str] = deque()

    for sid in seeds:
        dist[sid] = 0
        q.append(sid)

    while q:
        u = q.popleft()
        for v in adj.get(u, []):
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)

    return dist


def pick_best_direction_edge(candidates, dist_to_target):
    """
    후보 엣지들 중 하나를 선택
    - strength 최우선
    - strength 동일이면 dist 큰->작 방향 선호
    - tie면 안정적 정렬 기준
    """
    # 1) strength max
    max_strength = max(e.get("strength", 0.0) for e in candidates)
    top = [e for e in candidates if e.get("strength", 0.0) == max_strength]
    if len(top) == 1:
        return top[0]

    # 2) dist 방향 점수: (dist(source) - dist(target))가 클수록 멀->가까움
    # dist 없으면 큰 값으로 두면 불리해질 수 있어서, 여기서는 "None이면 0"으로 두고
    # 대신 tie-break로 안정성 확보
    def dist_score(e) -> int:
        ds = dist_to_target.get(e["source"], 0)
        dt = dist_to_target.get(e["target"], 0)
        return ds - dt

    best_score = max(dist_score(e) for e in top)
    top2 = [e for e in top if dist_score(e) == best_score]
    if len(top2) == 1:
        return top2[0]

    # 3) 안정적인 tie-break: (source,target) 사전순
    top2.sort(key=lambda x: (x["source"], x["target"]))
    return top2[0]


## 순환 엣지 깨기 (A->B and B->A)
def break_bidirectional_edges(edges, dist_to_target):
    """
    동일 type에서 A->B, B->A가 동시에 존재하는 경우 하나를 제거

    규칙:
    1) strength 큰 쪽 유지
    2) strength 동률이면 "타겟에 더 가까운 노드 방향으로 들어오게" 유지
       - dist(source) > dist(target) 인 방향을 선호 (멀->가까움)
       - dist 정보 없으면 tie-break로 안정적인 기준(사전순)
    """
    grouped = defaultdict(list)

    for e in edges:
        a = e["source"]
        b = e["target"]
        et = e["type"]
        # unordered pair key
        if a < b:
            key = (a, b, et)
        else:
            key = (b, a, et)
        grouped[key].append(e)

    kept = []

    for _, elist in grouped.items():
        if len(elist) == 1:
            kept.append(elist[0])
            continue

        # 같은 pair+type에 여러 개가 있으면 (보통 2개)
        # 가장 좋은 1개만 남김
        best = pick_best_direction_edge(elist, dist_to_target)
        kept.append(best)

    return kept


## 에이전트 입력으로 변환
def build_agent_input(keyword_keyword_edges, keyword_id_to_name, target_paper_id):
    """
    agent 입력 형태로 변환:
    {"target_paper_id": "", 
     "nodes": ["kw name", ...],
     "edges": [{"start": "...", "end": "...", "type": "...", "reason": "...", "strength": 0.3}, ...]
    }

    nodes는 edges에 등장한 keyword들만 포함하도록 함(불필요 노드 제거).
    """
    node_name_set = set()
    out_edges = []

    for e in keyword_keyword_edges:
        s_id = e["source"]
        t_id = e["target"]
        s_name = keyword_id_to_name.get(s_id)
        t_name = keyword_id_to_name.get(t_id)
        if not s_name or not t_name:
            continue

        node_name_set.add(s_name)
        node_name_set.add(t_name)

        out_edges.append(
            {
                "start": s_name,
                "end": t_name,
                "type": e["type"],
                "reason": e.get("reason", "") or "",
                "strength": float(e.get("strength", 0.0) or 0.0),
            }
        )

    nodes = sorted(node_name_set)

    return {
        "target_paper_id": target_paper_id,
        "nodes": nodes,
        "edges": out_edges,
    }


## 전체 preprocess
def preprocess_graph(raw_subgraph):
    """
    입력:
      - raw_subgraph: 1차 subgraph raw JSON
    출력:
      - subgraph (LLM 입력용):
        { "target_paper_id": "...", "nodes": [...], "edges": [...] }

    전처리 단계:
      1) target_paper id 추출
      2) keyword id<->name 맵 구성
      3) paper id set 구성
      4) edge 평탄화
      5) target 제외 paper 및 paper 관련 edge 제거 (keyword-keyword만 유지)
      6) target과의 거리 계산 (seed: target paper와 직접 연결된 keyword)
      7) A<->B 양방향 엣지 제거(규칙 기반)
      8) agent 입력(subgraph) 생성
    """
    target_paper = extract_target_paper(raw_subgraph)
    target_paper_id = target_paper.get("id", "")

    keyword_id_to_name, _ = build_keyword_maps(raw_subgraph)
    paper_ids = get_paper_id_set(raw_subgraph)
    flat_edges = flatten_edges(raw_subgraph)

    keyword_keyword_edges = remove_non_target_papers_and_edges(
        flat_edges=flat_edges,
        paper_ids=paper_ids,
        target_paper_id=target_paper_id,
        keyword_id_to_name=keyword_id_to_name,
    )

    dist_to_target = compute_keyword_distance_to_target(
        raw_subgraph=raw_subgraph,
        keyword_id_to_name=keyword_id_to_name,
        target_paper_id=target_paper_id,
        keyword_keyword_edges=keyword_keyword_edges,
    )

    keyword_keyword_edges = break_bidirectional_edges(
        edges=keyword_keyword_edges,
        dist_to_target=dist_to_target,
    )

    subgraph = build_agent_input(
        keyword_keyword_edges=keyword_keyword_edges,
        keyword_id_to_name=keyword_id_to_name,
        target_paper_id=target_paper_id,
    )

    return subgraph
