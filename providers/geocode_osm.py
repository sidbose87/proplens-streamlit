import requests
from typing import List
from models.facts import AddressResolved

UA = {"User-Agent": "PropLens/0.1 (+https://example.com)"}

OSM_URL = "https://nominatim.openstreetmap.org/search"

def search_addresses(query: str) -> List[AddressResolved]:
    params = {
        "q": query,
        "format": "json",
        "addressdetails": 1,
        "limit": 5,
        "countrycodes": "au",
    }
    r = requests.get(OSM_URL, params=params, headers=UA, timeout=20)
    r.raise_for_status()
    out: List[AddressResolved] = []
    for item in r.json():
        addr = item.get("address", {})
        out.append(AddressResolved(
            query=query,
            display_name=item.get("display_name", ""),
            lat=float(item.get("lat")),
            lon=float(item.get("lon")),
            suburb=addr.get("suburb") or addr.get("town") or addr.get("city_suburb"),
            state=addr.get("state"),
            postcode=addr.get("postcode"),
            lga=None,
        ))
    return out