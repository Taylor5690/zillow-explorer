thonimport os
import sys
from typing import Any, Dict, List

# Ensure src directory is on sys.path
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEST_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from extractors.filters import apply_filters  # type: ignore  # noqa: E402
from transformers.data_cleanser import clean_record  # type: ignore  # noqa: E402
from transformers.field_mapper import map_fields  # type: ignore  # noqa: E402

def _sample_records() -> List[Dict[str, Any]]:
    return [
        {
            "zpid": 1,
            "price": {"value": 300000},
            "bedrooms": 2,
            "address": {"streetAddress": "A", "city": "X", "state": "NY", "zipcode": "12345"},
            "extra": None,
        },
        {
            "zpid": 2,
            "price": {"value": 500000},
            "bedrooms": 4,
            "address": {"streetAddress": "B", "city": "Y", "state": "NY", "zipcode": "67890"},
            "extra": "",
        },
        {
            "zpid": 3,
            "price": {"value": 750000},
            "bedrooms": 5,
            "address": {"streetAddress": "C", "city": "Z", "state": "NY", "zipcode": "00000"},
            "extra": [],
        },
    ]

def test_clean_record_strips_empty_values() -> None:
    record = {
        "a": None,
        "b": "",
        "c": [],
        "d": {},
        "e": {"x": None, "y": 1},
    }
    cleaned = clean_record(record, strip_empty=True)
    assert "a" not in cleaned
    assert "b" not in cleaned
    assert "c" not in cleaned
    assert "d" not in cleaned
    assert cleaned["e"] == {"y": 1}

def test_apply_filters_by_price_and_bedrooms() -> None:
    records = _sample_records()
    filtered = apply_filters(
        records,
        min_price=400000,
        max_price=800000,
        min_bedrooms=3,
        sort_by="price.value",
        order="asc",
        limit=None,
    )
    assert len(filtered) == 2
    assert filtered[0]["zpid"] == 2
    assert filtered[1]["zpid"] == 3

def test_map_fields_includes_and_renames() -> None:
    records = _sample_records()
    mapped = map_fields(
        records,
        field_mapping={"price": "priceUsd"},
        include_fields=["zpid", "price"],
    )

    assert len(mapped) == len(records)
    first = mapped[0]
    assert "zpid" in first
    assert "priceUsd" in first
    assert "price" not in first