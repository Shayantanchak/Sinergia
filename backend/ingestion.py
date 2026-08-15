import yfinance as yf
from typing import Optional, Dict
from backend.models import FinancialMetrics

def fetch_company_financials(ticker_symbol: str, overrides: Optional[Dict[str, float]] = None) -> FinancialMetrics:
    """
    Automated 3-statement financial data fetcher via yfinance with validation boundaries.
    Applies overrides if supplied, and standardizes fallback defaults for missing reporting items.
    """
    ticker_clean = ticker_symbol.strip().upper()
    
    data = {
        "ticker": ticker_clean,
        "company_name": ticker_clean,
        "share_price": 100.0,
        "diluted_shares": 100000000.0,
        "net_income": 1000000000.0,
        "total_debt": 0.0,
        "cash_and_equivalents": 500000000.0,
        "book_value_net_assets": 5000000000.0,
        "effective_tax_rate": 0.21
    }
    
    try:
        yf_ticker = yf.Ticker(ticker_clean)
        info = yf_ticker.info or {}
        
        # Company name
        data["company_name"] = info.get("shortName") or info.get("longName") or ticker_clean
        
        # Share Price
        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        if not price or price <= 0:
            fast_info = getattr(yf_ticker, "fast_info", {})
            price = fast_info.get("lastPrice") or fast_info.get("previousClose")
        if price and price > 0:
            data["share_price"] = float(price)
            
        # Shares Outstanding
        shares = info.get("sharesOutstanding") or info.get("impliedSharesOutstanding")
        if shares and shares > 0:
            data["diluted_shares"] = float(shares)
            
        # Net Income
        net_inc = info.get("netIncomeToCommon") or info.get("operatingCashflow")
        if net_inc is not None:
            data["net_income"] = float(net_inc)
            
        # Debt & Cash
        total_debt = info.get("totalDebt")
        if total_debt is not None and total_debt >= 0:
            data["total_debt"] = float(total_debt)
            
        cash = info.get("totalCash")
        if cash is not None and cash >= 0:
            data["cash_and_equivalents"] = float(cash)
            
        # Book Value of Net Assets (Total Stockholder Equity)
        book_val = info.get("bookValue")
        if book_val and data["diluted_shares"] > 0:
            data["book_value_net_assets"] = float(book_val) * data["diluted_shares"]
        else:
            total_assets = info.get("totalAssets")
            total_liab = info.get("totalLiab")
            if total_assets and total_liab:
                data["book_value_net_assets"] = float(total_assets - total_liab)
                
        # Tax Rate standardization
        # Fallback to standard 21% US corporate tax rate if missing or out of bounds
        tax_rate = 0.21
        try:
            financials = yf_ticker.financials
            if financials is not None and not financials.empty:
                if "Tax Provision" in financials.index and "Pretax Income" in financials.index:
                    tax_prov = financials.loc["Tax Provision"].iloc[0]
                    pretax = financials.loc["Pretax Income"].iloc[0]
                    if pretax and pretax > 0 and tax_prov is not None:
                        calc_rate = float(tax_prov / pretax)
                        if 0.0 <= calc_rate <= 0.5:
                            tax_rate = calc_rate
        except Exception:
            pass
        data["effective_tax_rate"] = tax_rate
        
    except Exception as e:
        print(f"Warning: yfinance fetch failed for {ticker_clean} ({e}). Using robust defaults.")

    # Apply manual user overrides if supplied
    if overrides:
        for k, v in overrides.items():
            if k in data and v is not None:
                data[k] = v

    # Enforce validation boundaries via Pydantic model
    validated_metrics = FinancialMetrics(**data)
    return validated_metrics
