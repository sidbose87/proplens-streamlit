from pydantic import BaseModel


class ExpenseBreakdown(BaseModel):
    stamp_duty: float
    council_rates_annual: float
    insurance_annual: float
    mortgage_monthly: float
    pm_fee_pct: float