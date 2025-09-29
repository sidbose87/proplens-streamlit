import json
import os

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "insurance_cost_per_sqm.json")
with open(os.path.abspath(DATA), "r", encoding="utf-8") as f:
    COSTS = json.load(f)


def estimate_sum_insured(build_sqm: float) -> float:
    cost = COSTS.get("default_cost_per_sqm", 2500)
    return max(0.0, build_sqm) * cost


def premium_from_risk(sum_insured: float, risk: str) -> float:
    base_rate = 0.0035  # 0.35 percent of sum insured
    mult = {"low": 0.9, "medium": 1.0, "high": 1.2}.get(risk, 1.0)
    return sum_insured * base_rate * mult