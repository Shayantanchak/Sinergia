"""
Phase 2 Live Demonstration Script for Sinergia
Run this script to perform real-time merger math, EPS accretion/dilution analysis, and breakeven synergy calculations.
"""
from backend.ingestion import fetch_company_financials
from backend.models import FinancialMetrics, DealInputParams
from backend.merger_engine import calculate_merger_math

def run_phase2_demo():
    print("=" * 70)
    print("      SINERGIA — PHASE 2 MERGER MECHANICS & BREAKEVEN DEMO")
    print("=" * 70)

    # 1. Ingest live market data for Acquirer and Target
    acquirer_ticker = "AAPL"
    target_ticker = "MSFT"
    print(f"\n[1/3] Ingesting Live 3-Statement Data ({acquirer_ticker} & {target_ticker})...")
    
    acquirer = fetch_company_financials(acquirer_ticker)
    target = fetch_company_financials(target_ticker)
    
    print(f"  • {acquirer.company_name} ({acquirer.ticker}): Share Price = ${acquirer.share_price:,.2f} | Net Income = ${acquirer.net_income / 1e9:,.2f}B | Standalone EPS = ${acquirer.net_income / acquirer.diluted_shares:,.2f}")
    print(f"  • {target.company_name} ({target.ticker}): Share Price = ${target.share_price:,.2f} | Net Income = ${target.net_income / 1e9:,.2f}B")

    # 2. Configure Deal Structuring Parameters
    # Deal Structure: 30% Offer Premium, 40% Cash / 30% Debt / 30% Stock
    params = DealInputParams(
        acquirer_ticker=acquirer_ticker,
        target_ticker=target_ticker,
        offer_premium_pct=30.0,
        cash_pct=40.0,
        debt_pct=30.0,
        stock_pct=30.0,
        cost_of_debt_pct=5.5,
        foregone_interest_rate_pct=2.5,
        synergies_pre_tax=10_000_000_000.0 # $10B pre-tax synergies
    )

    print("\n[2/3] Executing Merger Mathematics Engine...")
    res = calculate_merger_math(acquirer, target, params)

    print("\n" + "-" * 70)
    print("                     TRANSACTION SUMMARY")
    print("-" * 70)
    print(f"  • Target Share Price:        ${res['target_share_price']:,.2f}")
    print(f"  • Offer Premium:             {res['offer_premium_pct']:.1f}%")
    print(f"  • Offer Price per Share:     ${res['offer_price']:,.2f}")
    print(f"  • Purchase Equity Value:     ${res['purchase_equity_value'] / 1e9:,.2f} Billion")
    print(f"  • Goodwill Created:          ${res['goodwill_created'] / 1e9:,.2f} Billion")

    print("\n" + "-" * 70)
    print("                 CONSIDERATION & SHARE DILUTION")
    print("-" * 70)
    print(f"  • Cash Portion ({res['cash_pct']:.1f}%):       ${res['cash_used'] / 1e9:,.2f} Billion")
    print(f"  • Debt Portion ({res['debt_pct']:.1f}%):       ${res['debt_raised'] / 1e9:,.2f} Billion")
    print(f"  • Stock Portion ({res['stock_pct']:.1f}%):      ${res['stock_value'] / 1e9:,.2f} Billion")
    print(f"  • New Shares Issued:         {res['new_shares_issued'] / 1e6:,.2f} Million shares")
    print(f"  • Pro-Forma Share Count:     {res['pro_forma_shares'] / 1e6:,.2f} Million shares")

    print("\n" + "-" * 70)
    print("            PRO-FORMA EARNINGS & ACCRETION/DILUTION")
    print("-" * 70)
    print(f"  • Net Interest Burden:       ${res['net_interest_burden'] / 1e6:,.2f} Million")
    print(f"  • Post-Tax Synergies/Interest: ${res['post_tax_synergies'] / 1e9:,.2f} Billion")
    print(f"  • Pro-Forma Net Income:      ${res['pro_forma_net_income'] / 1e9:,.2f} Billion")
    print(f"  • Acquirer Standalone EPS:   ${res['standalone_eps']:,.2f}")
    print(f"  • Pro-Forma EPS:             ${res['pro_forma_eps']:,.2f}")
    
    accretion_str = "ACCRETIVE (+)" if res['accretion_dilution_pct'] >= 0 else "DILUTIVE (-)"
    print(f"  • Deal Impact:               {accretion_str} {res['accretion_dilution_pct']:+.2f}%")

    print("\n" + "-" * 70)
    print("              BREAKEVEN PRE-TAX SYNERGY SOLVER")
    print("-" * 70)
    print(f"  • Breakeven Pre-Tax Synergies Required: ${res['breakeven_synergies'] / 1e9:,.2f} Billion")
    print("-" * 70)
    print("\n[3/3] Demo completed successfully! Phase 2 engine is 100% operational.\n")

if __name__ == "__main__":
    run_phase2_demo()
