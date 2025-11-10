thonfrom __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from extractors.utils import get_logger

logger = get_logger("data_cleanser")

JsonType = Union[Dict[str, Any], List[Any], str, int, float, bool, None]

def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, tuple, set)) and len(value) == 0:
        return True
    if isinstance(value, dict) and len(value) == 0:
        return True
    return False

def _clean(value: JsonType, strip_empty: bool) -> Optional[JsonType]:
    if isinstance(value, dict):
        cleaned_dict: Dict[str, Any] = {}
        for key, val in value.items():
            cleaned_val = _clean(val, strip_empty)
            if strip_empty and _is_empty(cleaned_val):
                continue
            cleaned_dict[key] = cleaned_val
        if strip_empty and _is_empty(cleaned_dict):
            return None
        return cleaned_dict

    if isinstance(value, list):
        cleaned_list: List[Any] = []
        for item in value:
            cleaned_item = _clean(item, strip_empty)
            if strip_empty and _is_empty(cleaned_item):
                continue
            cleaned_list.append(cleaned_item)
        if strip_empty and _is_empty(cleaned_list):
            return None
        return cleaned_list

    # Scalars
    if strip_empty and _is_empty(value):
        return None
    return value

def clean_record(record: Dict[str, Any], strip_empty: bool = True) -> Dict[str, Any]:
    """
    Recursively remove null/empty values from a record.
    """
    cleaned = _clean(record, strip_empty)
    if cleaned is None:
        logger.debug("Record became empty after cleansing")
        return {}
    if not isinstance(cleaned, dict):
        # Should not happen for records, but keep defensive.
        return {"value": cleaned}
    return cleaned