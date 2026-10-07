import json
import math
from typing import Dict, Any, List

class RiskEngineOMS:
    """
    Deterministic Risk Engine & Order Management System (OMS)
    Bridges Antigravity Allocation Payloads and Broker Execution (IBKR / Alpaca).
    """

    def __init__(
        self,
        portfolio_state_file: str = "portfolio_state.json",
        allocation_payload_file: str = "oms_payload.json",
        broker: str = "ALPACA",  # "ALPACA" or "IBKR"
        execution_mode: str = "SYNTHETIC_MOC",  # "SYNTHETIC_MOC" (15:55 Market) or "NATIVE_MOC"
        max_consolidated_ai_cap: float = 0.70,  # Max combined Compute + Power (e.g. 70%)
        rebalance_drift_threshold: float = 0.0075  # 0.75% drift buffer to avoid churn on HOLD
    ):
        with open(portfolio_state_file, "r") as f:
            self.portfolio_state = json.load(f)

        with open(allocation_payload_file, "r") as f:
            self.allocation_payload = json.load(f)

        self.broker = broker.upper()
        self.execution_mode = execution_mode.upper()
        self.max_consolidated_ai_cap = max_consolidated_ai_cap
        self.rebalance_drift_threshold = rebalance_drift_threshold

        self.equity = self.portfolio_state["total_equity"]
        self.current_positions = self.portfolio_state.get("positions", {})
        self.allocations = self.allocation_payload["allocations"]
        self.alerts = []
        self.order_tickets = []

    def check_sector_risk_gate(self) -> Dict[str, float]:
        """
        Control 2: Evaluates consolidated sector / factor exposure.
        Enforces maximum consolidated CapEx exposure (Compute + Power).
        """
        sector_weights = {"COMPUTE": 0.0, "POWER": 0.0, "ROBOTICS": 0.0, "BIOTECH": 0.0}
        for item in self.allocations:
            if item["action"] in ["BUY_NEW", "ADD", "HOLD", "TRIM"]:
                sec = item.get("sector_bucket", "UNKNOWN")
                if sec in sector_weights:
                    sector_weights[sec] += item["target_weight"]

        consolidated_ai = sector_weights["COMPUTE"] + sector_weights["POWER"]
        report = {
            "compute_weight": round(sector_weights["COMPUTE"], 4),
            "power_weight": round(sector_weights["POWER"], 4),
            "robotics_weight": round(sector_weights["ROBOTICS"], 4),
            "biotech_weight": round(sector_weights["BIOTECH"], 4),
            "consolidated_ai_datacenter": round(consolidated_ai, 4),
            "cap_limit": self.max_consolidated_ai_cap,
            "status": "PASS" if consolidated_ai <= self.max_consolidated_ai_cap else "WARNING_OVER_CAP"
        }

        if consolidated_ai > self.max_consolidated_ai_cap:
            self.alerts.append({
                "type": "SECTOR_CONCENTRATION_WARNING",
                "message": f"Consolidated Compute + Power exposure is {consolidated_ai*100:.1f}%, exceeding configured cap of {self.max_consolidated_ai_cap*100:.1f}%."
            })

        return report

    def generate_orders(self) -> List[Dict[str, Any]]:
        """
        Controls 1 & 3: Calculates net order deltas, handles fractional sizing and broker constraints.
        """
        self.order_tickets = []

        # Load price reference from allocations
        with open("universe_analysis.csv", "r") as f:
            import pandas as pd
            df_univ = pd.read_csv("universe_analysis.csv").set_index("ticker")

        for alloc in self.allocations:
            ticker = alloc["ticker"]
            action = alloc["action"]
            target_weight = alloc["target_weight"]

            # Current state
            pos_info = self.current_positions.get(ticker, {})
            current_shares = pos_info.get("shares", 0.0)
            current_price = df_univ.loc[ticker, "price"] if ticker in df_univ.index else pos_info.get("current_price", 0.0)

            target_notional = target_weight * self.equity
            current_notional = current_shares * current_price
            current_weight = current_notional / self.equity if self.equity > 0 else 0.0

            # 1. HOLD Idempotency
            if action == "HOLD":
                weight_drift = abs(target_weight - current_weight)
                if weight_drift < self.rebalance_drift_threshold:
                    # Suppress order execution: no churn
                    continue

            # 2. Complete Liquidations (EXIT)
            if action == "EXIT":
                if current_shares > 0.0001:
                    ticket = self._build_ticket(
                        ticker=ticker,
                        side="SELL",
                        shares=current_shares,
                        price=current_price,
                        action_origin="EXIT",
                        note="Full position liquidation"
                    )
                    self.order_tickets.append(ticket)
                continue

            # 3. New Buys, Adds, Trims
            target_shares = target_notional / current_price if current_price > 0 else 0.0
            delta_shares = target_shares - current_shares

            # Check if order is economically significant (> $10 or > 0.001 shares)
            if abs(delta_shares * current_price) < 10.0:
                continue

            if delta_shares > 0:
                side = "BUY"
                qty = delta_shares
            else:
                side = "SELL"
                qty = abs(delta_shares)

            ticket = self._build_ticket(
                ticker=ticker,
                side=side,
                shares=qty,
                price=current_price,
                action_origin=action,
                note=f"Weight shift {current_weight*100:.2f}% -> {target_weight*100:.2f}%"
            )
            self.order_tickets.append(ticket)

        return self.order_tickets

    def _build_ticket(self, ticker: str, side: str, shares: float, price: float, action_origin: str, note: str) -> Dict[str, Any]:
        """
        Formats order ticket with broker-specific fractional & execution rules.
        """
        is_fractional = (shares % 1 != 0)
        notional_usd = round(shares * price, 2)

        order_type = "MOC"
        routing_notes = []

        if self.broker == "ALPACA":
            # Alpaca natively supports fractional market orders
            rounded_shares = round(shares, 4)
            order_type = "MARKET"  # Alpaca handles fractional via market orders
            routing_notes.append("Alpaca fractional API compatible")

        elif self.broker == "IBKR":
            if self.execution_mode == "NATIVE_MOC":
                if is_fractional:
                    # Native MOC on NYSE/NASDAQ requires integer shares
                    rounded_shares = round(shares)
                    routing_notes.append(f"Rounded from {shares:.4f} to whole share {rounded_shares} for native MOC")
                    if rounded_shares == 0:
                        rounded_shares = 1 if side == "BUY" else 0
                        routing_notes.append("Floor adjusted to 1 whole share")
                else:
                    rounded_shares = shares
            else:
                # SYNTHETIC_MOC: Send standard Market order at 15:55 EST (5 min before close)
                rounded_shares = round(shares, 4)
                order_type = "MARKET_CLOSE_WINDOW_1555"
                routing_notes.append("Routed via IBKR fractional Market Order at 15:55 EST (Synthetic MOC)")

        return {
            "symbol": ticker,
            "side": side,
            "action_origin": action_origin,
            "requested_shares": round(shares, 4),
            "executed_shares": rounded_shares,
            "estimated_price": round(price, 2),
            "estimated_notional_usd": round(rounded_shares * price, 2),
            "order_type": order_type,
            "routing": " | ".join(routing_notes),
            "notes": note
        }

    def run_full_pre_trade_audit(self) -> Dict[str, Any]:
        sector_audit = self.check_sector_risk_gate()
        orders = self.generate_orders()

        total_buy_notional = sum(o["estimated_notional_usd"] for o in orders if o["side"] == "BUY")
        total_sell_notional = sum(o["estimated_notional_usd"] for o in orders if o["side"] == "SELL")
        net_flow = total_buy_notional - total_sell_notional

        return {
            "account_equity": self.equity,
            "sector_audit": sector_audit,
            "total_orders_generated": len(orders),
            "total_buy_notional_usd": round(total_buy_notional, 2),
            "total_sell_notional_usd": round(total_sell_notional, 2),
            "net_capital_flow_usd": round(net_flow, 2),
            "alerts": self.alerts,
            "order_tickets": orders
        }

