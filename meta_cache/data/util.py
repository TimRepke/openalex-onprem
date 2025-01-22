from typing import Any

def get(obj: dict[str, Any], *keys, default: Any = None) -> Any | None:
    for key in keys:
        obj = obj.get(key)
        if obj is None:
            return default
    return obj

