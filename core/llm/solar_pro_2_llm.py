import os
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Mapping, Optional

from dotenv import load_dotenv
from langchain_upstage import ChatUpstage

load_dotenv()

_ASSIGNED_KEY_SLOT: ContextVar[Optional[int]] = ContextVar(
    "assigned_key_slot",
    default=None,
)

def resolve_upstage_api_key(
    assigned_key_slot: Optional[int],
    env: Optional[Mapping[str, str]] = None,
) -> Optional[str]:
    """Resolve key by assigned slot, fallback to default key."""

    source = env or os.environ
    if assigned_key_slot is not None and 1 <= assigned_key_slot <= 5:
        slot_key = source.get(f"UPSTAGE_API_KEY_{assigned_key_slot}")
        if slot_key:
            return slot_key
    return source.get("UPSTAGE_API_KEY")


@contextmanager
def assigned_key_slot_context(assigned_key_slot: Optional[int]):
    """Temporarily bind key slot for all nested get_solar_model() calls."""

    token = _ASSIGNED_KEY_SLOT.set(assigned_key_slot)
    try:
        yield
    finally:
        _ASSIGNED_KEY_SLOT.reset(token)


def bind_assigned_key_slot(assigned_key_slot: Optional[int]) -> Token:
    """Bind slot to current context and return reset token."""

    return _ASSIGNED_KEY_SLOT.set(assigned_key_slot)


def reset_assigned_key_slot(token: Token) -> None:
    """Reset previously bound slot token."""

    _ASSIGNED_KEY_SLOT.reset(token)


def get_solar_model(
    model_name: str = "solar-pro2",
    temperature: float = 0.7,
    reasoning_effort: str = "medium",
    assigned_key_slot: Optional[int] = None,
):
    if assigned_key_slot is None:
        assigned_key_slot = _ASSIGNED_KEY_SLOT.get()

    api_key = resolve_upstage_api_key(assigned_key_slot)

    return ChatUpstage(
        model=model_name,
        temperature=temperature,
        upstage_api_key=api_key,
        reasoning_effort=reasoning_effort
    )
