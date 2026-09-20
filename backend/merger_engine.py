from typing import Dict, Any
from backend.models import FinancialMetrics, DealInputParams

def calculate_merger_math(
    acquirer: FinancialMetrics,
    target: FinancialMetrics,
    params: DealInputParams
) -> Dict[str, Any]:
    """
    Deterministic Financial M&A Merger Mechanics Engine (Professional CA / CFA / IB Grade).
    Executes transaction sizing, balance sheet adjustments, PPA Goodwill & DTL derivation,
    income consolidation, EPS accretion/dilution, credit leverage analysis, and breakeven synergy solving.
    """
    # 1. Offer & Transaction Sizing (Public vs Private Target Support)
    offer_premium_decimal = params.offer_premium_pct / 100.0
    offer_price = target.share_price * (1.0 + offer_premium_decimal)
    
    if params.target_equity_value_override and params.target_equity_value_override > 0:
        purchase_equity_value = params.target_equity_value_override * (1.0 + offer_premium_decimal)
    else:
        purchase_equity_value = offer_price * target.diluted_shares
    
    # 2. Purchase Price Allocation (PPA), Asset Step-Ups & Deferred Tax Liabilities (DTL)
    # DTL Created = Asset Step-Up * Tax Rate
    tax_rate = acquirer.effective_tax_rate
    step_up = params.identifiable_intangibles_step_up
    dtl_created = step_up * tax_rate
    
    # Goodwill Created = max(0, Purchase Equity Value - (Target Book Value + Step-Up - DTL Created))
    net_identifiable_assets = target.book_value_net_assets + step_up - dtl_created
    goodwill_created = max(0.0, purchase_equity_value - net_identifiable_assets)
    
    # 3. Consideration Mix & Balance Sheet Adjustments
    cash_decimal = params.cash_pct / 100.0
    debt_decimal = params.debt_pct / 100.0
    stock_decimal = params.stock_pct / 100.0
    
    # Normalize consideration percentages if they don't sum to 100%
    total_pct = params.cash_pct + params.debt_pct + params.stock_pct
    if total_pct > 0 and abs(total_pct - 100.0) > 1e-4:
        cash_decimal = (params.cash_pct / total_pct)
        debt_decimal = (params.debt_pct / total_pct)
        stock_decimal = (params.stock_pct / total_pct)
        
    cash_used = purchase_equity_value * cash_decimal
    debt_raised = purchase_equity_value * debt_decimal
    stock_value = purchase_equity_value * stock_decimal
    
    new_shares_issued = stock_value / acquirer.share_price
    pro_forma_shares = acquirer.diluted_shares + new_shares_issued
    
    # 4. Income Consolidation & Accretion/Dilution
    cost_of_debt_decimal = params.cost_of_debt_pct / 100.0
    foregone_interest_decimal = params.foregone_interest_rate_pct / 100.0
    
    net_interest_burden = (debt_raised * cost_of_debt_decimal) + (cash_used * foregone_interest_decimal)
    post_tax_synergy_adj = (params.synergies_pre_tax - net_interest_burden) * (1.0 - tax_rate)
    
    pro_forma_net_income = acquirer.net_income + target.net_income + post_tax_synergy_adj
    
    standalone_eps = acquirer.net_income / acquirer.diluted_shares
    pro_forma_eps = pro_forma_net_income / pro_forma_shares
    
    if standalone_eps != 0:
        accretion_dilution_pct = ((pro_forma_eps - standalone_eps) / abs(standalone_eps)) * 100.0
    else:
        accretion_dilution_pct = 0.0

    # 5. Pro-Forma Credit Profile & Debt Covenants (EBITDA, Leverage & Interest Coverage)
    acquirer_ebitda = params.acquirer_ebitda_override or (acquirer.ebitda if acquirer.ebitda and acquirer.ebitda > 0 else max(1.0, acquirer.net_income * 1.35))
    target_ebitda = params.target_ebitda_override or (target.ebitda if target.ebitda and target.ebitda > 0 else max(1.0, target.net_income * 1.35))
    
    pro_forma_ebitda = acquirer_ebitda + target_ebitda + params.synergies_pre_tax
    pro_forma_total_debt = acquirer.total_debt + target.total_debt + debt_raised
    
    pro_forma_leverage_ratio = pro_forma_total_debt / max(1.0, pro_forma_ebitda)
    interest_coverage_ratio = pro_forma_ebitda / max(1.0, net_interest_burden)
    
    if pro_forma_leverage_ratio < 3.0:
        leverage_status = "GREEN (Investment Grade < 3.0x)"
    elif pro_forma_leverage_ratio <= 4.5:
        leverage_status = "AMBER (Moderate Leverage 3.0x - 4.5x)"
    else:
        leverage_status = "RED (High Debt Breach > 4.5x)"

    # 6. Breakeven Pre-Tax Synergies Solver
    target_pro_forma_ni = standalone_eps * pro_forma_shares
    breakeven_synergies = ((target_pro_forma_ni - acquirer.net_income - target.net_income) / (1.0 - tax_rate)) + net_interest_burden

    return {
        "acquirer_ticker": acquirer.ticker,
        "target_ticker": target.ticker,
        "acquirer_share_price": acquirer.share_price,
        "target_share_price": target.share_price,
        "offer_premium_pct": params.offer_premium_pct,
        "offer_price": offer_price,
        "purchase_equity_value": purchase_equity_value,
        "goodwill_created": goodwill_created,
        "identifiable_intangibles_step_up": step_up,
        "dtl_created": dtl_created,
        "cash_pct": params.cash_pct,
        "debt_pct": params.debt_pct,
        "stock_pct": params.stock_pct,
        "cash_used": cash_used,
        "debt_raised": debt_raised,
        "stock_value": stock_value,
        "new_shares_issued": new_shares_issued,
        "acquirer_diluted_shares": acquirer.diluted_shares,
        "pro_forma_shares": pro_forma_shares,
        "net_interest_burden": net_interest_burden,
        "synergies_pre_tax": params.synergies_pre_tax,
        "post_tax_synergies": post_tax_synergy_adj,
        "acquirer_net_income": acquirer.net_income,
        "target_net_income": target.net_income,
        "pro_forma_net_income": pro_forma_net_income,
        "standalone_eps": standalone_eps,
        "pro_forma_eps": pro_forma_eps,
        "accretion_dilution_pct": accretion_dilution_pct,
        "breakeven_synergies": breakeven_synergies,
        "effective_tax_rate": tax_rate,
        "acquirer_ebitda": acquirer_ebitda,
        "target_ebitda": target_ebitda,
        "pro_forma_ebitda": pro_forma_ebitda,
        "pro_forma_total_debt": pro_forma_total_debt,
        "pro_forma_leverage_ratio": round(pro_forma_leverage_ratio, 2),
        "interest_coverage_ratio": round(interest_coverage_ratio, 2),
        "leverage_status": leverage_status
    }
