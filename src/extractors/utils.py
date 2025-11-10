thonfrom __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Union

_LOGGING_CONFIGURED = False

def _configure_logging() -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )
    _LOGGING_CONFIGURED = True

def get_logger(name: str) -> logging.Logger:
    _configure_logging()
    return logging.getLogger(name)

def load_json_file(path: str) -> Union[Dict[str, Any], List[Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json_file(path: str, data: Any, pretty: bool = True) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if pretty:
            json.dump(data, f, indent=4, sort_keys=False)
        else:
            json.dump(data, f, separators=(",", ":"))