if __name__ == "__main__":
    print("=== TEST 1: ALPACA EXECUTION (FRACTIONAL NATIVE) ===")
    oms_alpaca = RiskEngineOMS(broker="ALPACA", execution_mode="SYNTHETIC_MOC")
    audit_alpaca = oms_alpaca.run_full_pre_trade_audit()
    print(f"Orders count: {audit_alpaca['total_orders_generated']}")
    print(f"Total BUY notional: ${audit_alpaca['total_buy_notional_usd']}")
    print(f"Total SELL notional: ${audit_alpaca['total_sell_notional_usd']}")
    print(f"Net flow: ${audit_alpaca['net_capital_flow_usd']}")
    for o in audit_alpaca["order_tickets"]:
        print(f"  [{o['action_origin']:7s}] {o['side']:4s} {o['executed_shares']:>7.3f} {o['symbol']:<4s} (~${o['estimated_notional_usd']:>7.2f}) | {o['order_type']} | {o['routing']}")

    print("\n=== TEST 2: IBKR SYNTHETIC MOC (15:55 EST FRACTIONAL ROUTING) ===")
    oms_ibkr = RiskEngineOMS(broker="IBKR", execution_mode="SYNTHETIC_MOC")
    audit_ibkr = oms_ibkr.run_full_pre_trade_audit()
    with open("executed_orders_batch.json", "w") as f:
        json.dump(audit_ibkr, f, indent=2)
    print("Saved executed_orders_batch.json successfully!")
