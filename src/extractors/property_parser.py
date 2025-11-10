thonfrom __future__ import annotations

from typing import Any, Dict, List, Optional

from .utils import get_logger

logger = get_logger("property_parser")

def _safe_int(value: Any) -> Optional[int]:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None

def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None

def _normalize_address(raw: Dict[str, Any]) -> Dict[str, Any]:
    addr = raw.get("address", {}) or {}

    street = addr.get("street") or addr.get("streetAddress") or raw.get("streetAddress")
    city = addr.get("city") or raw.get("city")
    state = addr.get("state") or raw.get("state")
    zipcode = addr.get("zipcode") or addr.get("zip") or raw.get("zipcode")

    return {
        "streetAddress": street,
        "city": city,
        "state": state,
        "zipcode": zipcode,
    }

def _normalize_price(raw: Dict[str, Any]) -> Dict[str, Any]:
    # Accept multiple possible keys for price
    price_value = (
        raw.get("price")
        or raw.get("priceValue")
        or (raw.get("price", {}) or {}).get("value")
        or raw.get("listPrice")
    )
    value_int = _safe_int(price_value)
    return {"value": value_int}

def _normalize_tax_assessment(raw: Dict[str, Any]) -> Dict[str, Any]:
    tax = raw.get("taxAssessment", {}) or {}
    assessed = (
        tax.get("taxAssessedValue")
        or raw.get("tax_assessed_value")
        or raw.get("taxAssessedValue")
    )
    year = tax.get("taxAssessmentYear") or raw.get("taxAssessmentYear") or raw.get(
        "tax_assessment_year"
    )
    return {
        "taxAssessedValue": _safe_int(assessed),
        "taxAssessmentYear": str(year) if year is not None else None,
    }

def _normalize_walkscore(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    ws = raw.get("walkScore") or raw.get("walkscore") or {}
    if isinstance(ws, dict):
        score = ws.get("walkscore") or ws.get("score")
        description = ws.get("description")
        if score is None and description is None:
            return None
        return {"walkscore": _safe_int(score), "description": description}
    if ws:
        return {"walkscore": _safe_int(ws), "description": None}
    return None

def _normalize_schools(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    schools = raw.get("schools") or []
    if not isinstance(schools, list):
        return []

    normalized: List[Dict[str, Any]] = []
    for s in schools:
        if not isinstance(s, dict):
            continue
        normalized.append(
            {
                "name": s.get("name") or s.get("schoolName"),
                "rating": _safe_int(s.get("rating") or s.get("score")),
                "distance": _safe_float(s.get("distance")),
            }
        )
    return normalized

def _normalize_price_history(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    history = raw.get("priceHistory") or []
    if not isinstance(history, list):
        return []
    return history

def _normalize_tax_history(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    history = raw.get("taxHistory") or []
    if not isinstance(history, list):
        return []
    return history

def _normalize_photos(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    photos = raw.get("photos") or []
    if not isinstance(photos, list):
        return []
    return photos

def _normalize_listing(raw: Dict[str, Any]) -> Dict[str, Any]:
    zpid = raw.get("zpid") or raw.get("id") or raw.get("zpid_raw")
    zpid_int = _safe_int(zpid)

    living_area = (
        raw.get("livingArea")
        or raw.get("area")
        or raw.get("living_area")
        or raw.get("sqft")
    )

    lot_size = None
    lot_size_container = raw.get("lotSizeWithUnit") or {}
    if isinstance(lot_size_container, dict):
        lot_size = lot_size_container.get("lotSize") or lot_size_container.get("value")

    result: Dict[str, Any] = {
        "zpid": zpid_int,
        "price": _normalize_price(raw),
        "address": _normalize_address(raw),
        "bedrooms": _safe_int(raw.get("bedrooms") or raw.get("beds")),
        "bathrooms": _safe_float(raw.get("bathrooms") or raw.get("baths")),
        "livingArea": _safe_int(living_area),
        "yearBuilt": _safe_int(raw.get("yearBuilt") or raw.get("year_built")),
        "lotSizeWithUnit": {"lotSize": _safe_int(lot_size)},
        "propertyType": raw.get("propertyType") or raw.get("property_type"),
        "taxAssessment": _normalize_tax_assessment(raw),
        "priceHistory": _normalize_price_history(raw),
        "taxHistory": _normalize_tax_history(raw),
        "schools": _normalize_schools(raw),
        "walkScore": _normalize_walkscore(raw),
        "resoFacts": raw.get("resoFacts") or raw.get("features") or {},
        "attributionInfo": raw.get("attributionInfo") or {},
        "photos": _normalize_photos(raw),
        "url": raw.get("url"),
    }

    logger.debug("Normalized listing for zpid %s", zpid_int)
    return result

def parse_property_listings(raw_listings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert raw scraped Zillow-like data into normalized listings.

    The function is defensive and attempts to handle missing or slightly
    malformed records without failing the entire batch.
    """
    normalized: List[Dict[str, Any]] = []
    for idx, raw in enumerate(raw_listings):
        if not isinstance(raw, dict):
            logger.warning("Skipping non-dict listing at index %d", idx)
            continue
        try:
            norm = _normalize_listing(raw)
            if norm.get("zpid") is None:
                logger.warning("Listing at index %d missing zpid, skipping", idx)
                continue
            normalized.append(norm)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to normalize listing at index %d: %s", idx, exc)
    return normalized