import pytest
from pydantic import ValidationError
from backend.models import FinancialMetrics, DealInputParams
from backend.merger_engine import calculate_merger_math
from backend.ingestion import fetch_company_financials

def test_all_cash_accretion_logic():
    acquirer = FinancialMetrics(
        ticker="ACQ",
        share_price=100.0,
        diluted_shares=100000000.0, # 100M
        net_income=1000000000.0,    # $1B (EPS = $10)
        book_value_net_assets=5000000000.0,
        effective_tax_rate=0.20
    )
    target = FinancialMetrics(
        ticker="TGT",
        share_price=50.0,
        diluted_shares=50000000.0,  # 50M
        net_income=3000000000.0,    # $3B
        book_value_net_assets=2000000000.0,
        effective_tax_rate=0.20
    )
    params = DealInputParams(
        acquirer_ticker="ACQ",
        target_ticker="TGT",
        offer_premium_pct=20.0,      # Offer price = $60
        cash_pct=100.0,
        debt_pct=0.0,
        stock_pct=0.0,
        cost_of_debt_pct=5.0,
        foregone_interest_rate_pct=2.5,
        synergies_pre_tax=100000000.0 # $100M
    )

    res = calculate_merger_math(acquirer, target, params)
    
    assert res["offer_price"] == 60.0
    assert res["purchase_equity_value"] == 3000000000.0 # $3B
    assert res["goodwill_created"] == 1000000000.0 # $3B - $2B
    assert res["new_shares_issued"] == 0.0
    assert res["pro_forma_shares"] == 100000000.0
    
    # Net interest burden = $3B * 2.5% = $75M
    assert res["net_interest_burden"] == 75000000.0
    # Post tax synergies = ($100M - $75M) * (1 - 0.20) = $20M
    assert res["post_tax_synergies"] == 20000000.0
    # Pro forma Net Income = $1B + $3B + $20M = $4.02B
    assert res["pro_forma_net_income"] == 4020000000.0
    # Standalone EPS = $10.00, Pro-Forma EPS = $40.20
    assert res["standalone_eps"] == 10.0
    assert res["pro_forma_eps"] == 40.20
    assert pytest.approx(res["accretion_dilution_pct"], 0.01) == 302.0

def test_all_stock_dilution_thresholds():
    acquirer = FinancialMetrics(
        ticker="ACQ",
        share_price=100.0,
        diluted_shares=100000000.0, # 100M (EPS = $10)
        net_income=1000000000.0,    # $1B
        book_value_net_assets=5000000000.0,
        effective_tax_rate=0.20
    )
    target = FinancialMetrics(
        ticker="TGT",
        share_price=50.0,
        diluted_shares=50000000.0,  # 50M
        net_income=100000000.0,     # $100M (EPS = $2)
        book_value_net_assets=2000000000.0,
        effective_tax_rate=0.20
    )
    params = DealInputParams(
        acquirer_ticker="ACQ",
        target_ticker="TGT",
        offer_premium_pct=50.0,      # Offer price = $75
        cash_pct=0.0,
        debt_pct=0.0,
        stock_pct=100.0,
        cost_of_debt_pct=5.0,
        foregone_interest_rate_pct=2.5,
        synergies_pre_tax=0.0        # No synergies
    )

    res = calculate_merger_math(acquirer, target, params)
    
    assert res["offer_price"] == 75.0
    assert res["purchase_equity_value"] == 3750000000.0 # $3.75B
    assert res["new_shares_issued"] == 37500000.0      # 37.5M shares
    assert res["pro_forma_shares"] == 137500000.0     # 137.5M shares
    assert res["pro_forma_net_income"] == 1100000000.0 # $1.1B
    
    # Pro-Forma EPS = $1.1B / 137.5M = $8.00
    assert res["pro_forma_eps"] == 8.0
    # Accretion/Dilution % = ($8 - $10) / $10 = -20.0%
    assert pytest.approx(res["accretion_dilution_pct"], 0.01) == -20.0

def test_breakeven_synergy_solver_exactness():
    acquirer = FinancialMetrics(
        ticker="AAPL",
        share_price=150.0,
        diluted_shares=15000000000.0,
        net_income=90000000000.0,
        book_value_net_assets=60000000000.0,
        effective_tax_rate=0.21
    )
    target = FinancialMetrics(
        ticker="NFLX",
        share_price=400.0,
        diluted_shares=440000000.0,
        net_income=5000000000.0,
        book_value_net_assets=20000000000.0,
        effective_tax_rate=0.21
    )
    params = DealInputParams(
        acquirer_ticker="AAPL",
        target_ticker="NFLX",
        offer_premium_pct=30.0,
        cash_pct=40.0,
        debt_pct=30.0,
        stock_pct=30.0,
        cost_of_debt_pct=6.0,
        foregone_interest_rate_pct=3.0,
        synergies_pre_tax=0.0 # Arbitrary initial synergies
    )

    initial_res = calculate_merger_math(acquirer, target, params)
    bk_synergies = initial_res["breakeven_synergies"]
    
    # Plug computed breakeven synergies back into engine
    params_at_breakeven = params.model_copy()
    params_at_breakeven.synergies_pre_tax = bk_synergies
    
    breakeven_res = calculate_merger_math(acquirer, target, params_at_breakeven)
    
    # Verify that Pro-Forma EPS matches Standalone EPS and Accretion/Dilution % is 0.00%
    assert pytest.approx(breakeven_res["pro_forma_eps"], rel=1e-5) == breakeven_res["standalone_eps"]
    assert abs(breakeven_res["accretion_dilution_pct"]) < 1e-4

