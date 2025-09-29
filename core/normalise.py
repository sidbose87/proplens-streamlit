from typing import Dict, Any, Optional
from models.facts import FieldValue, PropertyFacts, AddressResolved


def _fv(value, source: str, confidence: float) -> FieldValue:
    return FieldValue(value=value, source=source, confidence=confidence)


def _num(val) -> Optional[float]:
    try:
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip().replace(",", "")
        return float(s)
    except Exception:
        return None


def normalise_jsonld(jsonld: Dict[str, Any]) -> Dict[str, FieldValue]:
    out: Dict[str, FieldValue] = {}

    # Dwelling type
    jtype = jsonld.get("@type")
    dtype = None
    if isinstance(jtype, list):
        for t in jtype:
            if t in ("House","Apartment","SingleFamilyResidence","Residence"):
                dtype = t
                break
    elif isinstance(jtype, str):
        dtype = jtype
    if dtype:
        out["dwelling_type"] = _fv(dtype, "jsonld", 0.85)

    # Beds, baths, cars
    for k, outk in [
        ("numberOfBedrooms", "beds"),
        ("numberOfBathroomsTotal", "baths"),
        ("numberOfRooms", "rooms_hint"),
        ("numberOfFullBathrooms", "baths_full_hint"),
        ("numberOfPartialBathrooms", "baths_part_hint"),
        ("numberOfParkingSpaces", "cars"),
        ("vehicleSeatingCapacity", "cars_hint"),
    ]:
        v = _num(jsonld.get(k))
        if v is not None and outk in ("beds","baths","cars"):
            out[outk] = _fv(v, "jsonld", 0.9)

    # amenityFeature may carry totals
    af = jsonld.get("amenityFeature")
    if isinstance(af, list):
        for feat in af:
            name = str(feat.get("name", "")).lower()
            val = _num(feat.get("value"))
            if val is None:
                continue
            if "bath" in name:
                out.setdefault("baths", _fv(val, "jsonld", 0.8))
            if "bed" in name:
                out.setdefault("beds", _fv(val, "jsonld", 0.8))
            if any(x in name for x in ["car","garage","parking"]):
                out.setdefault("cars", _fv(val, "jsonld", 0.7))

    # Sizes
    def _size(node, outkey):
        if isinstance(node, dict):
            val = _num(node.get("value"))
            unit = node.get("unitCode") or node.get("unitText")
            if val is not None:
                # convert sqm if needed
                if unit and str(unit).lower() in ("sqm","m2","m^2","mtk"):
                    out[outkey] = _fv(val, "jsonld", 0.75)
                elif unit and str(unit).lower() in ("sqft","ft2"):
                    out[outkey] = _fv(val*0.092903, "jsonld", 0.7)
                else:
                    out[outkey] = _fv(val, "jsonld", 0.6)

    _size(jsonld.get("floorSize"), "build_sqm")
    _size(jsonld.get("lotSize"), "land_sqm")

    # Last sold price hint via offers
    offers = jsonld.get("offers")
    if isinstance(offers, dict):
        price = _num(offers.get("price"))
        if price:
            out["last_sold_price"] = _fv(price, "jsonld", 0.5)

    return out


def estimate_from_heuristics(address: AddressResolved, land_sqm: Optional[float]) -> Dict[str, FieldValue]:
    # Very basic heuristics. Replace with locality aware distributions later.
    beds = 4 if land_sqm and land_sqm >= 450 else 3
    baths = 2 if beds >= 3 else 1
    cars = 2 if beds >= 3 else 1
    build = 180.0 if beds >= 4 else 140.0
    dtype = "House" if (land_sqm or 0) >= 250 else "Apartment"
    out = {
        "dwelling_type": _fv(dtype, "estimated", 0.5),
        "beds": _fv(beds, "estimated", 0.5),
        "baths": _fv(baths, "estimated", 0.5),
        "cars": _fv(cars, "estimated", 0.5),
        "build_sqm": _fv(build, "estimated", 0.4),
    }
    if land_sqm:
        out["land_sqm"] = _fv(land_sqm, "open_data", 0.6)
    return out


def merge_facts(*, address: AddressResolved, jsonld_map: Dict[str, FieldValue] | None, open_data: dict | None, estimated_map: Dict[str, FieldValue], source_urls: list[str]) -> PropertyFacts:
    def pick(key: str) -> FieldValue:
        if jsonld_map and key in jsonld_map:
            return jsonld_map[key]
        if open_data and key in open_data and open_data[key] is not None:
            return FieldValue(value=open_data[key], source="open_data", confidence=float(open_data.get("confidence", 0.6)))
        return estimated_map.get(key, FieldValue(value=None, source="estimated", confidence=0.1))

    return PropertyFacts(
        address=address,
        dwelling_type=pick("dwelling_type"),
        beds=pick("beds"),
        baths=pick("baths"),
        cars=pick("cars"),
        land_sqm=pick("land_sqm"),
        build_sqm=pick("build_sqm"),
        last_sold_price=jsonld_map.get("last_sold_price") if jsonld_map else None,
        source_urls=source_urls or [],
    )