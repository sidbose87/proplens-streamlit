import math

def calc_repayments(loan_amount: float, rate_annual: float, years: int) -> float:
    if loan_amount <= 0 or years <= 0:
        return 0.0
    r = rate_annual / 12.0
    n = years * 12
    if r == 0:
        return loan_amount / n
    return loan_amount * (r * (1 + r) ** n) / ((1 + r) ** n - 1)