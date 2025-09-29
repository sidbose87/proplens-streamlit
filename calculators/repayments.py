def _pni_monthly(loan_amount: float, annual_rate: float, years: int) -> float:
    if loan_amount <= 0 or years <= 0:
        return 0.0
    r = annual_rate / 12.0
    n = years * 12
    if r == 0:
        return loan_amount / n
    return loan_amount * (r * (1 + r) ** n) / ((1 + r) ** n - 1)


def calc_repayments(
    loan_amount: float,
    annual_rate: float,
    years: int,
    repayment_type: str = "P&I",
    interest_only_years: int = 0
) -> float:
    if loan_amount <= 0:
        return 0.0
    repayment_type = (repayment_type or "P&I").upper()
    if repayment_type.startswith("I"):  # "IO"
        return loan_amount * (annual_rate / 12.0)
    return float(_pni_monthly(loan_amount, annual_rate, years))


def pick_active_rate(
    rate_type: str,
    variable_rate_pct: float,
    fixed_rate_pct: float,
    fixed_years: int
) -> float:
    rate_type = (rate_type or "Variable").lower()
    if rate_type.startswith("fixed"):
        return fixed_rate_pct / 100.0
    return variable_rate_pct / 100.0
