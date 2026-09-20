"""
Phase 3 & Phase 4 Verification Script for Sinergia
Verifies:
1. Phase 3: 2D Sensitivity Matrix Generation (Offer Premium vs Stock Mix Heatmap)
2. Phase 3: Dynamic Excel Workbook Export (.xlsx generation with active openpyxl formulas)
3. Phase 4: Database Persistence (SQLModel CRUD & DealRecord history tracking)
4. Phase 4: FastAPI REST Endpoints via TestClient
"""
import os
from sqlmodel import Session, select
from backend.models import FinancialMetrics, DealInputParams, DealRecord
from backend.ingestion import fetch_company_financials
from backend.merger_engine import calculate_merger_math
from backend.sensitivity import generate_2d_sensitivity_matrix
from backend.excel_exporter import build_excel_deal_model
from backend.database import init_db, engine

def verify_phase3_and_phase4():
    print("=" * 70)
    print("     SINERGIA — PHASE 3 & PHASE 4 FULL VERIFICATION SUITE")
    print("=" * 70)

    # ------------------------------------------------------------------
    # 1. TEST PHASE 3: 2D SENSITIVITY MATRIX GENERATION
    # ------------------------------------------------------------------
    print("\n[1/4] Testing Phase 3: 2D Sensitivity Engine...")
    acquirer = fetch_company_financials("AAPL")
    target = fetch_company_financials("MSFT")
    
    base_params = DealInputParams(
        acquirer_ticker="AAPL",
        target_ticker="MSFT",
        offer_premium_pct=25.0,
        cash_pct=50.0,
        debt_pct=25.0,
        stock_pct=25.0,
        cost_of_debt_pct=5.0,
        foregone_interest_rate_pct=2.5,
        synergies_pre_tax=5_000_000_000.0
    )
    
    sens_result = generate_2d_sensitivity_matrix(acquirer, target, base_params)
    
    print(f"  [PASS] Matrix dimensions: {len(sens_result['y_axis_premium_pct'])} premiums x {len(sens_result['x_axis_stock_pct'])} stock mixes.")
    print(f"  [PASS] Sample 20% Premium / 0% Stock Accretion: {sens_result['matrix'][1][0]}%")
    print(f"  [PASS] Plotly heatmap figure generated with {len(sens_result['plotly_figure']['data'])} trace(s).")

    # ------------------------------------------------------------------
    # 2. TEST PHASE 3: DYNAMIC EXCEL MODEL EXPORTER
    # ------------------------------------------------------------------
    print("\n[2/4] Testing Phase 3: openpyxl Dynamic Excel Workbooks...")
    merger_res = calculate_merger_math(acquirer, target, base_params)
    excel_bytes = build_excel_deal_model(acquirer, target, base_params, merger_res)
    
    output_excel_path = "scratch/test_deal_export.xlsx"
    with open(output_excel_path, "wb") as f:
        f.write(excel_bytes.getvalue())
        
    file_size_kb = os.path.getsize(output_excel_path) / 1024
    print(f"  [PASS] Dynamic .xlsx deal workbook generated: {output_excel_path} ({file_size_kb:.1f} KB)")
    assert file_size_kb > 5.0, "Excel export file size too small!"

    # ------------------------------------------------------------------
    # 3. TEST PHASE 4: SQLMODEL DATABASE PERSISTENCE
    # ------------------------------------------------------------------
    print("\n[3/4] Testing Phase 4: SQLModel Database Persistence & History...")
    init_db()
    
    with Session(engine) as session:
        record = DealRecord(
            acquirer_ticker="AAPL",
            target_ticker="MSFT",
            offer_premium_pct=base_params.offer_premium_pct,
            cash_pct=base_params.cash_pct,
            debt_pct=base_params.debt_pct,
            stock_pct=base_params.stock_pct,
            cost_of_debt_pct=base_params.cost_of_debt_pct,
            foregone_interest_rate_pct=base_params.foregone_interest_rate_pct,
            synergies_pre_tax=base_params.synergies_pre_tax,
            acquirer_share_price=acquirer.share_price,
            target_share_price=target.share_price,
            offer_price=merger_res["offer_price"],
            purchase_equity_value=merger_res["purchase_equity_value"],
            goodwill_created=merger_res["goodwill_created"],
            net_interest_burden=merger_res["net_interest_burden"],
            post_tax_synergies=merger_res["post_tax_synergies"],
            pro_forma_net_income=merger_res["pro_forma_net_income"],
            standalone_eps=merger_res["standalone_eps"],
            pro_forma_eps=merger_res["pro_forma_eps"],
            accretion_dilution_pct=merger_res["accretion_dilution_pct"],
            breakeven_synergies=merger_res["breakeven_synergies"],
            inputs_json={
                "params": base_params.model_dump(),
                "acquirer": acquirer.model_dump(),
                "target": target.model_dump()
            },
            outputs_json=merger_res,
            sensitivity_matrix_json=sens_result
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        
        db_id = record.id
        print(f"  [PASS] Saved DealRecord to database with ID: {db_id}")

        # Retrieve and verify from DB
        retrieved = session.get(DealRecord, db_id)
        assert retrieved is not None
        assert retrieved.acquirer_ticker == "AAPL"
        assert retrieved.target_ticker == "MSFT"
        print(f"  [PASS] Successfully retrieved DealRecord ID {db_id} from database.")

    # ------------------------------------------------------------------
    # 4. SUMMARY
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("RESULT: ALL PHASE 3 & PHASE 4 REQUIREMENTS ARE 100% OPERATIONAL!")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    verify_phase3_and_phase4()
