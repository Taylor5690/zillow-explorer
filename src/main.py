thonimport json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

import click

# Ensure src directory is on sys.path so we can import our internal modules
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from extractors.property_parser import parse_property_listings  # type: ignore  # noqa: E402
from extractors.filters import apply_filters  # type: ignore  # noqa: E402
from extractors.utils import get_logger, load_json_file, save_json_file  # type: ignore  # noqa: E402
from transformers.field_mapper import map_fields  # type: ignore  # noqa: E402
from transformers.data_cleanser import clean_record  # type: ignore  # noqa: E402

logger = get_logger("zillow_explorer")

def load_settings() -> Dict[str, Any]:
    settings_path = os.path.join(CURRENT_DIR, "config", "settings.json")
    try:
        return load_json_file(settings_path)
    except FileNotFoundError:
        logger.warning("settings.json not found, using default settings")
        return {
            "filters": {
                "min_price": None,
                "max_price": None,
                "min_bedrooms": None,
                "sort_by": "price.value",
                "order": "asc",
                "limit": 50,
            },
            "transform": {
                "include_fields": [],
                "field_mapping": {},
                "strip_empty": True,
            },
        }

def build_pipeline(
    raw_listings: List[Dict[str, Any]],
    settings: Dict[str, Any],
) -> List[Dict[str, Any]]:
    logger.info("Starting pipeline for %d raw listings", len(raw_listings))

    normalized = parse_property_listings(raw_listings)
    logger.info("Parsed %d normalized listings", len(normalized))

    filters_cfg = settings.get("filters", {})
    filtered = apply_filters(
        normalized,
        min_price=filters_cfg.get("min_price"),
        max_price=filters_cfg.get("max_price"),
        min_bedrooms=filters_cfg.get("min_bedrooms"),
        sort_by=filters_cfg.get("sort_by", "price.value"),
        order=filters_cfg.get("order", "asc"),
        limit=filters_cfg.get("limit"),
    )
    logger.info("After filtering, %d listings remain", len(filtered))

    transform_cfg = settings.get("transform", {})
    mapped = map_fields(
        filtered,
        field_mapping=transform_cfg.get("field_mapping") or {},
        include_fields=transform_cfg.get("include_fields") or [],
    )

    strip_empty = bool(transform_cfg.get("strip_empty", True))
    cleaned: List[Dict[str, Any]] = []
    for item in mapped:
        cleaned_item = clean_record(item, strip_empty=strip_empty)
        if cleaned_item:
            cleaned.append(cleaned_item)

    logger.info("Cleaned %d listings", len(cleaned))
    return cleaned

@click.command()
@click.option(
    "--input-file",
    "-i",
    default=None,
    help="Path to JSON file containing raw Zillow-like listing data.",
)
@click.option(
    "--output-file",
    "-o",
    default=None,
    help="Path where the normalized JSON output should be written.",
)
@click.option(
    "--pretty",
    is_flag=True,
    default=True,
    help="Pretty-print JSON output.",
)
def main(input_file: Optional[str], output_file: Optional[str], pretty: bool) -> None:
    """
    Run the Zillow Explorer pipeline on sample or provided input data.
    """
    project_root = os.path.dirname(CURRENT_DIR)
    default_input = os.path.join(project_root, "data", "inputs.sample.json")
    default_output = os.path.join(project_root, "data", "example_output.json")

    input_path = input_file or default_input
    output_path = output_file or default_output

    logger.info("Loading settings and input data")
    settings = load_settings()
    try:
        raw_listings = load_json_file(input_path)
    except FileNotFoundError:
        logger.error("Input file not found: %s", input_path)
        raise SystemExit(1)
    except json.JSONDecodeError as exc:
        logger.error("Failed to decode input JSON: %s", exc)
        raise SystemExit(1)

    if not isinstance(raw_listings, list):
        logger.error("Input JSON must be a list of listing objects")
        raise SystemExit(1)

    try:
        result = build_pipeline(raw_listings, settings)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Pipeline execution failed: %s", exc)
        raise SystemExit(1)

    logger.info("Writing %d records to %s", len(result), output_path)
    save_json_file(output_path, result, pretty=pretty)
    click.echo(f"Wrote {len(result)} records to {output_path}")

if __name__ == "__main__":
    main()