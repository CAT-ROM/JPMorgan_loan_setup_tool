import json
import re
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TOP_TIER = Decimal("99.00")

Ratio = Annotated[Decimal, Field(gt=0, decimal_places=2)]


class PricingTier(BaseModel):
    model_config = ConfigDict(extra="forbid")

    leverage_threshold: Decimal
    margin_bps: int


class LoanTerms(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Bookkeeping columns present in the answer key (not part of the rules)
    agreement_id: Optional[str] = None
    checked_by: Optional[str] = None
    checked_date: Optional[date] = None

    borrower_name: str = Field(min_length=1)
    commitment_amount: int = Field(gt=0)
    maturity_date: date
    margin_type: Literal["flat", "grid"]
    flat_margin_bps: Optional[int] = None
    pricing_grid: Optional[list[PricingTier]] = None
    max_leverage_ratio: Optional[Ratio] = None
    min_interest_coverage_ratio: Optional[Ratio] = None

    @field_validator("borrower_name", mode="before")
    @classmethod
    def strip_name(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("maturity_date", mode="before")
    @classmethod
    def strict_iso_date(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if not ISO_DATE.match(v):
                raise ValueError("maturity_date must be formatted YYYY-MM-DD")
            return date.fromisoformat(v)  # rejects impossible dates like 2030-02-30
        return v

    @field_validator(
        "agreement_id",
        "checked_by",
        "checked_date",
        "flat_margin_bps",
        "pricing_grid",
        "max_leverage_ratio",
        "min_interest_coverage_ratio",
        mode="before",
    )
    @classmethod
    def blank_to_none(cls, v):
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("pricing_grid", mode="before")
    @classmethod
    def parse_grid_json(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return None
            try:
                return json.loads(v, parse_float=Decimal)
            except json.JSONDecodeError as e:
                raise ValueError(f"pricing_grid is not valid JSON: {e}")
        return v

    @field_validator("pricing_grid")
    @classmethod
    def check_grid(cls, tiers):
        if tiers is None:
            return tiers
        if not tiers:
            raise ValueError("pricing_grid must contain at least one tier")
        thresholds = [t.leverage_threshold for t in tiers]
        if any(a >= b for a, b in zip(thresholds, thresholds[1:])):
            raise ValueError("tiers must be sorted by leverage_threshold, low to high, with no duplicates")
        if thresholds[-1] != TOP_TIER:
            raise ValueError("the top tier must have leverage_threshold 99.00")
        return tiers

    @model_validator(mode="after")
    def check_margin_shape(self):
        if self.margin_type == "flat":
            if self.flat_margin_bps is None:
                raise ValueError("flat deal needs flat_margin_bps")
            if self.pricing_grid is not None:
                raise ValueError("flat deal must not have a pricing_grid")
        else:
            if self.pricing_grid is None:
                raise ValueError("grid deal needs a pricing_grid")
            if self.flat_margin_bps is not None:
                raise ValueError("grid deal must not have flat_margin_bps")
        return self
