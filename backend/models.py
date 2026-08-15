from typing import Optional, Any, Dict, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Column, JSON

def utc_now():
    return datetime.now(timezone.utc)

class DealRecord(SQLModel, table=True):
    __tablename__ = "deal_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    
    # Ticker symbols
    acquirer_ticker: str = Field(index=True)
    target_ticker: str = Field(index=True)
    
    # Input Transaction Terms
    offer_premium_pct: float
    cash_pct: float
    debt_pct: float
    stock_pct: float
    cost_of_debt_pct: float
    foregone_interest_rate_pct: float
    synergies_pre_tax: float
    
    # Financial Output Summary
    acquirer_share_price: float
    target_share_price: float
    offer_price: float
    purchase_equity_value: float
    goodwill_created: float
    net_interest_burden: float
    post_tax_synergies: float
    pro_forma_net_income: float
    standalone_eps: float
    pro_forma_eps: float
    accretion_dilution_pct: float
    breakeven_synergies: float
    
    # Full JSON payloads (Inputs, Financial Statements, 2D Sensitivity Matrix)
    inputs_json: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    outputs_json: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    sensitivity_matrix_json: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

class FinancialMetrics(SQLModel):
    """Pydantic model for company 3-statement financial inputs and validation boundaries"""
    ticker: str
    company_name: Optional[str] = "Unknown"
    share_price: float = Field(..., gt=0, description="Share price must be > 0")
    diluted_shares: float = Field(..., gt=0, description="Diluted shares must be > 0")
    net_income: float = Field(..., description="Net Income (can be positive or negative)")
    total_debt: float = Field(0.0, ge=0, description="Total debt must be >= 0")
    cash_and_equivalents: float = Field(0.0, ge=0, description="Cash & equivalents must be >= 0")
    book_value_net_assets: float = Field(..., description="Target Book Value of Net Assets for Goodwill calculation")
    effective_tax_rate: float = Field(0.21, ge=0.0, le=0.5, description="Tax rate in range [0.0, 0.5]")

class DealInputParams(SQLModel):
    acquirer_ticker: str = "AAPL"
    target_ticker: str = "NVDA"
    offer_premium_pct: float = Field(20.0, ge=0.0, le=200.0) # e.g. 20%
    cash_pct: float = Field(50.0, ge=0.0, le=100.0)
    debt_pct: float = Field(0.0, ge=0.0, le=100.0)
    stock_pct: float = Field(50.0, ge=0.0, le=100.0)
    cost_of_debt_pct: float = Field(5.0, ge=0.0, le=20.0)
    foregone_interest_rate_pct: float = Field(2.5, ge=0.0, le=15.0)
    synergies_pre_tax: float = Field(50000000.0, ge=0.0) # $50M pre-tax synergies
    
    # Optional override metrics if yfinance is offline or custom input specified
    acquirer_overrides: Optional[Dict[str, float]] = None
    target_overrides: Optional[Dict[str, float]] = None
