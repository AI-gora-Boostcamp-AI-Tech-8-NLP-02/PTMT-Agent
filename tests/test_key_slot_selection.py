from core.llm.solar_pro_2_llm import resolve_upstage_api_key


def test_resolve_slot_key_when_available() -> None:
    env = {
        "UPSTAGE_API_KEY": "default-key",
        "UPSTAGE_API_KEY_3": "slot-3-key",
    }

    resolved = resolve_upstage_api_key(assigned_key_slot=3, env=env)
    assert resolved == "slot-3-key"


def test_resolve_falls_back_to_default_when_slot_missing() -> None:
    env = {
        "UPSTAGE_API_KEY": "default-key",
    }

    resolved = resolve_upstage_api_key(assigned_key_slot=4, env=env)
    assert resolved == "default-key"


def test_resolve_ignores_out_of_range_slot() -> None:
    env = {
        "UPSTAGE_API_KEY": "default-key",
        "UPSTAGE_API_KEY_7": "invalid-slot-key",
    }

    resolved = resolve_upstage_api_key(assigned_key_slot=7, env=env)
    assert resolved == "default-key"
