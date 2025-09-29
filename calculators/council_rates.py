# Very simple council rate estimator based on land size

def calc_council_rates(lga: str, land_sqm: float) -> float:
    base = 1200.0
    var = 0.5 * max(0.0, land_sqm - 300)  # 50 cents per sqm over 300
    # crude LGA modifier
    mod = 1.1 if lga and "Sydney" in lga else 1.0
    return (base + var) * mod