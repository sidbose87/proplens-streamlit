import json
from typing import Any, Dict, Optional, Tuple
from bs4 import BeautifulSoup
from core.rate_limit import polite_get


SCHEMA_TYPES = {
    "House",
    "Apartment",
    "SingleFamilyResidence",
    "Place",
    "Accommodation",
    "Offer",
    "Residence",
}


def _first_jsonld_block(html: str) -> Optional[Dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        txt = script.string or script.text
        if not txt:
            continue
        try:
            data = json.loads(txt)
        except Exception:
            continue
        # Handle list or graph
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and _is_property_schema(item):
                    return item
        elif isinstance(data, dict):
            if "@graph" in data and isinstance(data["@graph"], list):
                for item in data["@graph"]:
                    if isinstance(item, dict) and _is_property_schema(item):
                        return item
            if _is_property_schema(data):
                return data
    return None


def _is_property_schema(d: Dict[str, Any]) -> bool:
    t = d.get("@type")
    if isinstance(t, list):
        return any(x in SCHEMA_TYPES for x in t)
    return t in SCHEMA_TYPES


def extract_schema_org(url: str) -> Tuple[Optional[Dict[str, Any]], bool, bool]:
    """Return (jsonld, robots_allowed, fetched_ok). fetched_ok True means the page was fetched and parsed.
    If robots disallows, returns (None, False, False).
    """
    resp, allowed = polite_get(url)
    if not allowed:
        return None, False, False
    if not resp or not resp.ok:
        return None, True, False
    data = _first_jsonld_block(resp.text)
    return data, True, True