def test_pydantic_validation_boundaries():
    # Share price <= 0 should fail validation
    with pytest.raises(ValidationError):
        FinancialMetrics(
            ticker="BAD",
            share_price=0.0,
            diluted_shares=100.0,
            net_income=100.0,
            book_value_net_assets=100.0,
            effective_tax_rate=0.20
        )
        
    # Effective tax rate > 0.5 should fail validation
    with pytest.raises(ValidationError):
        FinancialMetrics(
            ticker="BAD",
            share_price=10.0,
            diluted_shares=100.0,
            net_income=100.0,
            book_value_net_assets=100.0,
            effective_tax_rate=0.85
        )

def test_mixed_consideration_structure():
    """Verify deal math for a 50% Cash / 30% Debt / 20% Stock deal."""
    acquirer = FinancialMetrics(
        ticker="ACQ",
        share_price=200.0,
        diluted_shares=50000000.0,  # 50M shares
        net_income=500000000.0,     # $500M ($10 EPS)
        book_value_net_assets=2000000000.0,
        effective_tax_rate=0.25
    )
    target = FinancialMetrics(
        ticker="TGT",
        share_price=50.0,
        diluted_shares=20000000.0,  # 20M shares
        net_income=100000000.0,     # $100M ($5 EPS)
        book_value_net_assets=500000000.0,
        effective_tax_rate=0.25
    )
    params = DealInputParams(
        acquirer_ticker="ACQ",
        target_ticker="TGT",
        offer_premium_pct=20.0,     # Offer price = $60
        cash_pct=50.0,              # $600M
        debt_pct=30.0,              # $360M
        stock_pct=20.0,             # $240M
        cost_of_debt_pct=6.0,
        foregone_interest_rate_pct=2.0,
        synergies_pre_tax=50000000.0 # $50M
    )

    res = calculate_merger_math(acquirer, target, params)
    
    assert res["offer_price"] == 60.0
    assert res["purchase_equity_value"] == 1200000000.0 # $1.2B
    assert res["cash_used"] == 600000000.0
    assert res["debt_raised"] == 360000000.0
    assert res["stock_value"] == 240000000.0
    assert res["new_shares_issued"] == 1200000.0       # 1.2M shares @ $200
    assert res["pro_forma_shares"] == 51200000.0
    
    # Net interest = ($360M * 6%) + ($600M * 2%) = $21.6M + $12M = $33.6M
    assert pytest.approx(res["net_interest_burden"], 0.01) == 33600000.0

def test_negative_net_income_distressed_target():
    """Verify accretion/dilution math for a target with negative net income (distressed target)."""
    acquirer = FinancialMetrics(
        ticker="ACQ",
        share_price=100.0,
        diluted_shares=100000000.0,
        net_income=1000000000.0,
        book_value_net_assets=5000000000.0,
        effective_tax_rate=0.20
    )
    target = FinancialMetrics(
        ticker="DISTRESSED",
        share_price=10.0,
        diluted_shares=10000000.0,
        net_income=-50000000.0,     # -$50M loss
        book_value_net_assets=50000000.0,
        effective_tax_rate=0.20
    )
    params = DealInputParams(
        acquirer_ticker="ACQ",
        target_ticker="DISTRESSED",
        offer_premium_pct=0.0,
        cash_pct=100.0,
        debt_pct=0.0,
        stock_pct=0.0,
        cost_of_debt_pct=5.0,
        foregone_interest_rate_pct=2.0,
        synergies_pre_tax=100000000.0 # $100M pre-tax synergies
    )

    res = calculate_merger_math(acquirer, target, params)
    
    # Pre-tax net interest = $100M cash * 2% = $2M
    # Post-tax synergies & interest = ($100M - $2M) * (1 - 0.2) = $78.4M
    # Pro-forma Net Income = $1000M + (-$50M) + $78.4M = $1028.4M
    assert pytest.approx(res["pro_forma_net_income"], 0.01) == 1028400000.0
    assert res["pro_forma_eps"] > res["standalone_eps"] # Accretive deal

