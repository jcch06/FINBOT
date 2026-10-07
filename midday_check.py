"""
=============================================================================
MIDDAY RISK SENTINEL & POSITION HEALTH CHECK
=============================================================================
Auteur       : Quantitative Risk Architecture Agent
Description  : Interroge les positions ouvertes sur Alpaca Paper Trading
               en milieu de séance (12h30 ET / 18h30 Paris), calcule les
               P&L temps réel, surveille les distances aux Stop-Loss / Take-Profit,
               et coupe immédiatement toute ligne qui franchit son stop.
=============================================================================
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MiddaySentinel")

def run_midday_check(payload_file: str = "oms_payload.json", auto_exit_on_stop: bool = True):
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce

    api_key = os.getenv("APCA_API_KEY_ID")
    api_secret = os.getenv("APCA_API_SECRET_KEY")

    if not api_key or not api_secret:
        logger.error("Clés API Alpaca absentes dans l'environnement !")
        return

    client = TradingClient(api_key, api_secret, paper=True)
    account = client.get_account()
    positions = client.get_all_positions()

    total_equity = float(account.equity)
    cash_balance = float(account.cash)

    logger.info(f"Connexion Alpaca : Capital = ${total_equity:,.2f} | Cash = ${cash_balance:,.2f}")
    logger.info(f"Positions ouvertes : {len(positions)} lignes actives")

    # Charger les niveaux de risque depuis le payload OMS
    risk_map = {}
    if os.path.exists(payload_file):
        with open(payload_file, "r", encoding="utf-8") as f:
            oms_data = json.load(f)
            for alloc in oms_data.get("allocations", []):
                risk_map[alloc["ticker"]] = alloc.get("risk_parameters", {})

    report_lines = []
    total_unrealized_pl = 0.0
    alerts = []
    actions_taken = []

    for p in positions:
        sym = p.symbol
        qty = float(p.qty)
        entry_px = float(p.avg_entry_price)
        curr_px = float(p.current_price)
        pl_usd = float(p.unrealized_pl)
        pl_pct = float(p.unrealized_plpc) * 100.0
        total_unrealized_pl += pl_usd

        rp = risk_map.get(sym, {})
        stop_px = float(rp.get("stop_loss_price", 0.0))
        dist_to_stop_pct = ((curr_px - stop_px) / curr_px * 100.0) if (curr_px > 0 and stop_px > 0) else None

        tp_ladder = rp.get("profit_taking_ladder", [])
        tp1 = float(tp_ladder[0]["target_price"]) if len(tp_ladder) > 0 else 0.0
        dist_to_tp1_pct = ((tp1 - curr_px) / curr_px * 100.0) if (curr_px > 0 and tp1 > 0) else None

        status = "SAFE"
        if stop_px > 0 and curr_px <= stop_px:
            status = "STOP_BREACHED"
            alerts.append(f"[ALERTE STOP] {sym} a touché son stop-loss à {curr_px:.2f}$ (Stop: {stop_px:.2f}$)")
            if auto_exit_on_stop:
                try:
                    logger.warning(f"Exécution immédiate d'un ordre EXIT d'urgence pour {sym} ({qty} actions)...")
                    order_data = MarketOrderRequest(
                        symbol=sym,
                        qty=round(qty, 4),
                        side=OrderSide.SELL,
                        time_in_force=TimeInForce.DAY
                    )
                    res = client.submit_order(order_data)
                    actions_taken.append({
                        "symbol": sym,
                        "action": "EMERGENCY_STOP_EXIT",
                        "order_id": str(res.id),
                        "shares": qty,
                        "price": curr_px
                    })
                    status = "STOPPED_OUT_EXECUTED"
                except Exception as e:
                    logger.error(f"Erreur d'envoi de l'ordre d'urgence pour {sym}: {e}")
        elif dist_to_stop_pct is not None and dist_to_stop_pct < 2.5:
            status = "NEAR_STOP_WARNING"
            alerts.append(f"[ATTENTION] {sym} est proche de son stop-loss (Marge: {dist_to_stop_pct:.1f}%)")
        elif tp1 > 0 and curr_px >= tp1:
            status = "TARGET_1_HIT"
            alerts.append(f"[TAKE PROFIT] {sym} a atteint son Take-Profit 1 à {curr_px:.2f}$ (Cible: {tp1:.2f}$)")

        report_lines.append({
            "symbol": sym,
            "shares": round(qty, 4),
            "entry_price": round(entry_px, 2),
            "current_price": round(curr_px, 2),
            "unrealized_pl_usd": round(pl_usd, 2),
            "unrealized_pl_pct": round(pl_pct, 2),
            "stop_loss_price": round(stop_px, 2),
            "margin_to_stop_pct": round(dist_to_stop_pct, 1) if dist_to_stop_pct is not None else None,
            "take_profit_1": round(tp1, 2),
            "status": status
        })

    # Affichage console
    ny_tz = ZoneInfo("America/New_York")
    now_ny = datetime.now(ny_tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"\n==========================================================================")
    print(f"RAPPORT MIDDAY SENTINEL - HEURE NEW YORK : {now_ny}")
    print(f"Total Equity : ${total_equity:,.2f} | Cash : ${cash_balance:,.2f} | P&L Global : {total_unrealized_pl:+,.2f}$")
    print(f"==========================================================================")
    print(f"{'SYM':<5} | {'PRIX':>7} | {'ENTRÉE':>7} | {'P&L ($)':>8} | {'P&L (%)':>7} | {'STOP':>7} | {'MARGE STOP':>10} | {'STATUT':<15}")
    print(f"--------------------------------------------------------------------------")
    for r in report_lines:
        marge_str = f"{r['margin_to_stop_pct']:+5.1f}%" if r['margin_to_stop_pct'] is not None else "N/A"
        print(f"{r['symbol']:<5} | {r['current_price']:>7.2f} | {r['entry_price']:>7.2f} | {r['unrealized_pl_usd']:>+7.2f}$ | {r['unrealized_pl_pct']:>+6.2f}% | {r['stop_loss_price']:>7.2f} | {marge_str:>10} | {r['status']:<15}")
    print(f"==========================================================================\n")

    summary_result = {
        "check_timestamp": datetime.now(timezone.utc).isoformat(),
        "wall_street_time": now_ny,
        "total_equity": total_equity,
        "cash_balance": cash_balance,
        "total_unrealized_pl_usd": round(total_unrealized_pl, 2),
        "positions_count": len(positions),
        "alerts": alerts,
        "actions_taken": actions_taken,
        "positions": report_lines
    }

    with open("midday_report.json", "w", encoding="utf-8") as f:
        json.dump(summary_result, f, indent=2)

    # Écriture dans le GitHub Actions Step Summary si dans CI
    github_summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if github_summary_file:
        with open(github_summary_file, "a", encoding="utf-8") as gf:
            gf.write(f"### 🛡️ Midday Risk Sentinel Report ({now_ny})\n\n")
            gf.write(f"- **Total Equity** : `${total_equity:,.2f}`\n")
            gf.write(f"- **Cash Réserve** : `${cash_balance:,.2f}`\n")
            gf.write(f"- **P&L Non-Réalisé Net** : `{total_unrealized_pl:+,.2f}$`\n\n")
            gf.write("| Symbole | Cours | Entrée | P&L ($) | P&L (%) | Stop-Loss | Marge Stop | Statut |\n")
            gf.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")
            for r in report_lines:
                marge_s = f"{r['margin_to_stop_pct']:+.1f}%" if r['margin_to_stop_pct'] is not None else "N/A"
                badge = "🟢 SAFE" if r['status'] == 'SAFE' else ("🔴 " + r['status'])
                gf.write(f"| **{r['symbol']}** | {r['current_price']:.2f}$ | {r['entry_price']:.2f}$ | {r['unrealized_pl_usd']:+.2f}$ | {r['unrealized_pl_pct']:+.2f}% | {r['stop_loss_price']:.2f}$ | {marge_s} | {badge} |\n")
            if alerts:
                gf.write("\n#### ⚠️ Alertes Détectées\n")
                for a in alerts:
                    gf.write(f"- {a}\n")

if __name__ == "__main__":
    run_midday_check()
