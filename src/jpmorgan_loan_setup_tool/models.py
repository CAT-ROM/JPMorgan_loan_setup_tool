from decimal import Decimal
from pydantic import BaseModel, Field


class LoanSetup(BaseModel):
    principal: Decimal = Field(gt=0)
    annual_rate: Decimal = Field(ge=0, le=1)  # 0.065 = 6.5%
    term_months: int = Field(gt=0)
