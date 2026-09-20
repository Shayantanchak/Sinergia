from typing import Dict, Any, List
import copy
import plotly.graph_objects as go
from backend.models import FinancialMetrics, DealInputParams
from backend.merger_engine import calculate_merger_math

def generate_2d_sensitivity_matrix(
    acquirer: FinancialMetrics,
    target: FinancialMetrics,
    base_params: DealInputParams,
    premium_range: List[float] = [10.0, 20.0, 30.0, 40.0, 50.0],
    stock_range: List[float] = [0.0, 25.0, 50.0, 75.0, 100.0]
) -> Dict[str, Any]:
    """
    Constructs a 2D Accretion/Dilution sensitivity matrix:
    Y-Axis: Offer Premium % (10% to 50%)
    X-Axis: % Stock Consideration (0% to 100%)
    Generates interactive color-coded Plotly heatmap data.
    """
    matrix: List[List[float]] = []
    annotations: List[List[str]] = []
    
    for prem in premium_range:
        row: List[float] = []
        ann_row: List[str] = []
        for stock_pct in stock_range:
            # Clone params
            param_copy = base_params.model_copy()
            param_copy.offer_premium_pct = prem
            param_copy.stock_pct = stock_pct
            
            # Adjust remaining consideration between cash and debt
            rem = 100.0 - stock_pct
            if base_params.cash_pct + base_params.debt_pct > 0:
                cash_ratio = base_params.cash_pct / (base_params.cash_pct + base_params.debt_pct)
                param_copy.cash_pct = rem * cash_ratio
                param_copy.debt_pct = rem * (1.0 - cash_ratio)
            else:
                param_copy.cash_pct = rem
                param_copy.debt_pct = 0.0
                
            res = calculate_merger_math(acquirer, target, param_copy)
            acc_pct = round(res["accretion_dilution_pct"], 2)
            row.append(acc_pct)
            
            status = "+" if acc_pct >= 0 else ""
            ann_row.append(f"{status}{acc_pct:.2f}%")
            
        matrix.append(row)
        annotations.append(ann_row)
        
    x_labels = [f"{s:.0f}% Stock" for s in stock_range]
    y_labels = [f"{p:.0f}% Premium" for p in premium_range]
    
    # Custom red-yellow-green colorscale centered around 0%
    colorscale = [
        [0.0, "#d9534f"],   # Red for dilutive
        [0.49, "#f0ad4e"],  # Orange/Yellow near neutral
        [0.5, "#ffffff"],   # White at zero
        [0.51, "#5bc0de"],  # Light blue
        [1.0, "#5cb85c"]    # Green for accretive
    ]

    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=x_labels,
        y=y_labels,
        text=annotations,
        texttemplate="%{text}",
        textfont={"size": 12, "color": "black"},
        colorscale=colorscale,
        colorbar=dict(title="Accretion / Dilution %"),
        zmid=0.0
    ))
    
    fig.update_layout(
        title="2D Sensitivity: Offer Premium vs. % Stock Consideration",
        xaxis_title="% Stock Consideration",
        yaxis_title="Offer Premium %",
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40)
    )

    plotly_dict = fig.to_dict()

    return {
        "x_axis_stock_pct": stock_range,
        "y_axis_premium_pct": premium_range,
        "matrix": matrix,
        "formatted_matrix": annotations,
        "plotly_figure": plotly_dict
    }
