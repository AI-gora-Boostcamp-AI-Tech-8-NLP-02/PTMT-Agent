# core/tools/gdb_search.py

import os
import pandas as pd
from neo4j import GraphDatabase
import json
import logging

from dotenv import load_dotenv

logging.getLogger("neo4j").setLevel(logging.WARNING)

# Wait 60 seconds before connecting using these details, or login to https://console.neo4j.io to validate the Aura Instance is available
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI") 
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME") 
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD") 
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE") 
AURA_INSTANCEID = os.getenv("AURA_INSTANCEID") 
AURA_INSTANCENAME = os.getenv("AURA_INSTANCENAME") 

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def close_driver():
    driver.close()

print(driver.get_server_info())

def run_cypher(query: str, params: dict | None = None, limit: int = 10):
    params = params or {}
    with driver.session() as session:
        result = session.run(query, params)
        rows = [r.data() for r in result]
    return rows[:limit]


prereq_depth = 2  # depth 직접 박기: *1..2
ref_limit = 5
kw_paper_limit = 3

min_prereq_strength = 0.9
min_kw_strength = 0.0
min_ref_strength = 0.5

def get_subgraph_1(paper_name, initial_keywords): 

    prereq_depth = 2  # depth 직접 박기: *1..2
    ref_limit = 5
    kw_paper_limit = 3

    min_prereq_strength = 0.9
    min_kw_strength = 0.0
    min_ref_strength = 0.5

    q = """
    WITH 1 AS _
    OPTIONAL MATCH (p:Paper {name:$paper_name})

    /* 1) target paper와 직접 연결된 kc (ABOUT/IN) */
    OPTIONAL MATCH (p)-[pk:ABOUT|IN]-(k_paper:Keyword)
    WHERE pk.strength IS NULL OR pk.strength >= $min_kw_strength
    WITH p,
        [x IN collect(DISTINCT CASE
                WHEN k_paper IS NULL THEN NULL
                ELSE {k:k_paper, r:pk}
                END)
        WHERE x IS NOT NULL] AS paper_kw_links,
        $min_prereq_strength AS min_pr,
        $min_kw_strength     AS min_kw,
        $min_ref_strength    AS min_ref,
        $kw_paper_limit      AS kw_lim,
        $ref_limit           AS ref_lim,
        [c IN $initial_keywords | toLower(c)] AS cs

    /* 2) target paper의 직접 kc들의 선수개념(PREREQ) 확장 (depth 직접 박기: *1..2) */
    CALL (paper_kw_links, min_pr) {
    UNWIND paper_kw_links AS lk
    WITH lk.k AS k0, min_pr
    OPTIONAL MATCH path1 = (kpre:Keyword)-[pr:PREREQ*1..2]->(k0)
    WHERE ALL(x IN relationships(path1)
                WHERE x.strength IS NULL OR x.strength >= min_pr)
    RETURN collect(DISTINCT path1) AS paper_kw_prereq_paths
    }
    WITH p, paper_kw_links, paper_kw_prereq_paths, cs, min_pr, min_kw, min_ref, kw_lim, ref_lim

    /* 3) agent initial_keywords로 매칭된 seed kc */
    OPTIONAL MATCH (k_seed:Keyword)
    WHERE toLower(k_seed.name) IN cs
    OR ANY(a IN coalesce(k_seed.alias, []) WHERE toLower(a) IN cs)
    WITH p, paper_kw_links, paper_kw_prereq_paths,
        collect(DISTINCT k_seed) AS seeds,
        min_pr, min_kw, min_ref, kw_lim, ref_lim

    /* 4) seed 주변 prereq (depth 직접 박기: *1..2) */
    CALL (seeds, min_pr) {
    UNWIND (CASE WHEN size(seeds)=0 THEN [NULL] ELSE seeds END) AS s
    WITH s, min_pr
    OPTIONAL MATCH path2 = (kpre2:Keyword)-[pr2:PREREQ*1..2]->(s)
    WHERE s IS NOT NULL
        AND ALL(x IN relationships(path2)
                WHERE x.strength IS NULL OR x.strength >= min_pr)
    RETURN collect(DISTINCT path2) AS prereq_paths
    }
    WITH p, paper_kw_links, paper_kw_prereq_paths, seeds, prereq_paths,
        min_kw, min_ref, kw_lim, ref_lim

    /* 5) seed를 ABOUT한 논문들 (+ limit) */
    CALL (seeds, min_kw, kw_lim) {
    UNWIND (CASE WHEN size(seeds)=0 THEN [NULL] ELSE seeds END) AS s2
    WITH s2, min_kw, kw_lim
    OPTIONAL MATCH (p_about:Paper)-[ab:ABOUT]->(s2)
    WHERE s2 IS NOT NULL
        AND (ab.strength IS NULL OR ab.strength >= min_kw)
    WITH collect(DISTINCT CASE
        WHEN p_about IS NULL THEN NULL
        ELSE {p:p_about, r:ab, k:s2}
        END) AS xs, kw_lim
    RETURN [x IN xs WHERE x IS NOT NULL][0..kw_lim] AS seed_about_links
    }
    WITH p, paper_kw_links, paper_kw_prereq_paths, seeds, prereq_paths, seed_about_links,
        min_ref, ref_lim

    /* 6) target paper ref (p가 null이면 빈 배열) */
    CALL (p, min_ref, ref_lim) {
    OPTIONAL MATCH (ref:Paper)-[rr:REF_BY]->(p)
    WHERE rr.strength IS NULL OR rr.strength >= min_ref
    WITH collect(DISTINCT CASE
        WHEN ref IS NULL THEN NULL
        ELSE {p:ref, r:rr}
        END) AS xs, ref_lim
    RETURN [x IN xs WHERE x IS NOT NULL][0..ref_lim] AS ref_links
    }

    /*-- 정리 파트-- */

    /* paths에서 노드/관계 추출 (+ PREREQ는 dist(먼 정도)도 함께 저장) */
    WITH
    p, paper_kw_links, seeds, seed_about_links, ref_links,
    paper_kw_prereq_paths, prereq_paths,

    /* path 노드 */
    reduce(acc = [], pa IN paper_kw_prereq_paths | acc + nodes(pa)) +
    reduce(acc = [], pa IN prereq_paths         | acc + nodes(pa)) AS kc_nodes_from_paths,

    /* PREREQ 관계를 (r, dist)로 풀어 저장
        dist = size(rels) - index (끝 노드에 가까울수록 dist가 작음, 멀수록 큼) */
    reduce(acc = [], pa IN paper_kw_prereq_paths |
        acc + [i IN range(0, size(relationships(pa))-1) |
        { r: relationships(pa)[i], dist: size(relationships(pa)) - i }
        ]
    ) +
    reduce(acc = [], pa IN prereq_paths |
        acc + [i IN range(0, size(relationships(pa))-1) |
        { r: relationships(pa)[i], dist: size(relationships(pa)) - i }
        ]
    ) AS prereq_rel_rows

    WITH
    p, paper_kw_links, seeds, seed_about_links, ref_links,
    [k IN kc_nodes_from_paths WHERE k:Keyword] AS kc_nodes_from_paths,
    [x IN prereq_rel_rows WHERE x.r IS NOT NULL AND type(x.r) = 'PREREQ'] AS prereq_rel_rows

    /* raw paper/kc 리스트 만들기 (null 제거 포함) */
    WITH
    p, paper_kw_links, seed_about_links, ref_links, prereq_rel_rows,
    [sl IN seed_about_links | sl.p] AS about_papers_raw,
    [rl IN ref_links       | rl.p] AS ref_papers_raw,
    [lk IN paper_kw_links  | lk.k] AS paper_kcs_raw,
    seeds,
    kc_nodes_from_paths

    WITH
    p, paper_kw_links, seed_about_links, ref_links, prereq_rel_rows,

    /* paper raw */
    [x IN about_papers_raw WHERE x IS NOT NULL] +
    [y IN ref_papers_raw   WHERE y IS NOT NULL] AS paper_nodes_raw,

    /* kc raw */
    [a IN paper_kcs_raw WHERE a IS NOT NULL] +
    [s IN seeds         WHERE s IS NOT NULL] +
    [k IN kc_nodes_from_paths WHERE k IS NOT NULL] AS kc_nodes_raw

    /* 노드 dedup: “UNWIND + DISTINCT(elementId)” */
    CALL (paper_nodes_raw) {
    UNWIND paper_nodes_raw AS n
    WITH DISTINCT elementId(n) AS id, n
    RETURN collect({ id:id, name:n.name, description:n.description }) AS paper_nodes
    }

    CALL (kc_nodes_raw) {
    UNWIND kc_nodes_raw AS k
    WITH DISTINCT elementId(k) AS id, k
    RETURN collect({ id:id, name:k.name, categories:k.categories, link:k.link }) AS kc_nodes
    }

    /*-- 엣지 dedup + 분리-- */
    WITH
    p, paper_nodes, kc_nodes,
    paper_kw_links, seed_about_links, ref_links, prereq_rel_rows

    /* 1) kc-kc(PREREQ): (source,target) 기준
        strength desc, 동률이면 dist desc (먼 것이 우선) */
    CALL (prereq_rel_rows) {
    UNWIND prereq_rel_rows AS x
    WITH x.r AS r, x.dist AS dist
    WITH elementId(startNode(r)) AS s,
        elementId(endNode(r))   AS t,
        r, dist,
        coalesce(r.strength, 0.0) AS str
    ORDER BY s, t, str DESC, dist DESC
    WITH s, t, collect({r:r, dist:dist, str:str})[0] AS best
    RETURN collect({
        source: s, target: t,
        strength: best.r.strength,
        reason: best.r.reason
    }) AS kc_kc_edges
    }

    /* 2) paper-kc 관계를 type별로 분리해서 dedup
        dedup 키: (source,target,type)
        규칙: strength desc (동률이면 임의지만, 같은 type이므로 우선순위 불필요)
    */
    CALL (paper_kw_links, seed_about_links) {
    WITH [lk IN paper_kw_links   | lk.r] +
        [sl IN seed_about_links | sl.r] AS rels
    UNWIND rels AS r
    WITH r WHERE r IS NOT NULL AND type(r) IN ['ABOUT','IN']
    WITH elementId(startNode(r)) AS s,
        elementId(endNode(r))   AS t,
        type(r)                 AS ty,
        r,
        coalesce(r.strength, 0.0) AS str
    ORDER BY s, t, ty, str DESC
    WITH s, t, ty, collect(r)[0] AS best
    RETURN
        collect(CASE WHEN ty = 'ABOUT' THEN {
        source: s, target: t, strength: best.strength, reason: best.reason
        } END) AS about_edges_raw,
        collect(CASE WHEN ty = 'IN' THEN {
        source: s, target: t, strength: best.strength, reason: best.reason
        } END) AS in_edges_raw
    }

    /* null 제거 */
    WITH
    p, paper_nodes, kc_nodes, kc_kc_edges, ref_links,
    [e IN about_edges_raw WHERE e IS NOT NULL] AS about_edges,
    [e IN in_edges_raw    WHERE e IS NOT NULL] AS in_edges

    /* 3) paper-paper(REF_BY): (source,target) 기준, strength desc */
    CALL (ref_links) {
    WITH [rl IN ref_links | rl.r] AS rels
    UNWIND rels AS r
    WITH r WHERE r IS NOT NULL
    WITH elementId(startNode(r)) AS s,
        elementId(endNode(r))   AS t,
        r,
        coalesce(r.strength, 0.0) AS str
    ORDER BY s, t, str DESC
    WITH s, t, collect(r)[0] AS best
    RETURN collect({
        source: s, target: t,
        intents: best.intents,
        isInfluential: best.isInfluential,
        strength: best.strength
    }) AS paper_paper_edges
    }

    RETURN {
    target_paper: CASE
        WHEN p IS NULL THEN NULL
        ELSE {
        id: elementId(p),
        name: p.name,
        abstract: p.abstract,
        description: p.description,
        citationCount: p.citationCount
        }
    END,
    nodes: {
        papers: paper_nodes,
        keywords: kc_nodes
    },
    edges: {
        PREREQ: kc_kc_edges,
        ABOUT: about_edges,
        IN: in_edges,
        REF_BY: paper_paper_edges
    }
    } AS graph
    """

    res = run_cypher(q, {
        "paper_name": paper_name,
        "initial_keywords": initial_keywords,
        "min_prereq_strength": min_prereq_strength,
        "min_kw_strength": min_kw_strength,
        "min_ref_strength": min_ref_strength,
        "ref_limit": ref_limit,
        "kw_paper_limit": kw_paper_limit,
    })

    if not res: # 아예 없으면..
        return {
            "graph": {
                "target_paper": None,
                "nodes": {"papers": [], "keywords": []},
                "edges": {"PREREQ": [], "ABOUT": [], "IN": [], "REF_BY": []},
            }
        }
    return res[0]
