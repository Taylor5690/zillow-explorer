thonfrom __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .utils import get_logger

logger = get_logger("filters")

def _get_nested_value(data: Dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current

def _apply_price_filter(
    listings: Iterable[Dict[str, Any]],
    min_price: Optional[int],
    max_price: Optional[int],
) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for listing in listings:
        price = _get_nested_value(listing, "price.value")
        if price is None:
            continue
        if min_price is not None and price < min_price:
            continue
        if max_price is not None and price > max_price:
            continue
        result.append(listing)
    return result

def _apply_bedroom_filter(
    listings: Iterable[Dict[str, Any]],
    min_bedrooms: Optional[int],
) -> List[Dict[str, Any]]:
    if min_bedrooms is None:
        return list(listings)
    result: List[Dict[str, Any]] = []
    for listing in listings:
        beds = listing.get("bedrooms")
        if beds is None:
            continue
        try:
            if int(beds) >= min_bedrooms:
                result.append(listing)
        except (TypeError, ValueError):
            continue
    return result

def _apply_sorting(
    listings: Iterable[Dict[str, Any]],
    sort_by: str,
    order: str,
) -> List[Dict[str, Any]]:
    reverse = order.lower() == "desc"

    def sort_key(item: Dict[str, Any]) -> Any:
        value = _get_nested_value(item, sort_by)
        # Ensure None values go to the end
        return (value is None, value)

    try:
        return sorted(listings, key=sort_key, reverse=reverse)
    except TypeError:
        # Fallback: no sorting if incomparable types are encountered
        logger.warning("Failed to sort by %s due to incomparable types", sort_by)
        return list(listings)

def apply_filters(
    listings: List[Dict[str, Any]],
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_bedrooms: Optional[int] = None,
    sort_by: str = "price.value",
    order: str = "asc",
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Apply filtering, sorting and limiting to a list of normalized listings.
    """
    logger.info(
        "Applying filters: min_price=%s max_price=%s min_bedrooms=%s sort_by=%s order=%s limit=%s",
        min_price,
        max_price,
        min_bedrooms,
        sort_by,
        order,
        limit,
    )

    filtered = _apply_price_filter(listings, min_price, max_price)
    filtered = _apply_bedroom_filter(filtered, min_bedrooms)
    sorted_list = _apply_sorting(filtered, sort_by, order)

    if limit is not None and limit > 0:
        sorted_list = sorted_list[:limit]

    return sorted_list