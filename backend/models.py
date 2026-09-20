from typing import Optional, Any, Dict, List
from datetime import datetime, timezone
from enum import Enum
import uuid
from sqlmodel import SQLModel, Field, Column, JSON

def utc_now():
    return datetime.now(timezone.utc)

class UserTier(str, Enum):
    PERSONAL = "personal"
    PROFESSIONAL = "professional"
    MNC_FIRM = "mnc_firm"

class UserRole(str, Enum):
    ADMIN = "admin"
    MODELER = "modeler"
    VIEWER = "viewer"

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    full_name: str
    organization_name: Optional[str] = None
    tier: UserTier = Field(default=UserTier.PERSONAL)
    role: UserRole = Field(default=UserRole.MODELER)
    
    # MFA Settings
    mfa_enabled: bool = Field(default=False)
    totp_secret: Optional[str] = None
    backup_codes: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Profile & Preferences
    theme_preference: str = Field(default="dark")
    default_currency: str = Field(default="USD")
    default_tax_rate: float = Field(default=0.21)
    accounting_standard: str = Field(default="US_GAAP")
    created_at: datetime = Field(default_factory=utc_now)

class DealRecord(SQLModel, table=True):
    __tablename__ = "deal_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    user_id: Optional[str] = Field(default=None, foreign_key="users.id", index=True)
    
    # Ticker symbols / Entity Names
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
    
    # Extended Professional Outputs (CA / CFA / IB)
    dtl_created: float = Field(default=0.0)
    pro_forma_leverage_ratio: float = Field(default=0.0)
    interest_coverage_ratio: float = Field(default=0.0)
    
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
    ebitda: Optional[float] = Field(default=0.0, description="EBITDA metric for leverage & coverage ratios")

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
    
    # Extended Accounting & Valuation Inputs (Phase 7: CA / CFA)
    identifiable_intangibles_step_up: float = Field(0.0, ge=0.0, description="Asset step-up revaluation")
    target_equity_value_override: Optional[float] = Field(default=None, description="Direct valuation for unlisted/private targets")
    acquirer_ebitda_override: Optional[float] = Field(default=None)
    target_ebitda_override: Optional[float] = Field(default=None)
    
    # Optional override metrics if yfinance is offline or custom input specified
    acquirer_overrides: Optional[Dict[str, float]] = None
    target_overrides: Optional[Dict[str, float]] = None

class MLPredictionRequest(SQLModel):
    acquirer_ticker: str = "MSFT"
    target_ticker: str = "ATVI"
    target_revenue: float = Field(..., gt=0)
    target_market_cap: float = Field(..., gt=0)
    sector: Optional[str] = "Technology"

class MLPredictionResponse(SQLModel):
    acquirer_ticker: str
    target_ticker: str
    predicted_synergy_median: float
    predicted_synergy_min: float
    predicted_synergy_max: float
    predicted_synergy_pct_revenue: float
    recommended_offer_premium_pct: float
    regulatory_risk_score_pct: float
    regulatory_risk_status: str
    model_confidence_score: float

class MonteCarloInputParams(SQLModel):
    acquirer_ticker: str = "MSFT"
    target_ticker: str = "ATVI"
    num_simulations: int = Field(10000, ge=100, le=50000)
    synergies_mean: float = Field(50000000.0, ge=0.0)
    synergies_std_dev: float = Field(15000000.0, ge=0.0)
    cost_of_debt_mean_pct: float = Field(5.0, ge=0.0)
    cost_of_debt_std_dev_pct: float = Field(1.0, ge=0.0)
    offer_premium_pct: float = Field(20.0, ge=0.0)
    cash_pct: float = Field(50.0, ge=0.0)
    debt_pct: float = Field(0.0, ge=0.0)
    stock_pct: float = Field(50.0, ge=0.0)
    acquirer_overrides: Optional[Dict[str, float]] = None
    target_overrides: Optional[Dict[str, float]] = None

class MonteCarloResult(SQLModel):
    num_simulations: int
    mean_accretion_pct: float
    median_accretion_pct: float
    std_dev_accretion_pct: float
    probability_of_accretion_pct: float
    var_90_accretion_pct: float
    var_95_accretion_pct: float
    var_99_accretion_pct: float
    percentiles: Dict[str, float]
    simulation_histogram: Dict[str, Any]

class MultiYearInputParams(SQLModel):
    acquirer_ticker: str = "MSFT"
    target_ticker: str = "ATVI"
    forecast_years: int = Field(3, ge=1, le=5)
    synergy_ramp_up: List[float] = Field(default_factory=lambda: [0.33, 0.66, 1.00])
    acquirer_revenue_growth_pct: float = Field(5.0)
    target_revenue_growth_pct: float = Field(8.0)
    offer_premium_pct: float = 20.0
    cash_pct: float = 50.0
    debt_pct: float = 0.0
    stock_pct: float = 50.0
    synergies_steady_state_pre_tax: float = 50000000.0
    acquirer_overrides: Optional[Dict[str, float]] = None
    target_overrides: Optional[Dict[str, float]] = None

class MultiYearYearResult(SQLModel):
    year: int
    synergy_ramp_pct: float
    realized_synergies_pre_tax: float
    acquirer_net_income: float
    target_net_income: float
    pro_forma_net_income: float
    pro_forma_eps: float
    accretion_dilution_pct: float
    leverage_ratio: float

class MultiYearResult(SQLModel):
    acquirer_ticker: str
    target_ticker: str
    forecast_years: int
    yearly_projections: List[MultiYearYearResult]

