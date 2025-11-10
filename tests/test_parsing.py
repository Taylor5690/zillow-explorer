thonimport json
import os
import sys
from typing import Any, Dict, List

import pytest

# Ensure src directory is on sys.path
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TEST_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from extractors.property_parser import parse_property_listings  # type: ignore  # noqa: E402
from extractors.utils import load_json_file  # type: ignore  # noqa: E402

def _load_sample_input() -> List[Dict[str, Any]]:
    data_path = os.path.join(PROJECT_ROOT, "data", "inputs.sample.json")
    data = load_json_file(data_path)
    assert isinstance(data, list)
    return data

def _load_schema() -> Dict[str, Any]:
    schema_path = os.path.join(PROJECT_ROOT, "data", "schema.json")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_parse_property_listings_produces_records() -> None:
    raw = _load_sample_input()
    parsed = parse_property_listings(raw)

    assert isinstance(parsed, list)
    assert len(parsed) >= 2

    first = parsed[0]
    assert "zpid" in first and isinstance(first["zpid"], int)
    assert "price" in first and isinstance(first["price"], dict)
    assert "value" in first["price"]

def test_parsed_records_match_minimal_schema() -> None:
    raw = _load_sample_input()
    parsed = parse_property_listings(raw)
    schema = _load_schema()

    required = schema.get("required", [])
    for record in parsed:
        # ensure required top-level keys exist
        for key in required:
            assert key in record, f"Record missing required key: {key}"

        # basic type checks
        assert isinstance(record["zpid"], int)
        assert isinstance(record["price"], dict)
        assert "value" in record["price"]
        assert isinstance(record["address"], dict)

@pytest.mark.parametrize("index", [0, 1])
def test_address_fields_present(index: int) -> None:
    raw = _load_sample_input()
    parsed = parse_property_listings(raw)

    assert len(parsed) > index
    addr = parsed[index]["address"]
    assert addr["streetAddress"]
    assert addr["city"]
    assert addr["state"]
    assert addr["zipcode"]