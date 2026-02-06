# core/utils/resource_ranker.py

from __future__ import annotations
from typing import Any, Dict, List, Tuple


DEFAULT_TOP_N = 3  # 최종으로 반환될 자료 개수: 3개 -> 고정
DEFAULT_MIN_PREF = 1  # 키워드 당 선호자료 필수 개수
PREFERRED_WEIGHT = 1.5  # 선호 자료 가중치


def _safe_int(val: Any, default: int = 3) -> int:
    try:
        return int(float(val))
    except Exception:
        return default


def compute_score(resource: Dict[str, Any], pref_types: List[str] | None) -> Tuple[float, bool]:
    """
    score = quality * (1.5 if preferred else 1.0)
    preferred 기준: resource["type"]가 pref_types에 포함되는지
    """
    pref_set = set(pref_types or [])
    r_type = (resource.get("type") or "").strip()
    is_preferred = r_type in pref_set

    quality = _safe_int(resource.get("quality"), default=3)
    score = float(quality) * (PREFERRED_WEIGHT if is_preferred else 1.0)

    return score, is_preferred


def select_top_resources(
    resources: List[Dict[str, Any]],
    pref_types: List[str] | None,
    top_n: int = DEFAULT_TOP_N,
    min_pref: int = DEFAULT_MIN_PREF,
) -> List[Dict[str, Any]]:
    """
    - resources: 이미 difficulty/importance/quality/study_load/type 등이 채워진 후보 리스트
    - url 기준 중복 제거는 discovery 단계에서 끝났다고 가정 (여기서는 그대로 처리)
    - 반환: 최대 상위 top_n개 (top_n개 넘게 들어오면), min_pref만큼 preferred를 우선 보장

    절차:
    1) 각 resource에 score/is_preferred를 부여
    2) preferred 그룹에서 score desc로 min_pref개 선출
    3) 남은 자리(top_n - selected)만큼 전체에서 score desc로 채움
    """
    if not resources:
        return []

    # score, is_preferred 붙이기
    scored: List[Dict[str, Any]] = []
    for r in resources:
        score, is_pref = compute_score(r, pref_types)
        rr = dict(r)
        rr["score"] = score
        rr["is_preferred"] = is_pref
        scored.append(rr)

    preferred = [r for r in scored if r.get("is_preferred") is True]
    non_preferred = [r for r in scored if r.get("is_preferred") is not True]

    preferred.sort(key=lambda x: x.get("score", 0), reverse=True)
    non_preferred.sort(key=lambda x: x.get("score", 0), reverse=True)

    selected: List[Dict[str, Any]] = []

    # preferred에서 min_pref개 먼저
    if min_pref > 0 and preferred:
        selected.extend(preferred[:min_pref])

    # 남은 후보 자료들 (이미 뽑힌 것 제외)
    selected_urls = {r.get("url") for r in selected if r.get("url")}
    remaining: List[Dict[str, Any]] = []

    # preferred의 나머지 + non_preferred 전체를 합쳐서 점수순으로
    remaining.extend([r for r in preferred[min_pref:] if r.get("url") not in selected_urls])
    remaining.extend([r for r in non_preferred if r.get("url") not in selected_urls])
    remaining.sort(key=lambda x: x.get("score", 0), reverse=True)

    # top_n까지 채우기
    need = max(0, int(top_n) - len(selected))
    if need > 0:
        selected.extend(remaining[:need])

    return selected[: int(top_n)]