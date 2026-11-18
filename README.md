# JPMorgan_loan_setup_tool
## Loan terms validation rules

`LoanTerms` (`src/jpmorgan_loan_setup_tool/loan_terms.py`) rejects any row that breaks these rules:

- **borrower_name**: required and never blank, because a loan with no counterparty can't be traced.
- **commitment_amount**: a whole USD integer above zero. Integers avoid float rounding on amounts like 750000000, and zero or negative commitments are data errors.
- **maturity_date**: a real date in YYYY-MM-DD. One strict format avoids day/month mix-ups, and the parser rejects impossible dates like 2030-02-30.
- **margin_type**: `flat` or `grid`. A flat deal fills only `flat_margin_bps` and a grid deal fills only `pricing_grid`; both or neither is rejected, because it would be unclear which margin applies.
- **flat_margin_bps / margin_bps**: whole basis points, so margins are never fractional or stored as percentages.
- **pricing_grid**: a list of tiers sorted by `leverage_threshold` from low to high, with 99.00 as the top tier. It is never collapsed to one number, because a single value would lose how the margin steps up with leverage. The sort order and the 99.00 sentinel guarantee every leverage level maps to exactly one tier.
- **max_leverage_ratio / min_interest_coverage_ratio**: optional two-decimal ratios above zero, blank when a deal has no covenants. Blank means "no covenant", while zero would wrongly look like a real one.

The answer key also carries `agreement_id`, `checked_by` and `checked_date`. These are bookkeeping fields, accepted but not rule-checked. Any other unknown column is rejected.

Check the answer key with: `python scripts/validate_loans.py`

## Validation result

Running `python scripts/validate_loans.py` on the hand-checked answer key prints:

    Hand-Checked Loan Terms Answer Key (20 Agreements).csv: 20 of 20 rows passed
