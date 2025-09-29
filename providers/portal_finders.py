from typing import List
from models.facts import AddressResolved
from core.rate_limit import polite_get
from bs4 import BeautifulSoup
import urllib.parse

# Deterministic site queries to focus on AU portals
SITES = [
    "realestate.com.au",
    "domain.com.au",
    "onthehouse.com.au",
    "realty.com.au",
    "propertyvalue.com.au",
]

DUCK_URL = "https://duckduckgo.com/html/"


def _duckduckgo_search(query: str) -> list[str]:
    # Build a simple DuckDuckGo HTML request
    params = {"q": query}
    url = DUCK_URL + "?" + urllib.parse.urlencode(params)
    resp, allowed = polite_get(url)
    if not allowed or not resp or not resp.ok:
        return []
    soup = BeautifulSoup(resp.text, "lxml")
    out: list[str] = []
    for a in soup.select("a.result__a"):
        href = a.get("href")
        if href:
            out.append(href)
    return out


def find_candidate_urls(address: AddressResolved) -> List[str]:
    queries = []
    line = address.display_name
    for site in SITES:
        q = f"{line} site:{site}"
        queries.append(q)

    results: list[str] = []
    for q in queries:
        links = _duckduckgo_search(q)
        for L in links:
            if any(s in L for s in SITES):
                results.append(L)
        if len(results) >= 6:
            break

    # Deduplicate
    seen = set()
    uniq: list[str] = []
    for u in results:
        if u not in seen:
            uniq.append(u)
            seen.add(u)
    return uniq[:8]