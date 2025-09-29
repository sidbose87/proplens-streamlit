from pydantic import BaseModel


class MortgageInputs(BaseModel):
    price: float
    deposit_pct: float
    rate_pct: float
    years: int