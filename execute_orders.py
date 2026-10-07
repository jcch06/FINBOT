"""
=============================================================================
TIER 3: DETERMINISTIC RISK ENGINE & BROKER EXECUTION (ALPACA OMS)
=============================================================================
Auteur       : Quantitative Research & Portfolio Architecture Agent
Description  : Lit le batch d'ordres validés par le Risk Engine
               (executed_orders_batch.json), ordonnance les ventes en premier
               pour libérer du cash, puis soumet les ordres d'achat fractionnés
               à l'API Alpaca Paper Trading.
=============================================================================
"""

import os
import sys
import json
import logging
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AlpacaExecutor")

def execute_orders_on_alpaca(batch_file: str = "executed_orders_batch.json", dry_run: bool = False):
    if not os.path.exists(batch_file):
        logger.info(f"{batch_file} non trouvé. Génération via risk_engine_oms.py...")
        from risk_engine_oms import RiskEngineOMS
        oms = RiskEngineOMS(broker="ALPACA", execution_mode="SYNTHETIC_MOC")
        audit = oms.run_full_pre_trade_audit()
        with open(batch_file, "w") as f:
            json.dump(audit, f, indent=2)

    with open(batch_file, "r") as f:
        batch = json.load(f)

    orders = batch.get("order_tickets", [])
    logger.info(f"Chargement de {len(orders)} tickets d'ordres pré-validés.")

    api_key = os.getenv("APCA_API_KEY_ID")
    api_secret = os.getenv("APCA_API_SECRET_KEY")
    base_url = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")

    if not api_key or not api_secret or dry_run:
        logger.warning("Clés Alpaca absentes ou mode DRY-RUN activé. Simulation d'exécution des ordres :")
        for o in orders:
            logger.info(f"  [SIMULATED] {o['side']:4s} {o['executed_shares']:>7.3f} {o['symbol']:<5s} (~${o['estimated_notional_usd']:>7.2f}) | {o['order_type']} | {o['notes']}")
        return

    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce

    client = TradingClient(api_key, api_secret, paper=True)

    # IMPORTANT : Exécuter les VENTES en premier pour libérer le pouvoir d'achat !
    sell_orders = [o for o in orders if o["side"] == "SELL"]
    buy_orders = [o for o in orders if o["side"] == "BUY"]
    ordered_sequence = sell_orders + buy_orders

    logger.info(f"Lancement de l'exécution séquentielle : {len(sell_orders)} Ventes, puis {len(buy_orders)} Achats.")

    results = []
    for o in ordered_sequence:
        symbol = o["symbol"]
        side_str = o["side"].lower()
        qty = round(o["executed_shares"], 4)

        try:
            logger.info(f"Envoi ordre : {side_str.upper()} {qty} {symbol} à Alpaca...")
            order_data = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide.BUY if side_str == "buy" else OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            order_res = client.submit_order(order_data)
            logger.info(f"  -> SUCCESS : Order ID {order_res.id} ({order_res.status})")
            results.append({
                "symbol": symbol,
                "order_id": str(order_res.id),
                "status": str(order_res.status),
                "qty": qty,
                "side": side_str.upper(),
                "created_at": str(order_res.created_at)
            })
        except Exception as e:
            logger.error(f"Erreur d'envoi pour {symbol}: {e}")
            results.append({
                "symbol": symbol,
                "status": "ERROR",
                "error": str(e)
            })

    # Sauvegarder le journal d'exécution
    with open("broker_execution_receipts.json", "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Exécution terminée. Reçus enregistrés dans broker_execution_receipts.json ({len(results)} ordres traités).")

if __name__ == "__main__":
    is_dry = "--dry-run" in sys.argv
    execute_orders_on_alpaca(dry_run=is_dry)
