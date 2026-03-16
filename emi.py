"""
Series 8, CORE
Project 8b, EMI Wizard
-----------------------
A loan EMI calculator that does more than just give you a number.
It shows you the full picture: every payment, every rupee of interest,
and how much you're actually paying for the convenience of borrowing.

Features:
  - EMI calculation using the standard reducing-balance formula
  - Full amortization schedule (month-by-month breakdown)
  - Total interest paid, effective cost of loan
  - Compare multiple loans side by side
  - Export schedule to CSV

Usage:
  python emi.py                          # interactive mode
  python emi.py --principal 500000 --rate 8.5 --tenure 60
  python emi.py --compare                # compare multiple loans
  python emi.py --principal 500000 --rate 8.5 --tenure 60 --export

Author: Vidit Singhal
"""

import argparse
import csv
import os
import math


# ─── CORE MATH ────────────────────────────────────────────────────────────────

def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """
    Standard reducing-balance EMI formula.

    EMI = P × r × (1 + r)^n / ((1 + r)^n − 1)

    Where:
        P = principal amount
        r = monthly interest rate (annual rate / 12 / 100)
        n = tenure in months
    """
    if annual_rate == 0:
        return principal / tenure_months

    r = annual_rate / 12 / 100
    emi = principal * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1)
    return emi


def build_schedule(principal: float, annual_rate: float, tenure_months: int):
    """
    Build a full month-by-month amortization schedule.

    Returns a list of dicts, one per month:
        month, opening_balance, emi, principal_component,
        interest_component, closing_balance
    """
    emi = calculate_emi(principal, annual_rate, tenure_months)
    r   = annual_rate / 12 / 100

    schedule       = []
    balance        = principal
    total_interest = 0
    total_paid     = 0

    for month in range(1, tenure_months + 1):
        interest   = balance * r
        principal_part = emi - interest

        # Last month: clear any rounding residue
        if month == tenure_months:
            principal_part = balance
            emi_actual     = principal_part + interest
        else:
            emi_actual = emi

        closing = balance - principal_part
        total_interest += interest
        total_paid     += emi_actual

        schedule.append({
            "month":              month,
            "opening_balance":    round(balance, 2),
            "emi":                round(emi_actual, 2),
            "principal":          round(principal_part, 2),
            "interest":           round(interest, 2),
            "closing_balance":    max(0, round(closing, 2)),
            "total_paid_so_far":  round(total_paid, 2),
        })

        balance = max(0, closing)

    return schedule, round(emi, 2), round(total_interest, 2), round(total_paid, 2)


# ─── DISPLAY ──────────────────────────────────────────────────────────────────

def fmt(n: float) -> str:
    """Format number as Indian-style currency string."""
    return f"₹{n:,.2f}"


def print_summary(principal, annual_rate, tenure_months, emi, total_interest, total_paid):
    """Print the top-level loan summary."""
    tenure_years  = tenure_months // 12
    tenure_rem    = tenure_months % 12
    interest_pct  = (total_interest / principal) * 100
    cost_factor   = total_paid / principal

    tenure_str = ""
    if tenure_years:
        tenure_str += f"{tenure_years}y "
    if tenure_rem:
        tenure_str += f"{tenure_rem}m"

    print()
    print("  ╔══════════════════════════════════════════════╗")
    print("  ║              LOAN SUMMARY                    ║")
    print("  ╠══════════════════════════════════════════════╣")
    print(f"  ║  Principal          {fmt(principal):>24}  ║")
    print(f"  ║  Interest Rate      {annual_rate:>23.2f}%  ║")
    print(f"  ║  Tenure             {tenure_str:>24}  ║")
    print("  ╠══════════════════════════════════════════════╣")
    print(f"  ║  Monthly EMI        {fmt(emi):>24}  ║")
    print(f"  ║  Total Interest     {fmt(total_interest):>24}  ║")
    print(f"  ║  Total Amount Paid  {fmt(total_paid):>24}  ║")
    print("  ╠══════════════════════════════════════════════╣")
    print(f"  ║  Interest Burden    {interest_pct:>23.1f}%  ║")
    print(f"  ║  Cost Factor        {cost_factor:>23.2f}x  ║")
    print("  ╚══════════════════════════════════════════════╝")
    print()
    print(f"  → For every ₹1 borrowed, you pay back ₹{cost_factor:.2f}")
    print(f"  → ₹{total_interest:,.0f} goes purely to the bank as interest")
    print()


