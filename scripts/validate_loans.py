import csv
import sys

from pydantic import ValidationError

from jpmorgan_loan_setup_tool.loan_terms import LoanTerms

DEFAULT_CSV = "Hand-Checked Loan Terms Answer Key (20 Agreements).csv"


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    passed, failed = 0, []
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for i, row in enumerate(rows, start=2):  # line 1 is the header
        try:
            LoanTerms(**row)
            passed += 1
        except ValidationError as e:
            failed.append((i, row.get("agreement_id", "?"), e))
    print(f"{path}: {passed} of {len(rows)} rows passed")
    for line, agr, err in failed:
        print(f"\nLine {line} ({agr}):")
        for problem in err.errors():
            print(f"  {'.'.join(map(str, problem['loc']))}: {problem['msg']}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
