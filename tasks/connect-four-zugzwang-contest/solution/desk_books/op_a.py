"""Return the tournament schema token after confirming match logs exist."""


def op_a(history_dir: str) -> str:
    from pathlib import Path

    root = Path(history_dir)
    logs = sorted(root.glob("game_*.log"))
    if len(logs) < 1:
        raise FileNotFoundError("missing match logs")
    return "c4-zugzwang-v1"