def print_schedule(schedule, show_all=False):
    """
    Print the amortization schedule.
    By default shows first 3, last 3, and every 12th month.
    Pass show_all=True to print every month.
    """
    header = (
        f"  {'Mo':>3}  {'Opening':>14}  {'EMI':>12}  "
        f"{'Principal':>12}  {'Interest':>12}  {'Closing':>14}"
    )
    divider = "  " + "─" * (len(header) - 2)

    print(header)
    print(divider)

    show_months = set()
    if show_all:
        show_months = set(range(1, len(schedule) + 1))
    else:
        total = len(schedule)
        # First 3, last 3, every 12th
        show_months = {1, 2, 3, total - 2, total - 1, total}
        show_months.update(range(12, total, 12))

    last_shown = 0
    for row in schedule:
        m = row["month"]
        if m not in show_months:
            continue
        if m > last_shown + 1 and last_shown != 0:
            print(f"  {'·':>3}  {'···':>14}  {'···':>12}  {'···':>12}  {'···':>12}  {'···':>14}")
        print(
            f"  {m:>3}  {fmt(row['opening_balance']):>14}  "
            f"{fmt(row['emi']):>12}  {fmt(row['principal']):>12}  "
            f"{fmt(row['interest']):>12}  {fmt(row['closing_balance']):>14}"
        )
        last_shown = m

    print(divider)


def print_comparison(loans):
    """Compare multiple loan options side by side."""
    print()
    print("  ╔══════════════════════════════════════════════════════════════╗")
    print("  ║                    LOAN COMPARISON                          ║")
    print("  ╠══════════════════════════════════════════════════════════════╣")
    print(f"  ║  {'':>3}  {'Principal':>12}  {'Rate':>6}  {'Tenure':>7}  {'EMI':>12}  {'Total Interest':>15}  ║")
    print("  ╠══════════════════════════════════════════════════════════════╣")

    best_interest = min(loans, key=lambda x: x["total_interest"])

    for i, loan in enumerate(loans, 1):
        marker = " ★" if loan["total_interest"] == best_interest["total_interest"] else "  "
        tenure_str = f"{loan['tenure'] // 12}y {loan['tenure'] % 12}m".strip()
        print(
            f"  ║{marker} {i}  {fmt(loan['principal']):>12}  "
            f"{loan['rate']:>5.1f}%  {tenure_str:>7}  "
            f"{fmt(loan['emi']):>12}  {fmt(loan['total_interest']):>15}  ║"
        )

    print("  ╚══════════════════════════════════════════════════════════════╝")
    print()
    print("  ★ = lowest total interest paid")
    print()


# ─── EXPORT ───────────────────────────────────────────────────────────────────

def export_csv(schedule, principal, annual_rate, tenure_months, emi, total_interest, total_paid):
    """Export amortization schedule to a CSV file."""
    filename = f"emi_schedule_{int(principal)}_{annual_rate}pct_{tenure_months}m.csv"

    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)

        # Metadata header
        writer.writerow(["EMI Wizard, Series 8 Project 8b"])
        writer.writerow([])
        writer.writerow(["Principal",    principal])
        writer.writerow(["Annual Rate",  f"{annual_rate}%"])
        writer.writerow(["Tenure",       f"{tenure_months} months"])
        writer.writerow(["Monthly EMI",  emi])
        writer.writerow(["Total Interest Paid", total_interest])
        writer.writerow(["Total Amount Paid",   total_paid])
        writer.writerow([])

        # Schedule
        writer.writerow([
            "Month", "Opening Balance", "EMI",
            "Principal", "Interest", "Closing Balance", "Total Paid So Far"
        ])
        for row in schedule:
            writer.writerow([
                row["month"],
                row["opening_balance"],
                row["emi"],
                row["principal"],
                row["interest"],
                row["closing_balance"],
                row["total_paid_so_far"],
            ])

    print(f"  ✓ Schedule exported → {filename}")
    print()
    return filename


# ─── INPUT HELPERS ────────────────────────────────────────────────────────────

def get_float(prompt: str, min_val=0, max_val=None) -> float:
    while True:
        try:
            val = float(input(prompt).strip().replace(",", ""))
            if val <= min_val:
                print(f"  ✗ Must be greater than {min_val}. Try again.")
                continue
            if max_val and val > max_val:
                print(f"  ✗ Must be less than {max_val}. Try again.")
                continue
            return val
        except ValueError:
            print("  ✗ Invalid number. Try again.")


