thonfrom __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional

from extractors.utils import get_logger

logger = get_logger("field_mapper")

def _copy_included_fields(
    record: Dict[str, Any],
    include_fields: Optional[List[str]],
) -> Dict[str, Any]:
    if not include_fields:
        # Copy everything
        return dict(record)

    result: Dict[str, Any] = {}
    for field in include_fields:
        if field in record:
            result[field] = record[field]
        else:
            # Support simple dotted-path extraction for nested objects
            parts = field.split(".")
            current: Any = record
            for part in parts:
                if not isinstance(current, dict):
                    current = None
                    break
                current = current.get(part)
            if current is not None:
                # Rebuild the nested structure under the same dotted path
                target = result
                for part in parts[:-1]:
                    target = target.setdefault(part, {})
                target[parts[-1]] = current
    return result

def _apply_field_mapping(
    record: Dict[str, Any],
    field_mapping: Mapping[str, str],
) -> Dict[str, Any]:
    # Only map top-level keys for simplicity; nested renames can be handled via dotted paths in include_fields.
    for old, new in field_mapping.items():
        if old in record:
            record[new] = record.pop(old)
    return record

def map_fields(
    records: Iterable[Dict[str, Any]],
    field_mapping: Optional[Mapping[str, str]] = None,
    include_fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Apply include/exclude logic and optional renaming to a list of records.
    """
    mapped_records: List[Dict[str, Any]] = []
    for record in records:
        base = _copy_included_fields(record, include_fields)
        if field_mapping:
            base = _apply_field_mapping(base, field_mapping)
        mapped_records.append(base)

    logger.info(
        "Mapped %d records (include_fields=%s, field_mapping_keys=%s)",
        len(mapped_records),
        include_fields or "all",
        list(field_mapping.keys()) if field_mapping else [],
    )
    return mapped_records