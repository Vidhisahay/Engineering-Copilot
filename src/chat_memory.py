from typing import Any, Dict, List


def format_history_for_input(
    history: List[Dict[str, str]], current_msg: str, max_turns: int = 10
) -> str:
    if not history:
        return current_msg

    lines: List[str] = []
    for turn in history[-max_turns:]:
        lines.append(f"User: {turn['user']}")
        lines.append(f"Assistant: {turn['assistant']}")
    lines.append(f"User: {current_msg}")
    return "\n".join(lines)


def append_turn(
    history: List[Dict[str, str]] | None, user_msg: str, assistant_msg: str
) -> List[Dict[str, Any]]:
    updated = list(history or [])
    updated.append({"user": user_msg, "assistant": assistant_msg})
    return updated