def get_int(prompt: str, min_val=1, max_val=None) -> int:
    while True:
        try:
            val = int(input(prompt).strip())
            if val < min_val:
                print(f"  ✗ Must be at least {min_val}. Try again.")
                continue
            if max_val and val > max_val:
                print(f"  ✗ Must be at most {max_val}. Try again.")
                continue
            return val
        except ValueError:
            print("  ✗ Invalid number. Try again.")


# ─── MODES ────────────────────────────────────────────────────────────────────

def interactive_mode():
    """Guided interactive input."""
    print()
    print("  ─────────────────────────────────────")
    print("   Enter your loan details below.")
    print("   Press Ctrl+C anytime to exit.")
    print("  ─────────────────────────────────────")
    print()

    principal      = get_float("  Loan Amount (₹): ", min_val=0)
    annual_rate    = get_float("  Annual Interest Rate (%): ", min_val=0, max_val=100)
    tenure_months  = get_int("  Tenure (months): ", min_val=1, max_val=600)

    schedule, emi, total_interest, total_paid = build_schedule(
        principal, annual_rate, tenure_months
    )

    print_summary(principal, annual_rate, tenure_months, emi, total_interest, total_paid)

    show = input("  Show amortization schedule? (y/n): ").strip().lower()
    if show == "y":
        print()
        show_all = input("  Show all months or summary? (all/summary): ").strip().lower()
        print_schedule(schedule, show_all=(show_all == "all"))

    export = input("\n  Export to CSV? (y/n): ").strip().lower()
    if export == "y":
        export_csv(schedule, principal, annual_rate, tenure_months, emi, total_interest, total_paid)


def compare_mode():
    """Compare multiple loan scenarios interactively."""
    print()
    print("  ─────────────────────────────────────")
    print("   LOAN COMPARISON MODE")
    print("   Enter each loan option one by one.")
    print("   Type 'done' when finished (min 2).")
    print("  ─────────────────────────────────────")

    loans = []
    while True:
        print(f"\n  Loan option {len(loans) + 1}:")
        principal     = get_float("    Amount (₹): ", min_val=0)
        annual_rate   = get_float("    Rate (%): ", min_val=0, max_val=100)
        tenure_months = get_int("    Tenure (months): ", min_val=1)

        _, emi, total_interest, total_paid = build_schedule(principal, annual_rate, tenure_months)
        loans.append({
            "principal":      principal,
            "rate":           annual_rate,
            "tenure":         tenure_months,
            "emi":            emi,
            "total_interest": total_interest,
            "total_paid":     total_paid,
        })

        if len(loans) >= 2:
            again = input("\n  Add another loan? (y/n): ").strip().lower()
            if again != "y":
                break

    print_comparison(loans)


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="EMI Wizard, Loan calculator with full amortization schedule",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python emi.py
  python emi.py --principal 1000000 --rate 9.0 --tenure 240
  python emi.py --principal 500000 --rate 8.5 --tenure 60 --export
  python emi.py --compare
  python emi.py --principal 750000 --rate 10.5 --tenure 36 --all
        """
    )

    parser.add_argument("--principal", type=float, help="Loan amount in ₹")
    parser.add_argument("--rate",      type=float, help="Annual interest rate (%%)")
    parser.add_argument("--tenure",    type=int,   help="Loan tenure in months")
    parser.add_argument("--export",    action="store_true", help="Export schedule to CSV")
    parser.add_argument("--all",       action="store_true", help="Show full schedule (every month)")
    parser.add_argument("--compare",   action="store_true", help="Compare multiple loans")
    args = parser.parse_args()

    print()
    print("  ╔══════════════════════════════╗")
    print("  ║       EMI WIZARD, 8b        ║")
    print("  ╚══════════════════════════════╝")

    try:
        if args.compare:
            compare_mode()
            return

        if args.principal and args.rate and args.tenure:
            # Direct CLI args
            schedule, emi, total_interest, total_paid = build_schedule(
                args.principal, args.rate, args.tenure
            )
            print_summary(args.principal, args.rate, args.tenure, emi, total_interest, total_paid)
            print_schedule(schedule, show_all=args.all)
            if args.export:
                export_csv(schedule, args.principal, args.rate, args.tenure, emi, total_interest, total_paid)
        else:
            # Interactive
            interactive_mode()

    except KeyboardInterrupt:
        print("\n\n  Exiting. Goodbye.\n")


if __name__ == "__main__":
    main()