import pytest
from pydantic import ValidationError
from backend.models import FinancialMetrics
from backend.ingestion import fetch_company_financials
from backend.database import engine, init_db, get_session
from sqlmodel import Session

def test_phase1_environment_and_db_engine():
    """Verify database initialization and SQLModel engine connection."""
    init_db()
    with Session(engine) as session:
        assert session.is_active

def test_phase1_ingestion_validation_boundaries():
    """Verify Pydantic validation boundaries on FinancialMetrics model."""
    # 1. Valid metrics
    metrics = FinancialMetrics(
        ticker="AAPL",
        share_price=150.0,
        diluted_shares=15000000000.0,
        net_income=90000000000.0,
        total_debt=100000000000.0,
        cash_and_equivalents=60000000000.0,
        book_value_net_assets=60000000000.0,
        effective_tax_rate=0.21
    )
    assert metrics.share_price > 0
    assert metrics.diluted_shares > 0
    assert metrics.total_debt >= 0
    assert 0.0 <= metrics.effective_tax_rate <= 0.5

    # 2. Invalid Share Price (<= 0)
    with pytest.raises(ValidationError):
        FinancialMetrics(
            ticker="BAD",
            share_price=0.0,
            diluted_shares=100.0,
            net_income=100.0,
            book_value_net_assets=100.0
        )

    # 3. Invalid Diluted Shares (<= 0)
    with pytest.raises(ValidationError):
        FinancialMetrics(
            ticker="BAD",
            share_price=10.0,
            diluted_shares=-5.0,
            net_income=100.0,
            book_value_net_assets=100.0
        )

    # 4. Invalid Tax Rate (> 0.5)
    with pytest.raises(ValidationError):
        FinancialMetrics(
            ticker="BAD",
            share_price=10.0,
            diluted_shares=100.0,
            net_income=100.0,
            book_value_net_assets=100.0,
            effective_tax_rate=0.75
        )

def test_phase1_ingestion_yfinance_fetch_and_fallbacks():
    """Verify automated yfinance retrieval and robust fallback defaults."""
    # Test with standard ticker
    metrics = fetch_company_financials("MSFT")
    assert metrics.ticker == "MSFT"
    assert metrics.share_price > 0
    assert metrics.diluted_shares > 0
    assert 0.0 <= metrics.effective_tax_rate <= 0.5

    # Test with manual overrides
    overrides = {"share_price": 420.0, "effective_tax_rate": 0.18}
    custom_metrics = fetch_company_financials("MSFT", overrides=overrides)
    assert custom_metrics.share_price == 420.0
    assert custom_metrics.effective_tax_rate == 0.18
