from typing import List, Dict, Any, TypedDict, Optional, Literal

class BudgetedTime(TypedDict):
    total_days: str
    hours_per_day: str
    total_hours: str

class UserInfo(TypedDict):
    purpose: str
    level: str
    known_concept: List[str]
    budgeted_time: BudgetedTime
    resource_type_preference: List[str]
