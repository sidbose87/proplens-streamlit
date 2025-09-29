def calc_cashflow(inflow_month: float, repayment_month: float, outgoings_month: float) -> float:
    return float(inflow_month) - float(repayment_month) - float(outgoings_month)