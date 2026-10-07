import sys
import os
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (America/New_York) %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("RebalancePipeline")

def check_market_session():
    """
    Checks New York market time and verifies if we are within the pre-close execution window.
    """
    ny_tz = ZoneInfo("America/New_York")
    now_ny = datetime.now(ny_tz)
    weekday = now_ny.weekday()  # 0 = Monday, 4 = Friday

    logger.info(f"Current Wall Street Time: {now_ny.strftime('%Y-%m-%d %H:%M:%S %Z')} (Weekday: {weekday})")

    # Check weekend
    if weekday >= 5:
        logger.warning("Markets are closed (Weekend). Running in SIMULATION / AUDIT mode.")
        return False, now_ny

    # Standard trading session: 09:30 to 16:00 ET
    market_open = now_ny.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now_ny.replace(hour=16, minute=0, second=0, microsecond=0)
    rebalance_window_start = now_ny.replace(hour=15, minute=30, second=0, microsecond=0)

    if rebalance_window_start <= now_ny <= market_close:
        logger.info(f"PERFECT EXECUTION WINDOW: Between 15:30 and 16:00 ET. Pre-close MOC processing active.")
        return True, now_ny
    else:
        logger.info(f"Outside standard 15:30-16:00 ET window. Running pipeline in DRY-RUN / AUDIT mode.")
        return False, now_ny

def main():
    logger.info("==========================================================")
    logger.info("STARTING QUANTITATIVE PORTFOLIO REBALANCE PIPELINE")
    logger.info("Universe: AI Infrastructure (Compute) | Energy (Power) | Robotics | Biotech")
    logger.info("==========================================================")

    # 1. Market Time & DST Verification
    is_live_window, now_ny = check_market_session()

    # Model selector from CLI
    model_override = None
    if "--pro" in sys.argv:
        model_override = "gemini-2.5-pro"
    elif "--flash" in sys.argv:
        model_override = "gemini-2.5-flash"

    # 2. Tier 1: Deterministic Data Ingestion (build_dossier.py)
    logger.info("[Tier 1] Ingesting market data & Alpaca account state (build_dossier.py)...")
    from build_dossier import build_instruction_dossier
    dossier = build_instruction_dossier("dossier.json")
    logger.info(f"[Tier 1 Complete] Dossier compiled for {len(dossier['candidate_universe'])} sectors.")

    # 3. Tier 2: Analytical Reasoning & Allocation Engine (run_agent.py)
    logger.info("[Tier 2] Running Analytical Reasoning Agent (Gemini Flash/Pro hybrid)...")
    from run_agent import run_agent_reasoning
    payload = run_agent_reasoning(
        dossier_file="dossier.json",
        output_payload_file="oms_payload.json",
        model_override=model_override
    )

    summary = payload["portfolio_summary"]
    logger.info(f"Target Allocation: Invested {summary['proposed_invested_capital_ratio']*100:.1f}%, Cash {summary['proposed_cash_ratio']*100:.1f}%, Positions: {summary['active_positions_count']}")

    # 4. Tier 3: Downstream Risk Engine & Order Generation
    logger.info("[Tier 3] Processing Risk Engine & OMS Order Delta Generator...")
    from risk_engine_oms import RiskEngineOMS

    broker_target = os.getenv("BROKER_TARGET", "ALPACA")
    execution_mode = os.getenv("EXECUTION_MODE", "SYNTHETIC_MOC")
    logger.info(f"Broker configuration: {broker_target} | Execution Mode: {execution_mode}")

    oms = RiskEngineOMS(
        portfolio_state_file="portfolio_state.json",
        allocation_payload_file="oms_payload.json",
        broker=broker_target,
        execution_mode=execution_mode,
        max_consolidated_ai_cap=0.70,
        rebalance_drift_threshold=0.0075
    )

    audit_result = oms.run_full_pre_trade_audit()

    logger.info("----------------------------------------------------------")
    logger.info("RISK ENGINE & OMS PRE-TRADE AUDIT RESULTS:")
    sector = audit_result["sector_audit"]
    logger.info(f"  Sector Compute: {sector['compute_weight']*100:.1f}%")
    logger.info(f"  Sector Power:   {sector['power_weight']*100:.1f}%")
    logger.info(f"  Sector Robotics:{sector['robotics_weight']*100:.1f}%")
    logger.info(f"  Sector Biotech: {sector.get('biotech_weight', 0.0)*100:.1f}%")
    logger.info(f"  Consolidated AI Infrastructure (Compute + Power): {sector['consolidated_ai_datacenter']*100:.1f}% (Cap: {sector['cap_limit']*100:.1f}%) -> {sector['status']}")
    logger.info(f"  Orders generated: {audit_result['total_orders_generated']}")
    logger.info(f"  Total BUY Notional:  ${audit_result['total_buy_notional_usd']:,.2f}")
    logger.info(f"  Total SELL Notional: ${audit_result['total_sell_notional_usd']:,.2f}")
    logger.info(f"  Net Cash Impact:     ${audit_result['net_capital_flow_usd']:,.2f}")
    logger.info("----------------------------------------------------------")

    with open("executed_orders_batch.json", "w") as f:
        json.dump(audit_result, f, indent=2)

    logger.info("Order tickets batch saved to executed_orders_batch.json.")

    # 5. Broker Execution (si drapeau --execute ou variable AUTO_EXECUTE=true)
    auto_execute = ("--execute" in sys.argv) or (os.getenv("AUTO_EXECUTE", "false").lower() == "true")
    if auto_execute and audit_result.get("total_orders_generated", 0) > 0:
        logger.info("[Tier 3 Execution] Envoi des ordres à Alpaca Paper Trading...")
        from execute_orders import execute_orders_on_alpaca
        execute_orders_on_alpaca("executed_orders_batch.json", dry_run=False)

    logger.info("PIPELINE EXECUTION FINISHED SUCCESSFULLY.")
    logger.info("==========================================================")

if __name__ == "__main__":
    main()
