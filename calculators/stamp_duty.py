import json
import os

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "stamp_duty_rules", "nsw.json")

with open(os.path.abspath(DATA), "r", encoding="utf-8") as f:
    NSW_RULES = json.load(f)


def calc_stamp_duty(price: float, state: str = "NSW", owner_occ: bool = True) -> float:
    if state.upper() != "NSW":
        # Fallback simple percent
        return price * 0.045
    duty = 0.0
    for band in NSW_RULES["bands"]:
        low = band["low"]
        high = band["high"]
        rate = band["rate"]
        base = band.get("base", 0.0)
        if price >= low and (high is None or price <= high):
            duty = base + (price - low) * rate
            break
    if owner_occ and NSW_RULES.get("owner_occ_discount_pct"):
        duty = max(0.0, duty * (1 - NSW_RULES["owner_occ_discount_pct"]))
    return duty