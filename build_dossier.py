"""
=============================================================================
TIER 1: DETERMINISTIC DATA INGESTION ENGINE (THE DOSSIER BUILDER)
=============================================================================
Auteur       : Quantitative Research & Portfolio Architecture Agent
Description  : Récupère les données de marché (yfinance, pandas-ta), les
               fondamentaux & dates de résultats, et l'état du compte (Alpaca API)
               afin de compiler un "Instruction Dossier" (dossier.json) rigide et
               vérifié pour l'agent de raisonnement Antigravity / Gemini Pro.
=============================================================================
"""

import os
import sys
import json
import logging
from datetime import datetime, date, timezone
from typing import Dict, Any, Optional, List
import requests
import pandas as pd
import numpy as np
import yfinance as yf
from dotenv import load_dotenv

# Charger les variables du fichier .env
load_dotenv()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("DossierBuilder")

# 1. Univers d'investissement par défaut et chargement dynamique depuis watchlist.json
DEFAULT_UNIVERSE: Dict[str, list] = {
    "COMPUTE": ["NVDA", "TSM", "AVGO", "MRVL", "ANET", "VRT", "ARM", "MU", "AMD", "CLS", "NBIS"],
    "POWER": ["CEG", "VST", "GEV", "TLN", "NRG", "NEE", "ETN", "CCJ", "SMR", "OKLO"],
    "ROBOTICS": ["ISRG", "SYM", "TER", "ROK", "ZBRA", "PATH", "SERV", "ONDS", "RKLB"]
}

def get_target_universe() -> Dict[str, list]:
    """
    Charge la watchlist dynamique mise à jour par screener.py (watchlist.json),
    ou utilise l'univers par défaut.
    """
    watchlist_file = "watchlist.json"
    if os.path.exists(watchlist_file):
        try:
            with open(watchlist_file, "r", encoding="utf-8") as f:
                wl = json.load(f)
                if isinstance(wl, dict) and len(wl) > 0:
                    logger.info(f"Watchlist dynamique chargée depuis {watchlist_file} ({sum(len(v) for v in wl.values())} tickers).")
                    return wl
        except Exception as e:
            logger.warning(f"Impossible de lire {watchlist_file} : {e}")
    return DEFAULT_UNIVERSE

USER_LONG_TERM_PORTFOLIO = []

# Configuration des en-têtes SEC EDGAR
SEC_EDGAR_IDENTITY = os.getenv("SEC_EDGAR_IDENTITY", "UserAgent: AntigravityBot admin@quantportfolio.internal")


def fetch_alpaca_account_context() -> Dict[str, Any]:
    """
    Interroge l'API Alpaca Paper Trading pour récupérer l'état actuel du compte
    (total_equity, cash disponible, positions ouvertes) via alpaca-py.
    Si les clés API ne sont pas présentes, bascule sur portfolio_state.json local.
    """
    api_key = os.getenv("APCA_API_KEY_ID")
    api_secret = os.getenv("APCA_API_SECRET_KEY")

    if api_key and api_secret:
        try:
            logger.info("Connexion à l'API Alpaca Paper Trading via alpaca-py...")
            from alpaca.trading.client import TradingClient
            client = TradingClient(api_key=api_key, secret_key=api_secret, paper=True)
            account = client.get_account()

            equity = float(account.equity)
            cash = float(account.cash)

            positions_data = client.get_all_positions()
            positions = {}
            for p in positions_data:
                sym = p.symbol
                qty = float(p.qty)
                current_price = float(p.current_price)
                market_val = float(p.market_value)
                cost_basis = float(p.cost_basis)
                unrealized_pl = float(p.unrealized_pl)
                unrealized_plpc = float(p.unrealized_plpc)

                positions[sym] = {
                    "shares": round(qty, 4),
                    "current_price": round(current_price, 2),
                    "market_value_usd": round(market_val, 2),
                    "cost_basis_usd": round(cost_basis, 2),
                    "current_weight": round(market_val / equity, 4) if equity > 0 else 0.0,
                    "unrealized_pl_usd": round(unrealized_pl, 2),
                    "unrealized_pl_pct": round(unrealized_plpc * 100.0, 2)
                }

            logger.info(f"Alpaca connecté : Capital = ${equity:,.2f}, Cash = ${cash:,.2f}, Lignes = {len(positions)}")
            alpaca_state = {
                "source": "ALPACA_PAPER_API",
                "total_equity": round(equity, 2),
                "cash_balance": round(cash, 2),
                "cash_ratio": round(cash / equity, 4) if equity > 0 else 0.0,
                "active_positions_count": len(positions),
                "positions": positions
            }
            try:
                with open("portfolio_state.json", "w") as pf:
                    json.dump(alpaca_state, pf, indent=2)
            except Exception as e_save:
                logger.warning(f"Impossible d'enregistrer portfolio_state.json: {e_save}")
            return alpaca_state
        except Exception as e:
            logger.warning(f"Erreur d'accès à Alpaca API ({e}). Repli sur portfolio_state.json local.")

    # Repli local
    local_file = "portfolio_state.json"
    if os.path.exists(local_file):
        with open(local_file, "r") as f:
            local_state = json.load(f)
        equity = local_state.get("total_equity", 10000.0)
        cash = local_state.get("cash_balance", 1200.0)
        positions = local_state.get("positions", {})
        return {
            "source": "LOCAL_PORTFOLIO_STATE",
            "total_equity": round(equity, 2),
            "cash_balance": round(cash, 2),
            "cash_ratio": round(cash / equity, 4) if equity > 0 else 0.0,
            "active_positions_count": len(positions),
            "positions": positions
        }

    # Valeur par défaut
    return {
        "source": "DEFAULT_FALLBACK",
        "total_equity": 10000.0,
        "cash_balance": 10000.0,
        "cash_ratio": 1.0,
        "active_positions_count": 0,
        "positions": {}
    }


def compute_market_technicals(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Calcule les indicateurs techniques obligatoires (RSI Wilder, ATR, EMA, SMA, RVOL)
    sur les 120 dernières barres journalières OHLCV.
    Utilise pandas-ta si présent, ou fallback optimisé pandas/numpy vectorisé.
    """
    if len(df) < 50:
        return None

    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']

    # 1. RSI(14) lissage de Wilder (Wilder's Smoothing)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_14 = 100.0 - (100.0 / (1.0 + rs))

    # 2. True Range & ATR(14) / ATR(20)
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr_14 = tr.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    atr_20 = tr.ewm(alpha=1/20, min_periods=20, adjust=False).mean()

    # 3. Moyennes Mobiles
    ema_20 = close.ewm(span=20, adjust=False).mean()
    sma_50 = close.rolling(window=50).mean()
    sma_200 = close.rolling(window=200).mean() if len(df) >= 200 else pd.Series(np.nan, index=df.index)

    # 4. Volume relatif 30 jours (RVOL)
    vol_mean_30 = volume.rolling(window=30).mean()
    rvol_30 = volume / vol_mean_30.replace(0, np.nan)

    # Valeurs courantes
    curr_close = float(close.iloc[-1])
    curr_rsi = float(rsi_14.iloc[-1])
    curr_atr14 = float(atr_14.iloc[-1])
    curr_atr20 = float(atr_20.iloc[-1])
    curr_ema20 = float(ema_20.iloc[-1])
    curr_sma50 = float(sma_50.iloc[-1])
    curr_sma200 = float(sma_200.iloc[-1]) if not np.isnan(sma_200.iloc[-1]) else None
    curr_rvol = float(rvol_30.iloc[-1])

    # Distance normalisée à l'EMA20
    dist_ema20_pct = ((curr_close - curr_ema20) / curr_ema20) * 100.0
    dist_ema20_atr = ((curr_close - curr_ema20) / curr_atr14) if curr_atr14 > 0 else 0.0

    # Distance minimale du Stop Loss = 1.8 * ATR(14)
    min_stop_distance = 1.8 * curr_atr14
    suggested_hard_stop = curr_close - min_stop_distance

    # Critères de surachat / extension
    is_rsi_overbought = curr_rsi > 72.0
    is_atr_extended = dist_ema20_atr > 2.8
    is_pct_extended = dist_ema20_pct > 25.0
    is_extended = is_rsi_overbought or is_atr_extended or is_pct_extended

    return {
        "current_price": round(curr_close, 2),
        "rsi_14": round(curr_rsi, 2),
        "atr_14": round(curr_atr14, 2),
        "atr_20": round(curr_atr20, 2),
        "ema_20": round(curr_ema20, 2),
        "sma_50": round(curr_sma50, 2),
        "sma_200": round(curr_sma200, 2) if curr_sma200 else None,
        "rvol_30": round(curr_rvol, 2),
        "dist_ema20_pct": round(dist_ema20_pct, 2),
        "dist_ema20_atr": round(dist_ema20_atr, 2),
        "min_stop_distance": round(min_stop_distance, 2),
        "suggested_hard_stop": round(suggested_hard_stop, 2),
        "is_extended": bool(is_extended),
        "extension_flags": {
            "rsi_overbought": bool(is_rsi_overbought),
            "atr_extended": bool(is_atr_extended),
            "pct_extended": bool(is_pct_extended)
        }
    }


def fetch_fundamentals_and_calendar(ticker_obj: yf.Ticker, curr_price: float) -> Dict[str, Any]:
    """
    Récupère les métriques fondamentales, le consensus Wall Street et la date
    du prochain rapport d'annonces de résultats (Earnings).
    """
    info = ticker_obj.info or {}

    # 1. Calendrier des résultats & Flag 72h
    next_earnings = None
    days_to_earnings = None
    earnings_risk_flag = "NORMAL"

    cal = ticker_obj.calendar
    if isinstance(cal, dict) and "Earnings Date" in cal:
        ed_val = cal["Earnings Date"]
        if isinstance(ed_val, list) and len(ed_val) > 0:
            next_earnings = ed_val[0]
        elif isinstance(ed_val, (datetime, date)):
            next_earnings = ed_val

    if next_earnings:
        if isinstance(next_earnings, datetime):
            ed_date = next_earnings.date()
        else:
            ed_date = next_earnings
        today_date = datetime.now(timezone.utc).date()
        days_to_earnings = (ed_date - today_date).days

        # Flag si <= 72h (3 jours)
        if 0 <= days_to_earnings <= 3:
            earnings_risk_flag = "HIGH_RISK_EARNINGS_LEAP"
        elif days_to_earnings < 0:
            earnings_risk_flag = "RECENTLY_REPORTED"

    # 2. Métriques financières
    gross_margin = info.get("grossMargins")
    rev_growth = info.get("revenueGrowth")
    fwd_pe = info.get("forwardPE")
    target_mean = info.get("targetMeanPrice")
    target_high = info.get("targetHighPrice")
    target_low = info.get("targetLowPrice")
    rec_key = info.get("recommendationKey", "none")

    upside_pct = None
    if target_mean and curr_price > 0:
        upside_pct = round(((target_mean - curr_price) / curr_price) * 100.0, 2)

    return {
        "calendar_risk": {
            "next_earnings_date": str(next_earnings) if next_earnings else None,
            "days_to_earnings": days_to_earnings,
            "earnings_risk_flag": earnings_risk_flag
        },
        "financial_metrics": {
            "gross_margin_ttm": round(gross_margin, 4) if gross_margin is not None else None,
            "revenue_growth_yoy": round(rev_growth, 4) if rev_growth is not None else None,
            "forward_pe": round(fwd_pe, 2) if fwd_pe is not None else None,
            "analyst_target_mean": round(target_mean, 2) if target_mean is not None else None,
            "analyst_target_high": round(target_high, 2) if target_high is not None else None,
            "analyst_target_low": round(target_low, 2) if target_low is not None else None,
            "upside_to_mean_pct": upside_pct,
            "consensus_recommendation": rec_key
        }
    }


def fetch_tavily_catalysts(ticker: str) -> List[Dict[str, str]]:
    """
    Interroge l'API Tavily pour extraire les actualités financières en temps réel et catalyseurs récents.
    Consomme 1 crédit Tavily par ticker interrogé.
    """
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key or tavily_key.startswith("tvly-..."):
        return []

    try:
        logger.info(f"Recherche Web Tavily en direct pour {ticker}...")
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": tavily_key,
                "query": f"{ticker} stock earnings contracts catalysts news 2026",
                "search_depth": "basic",
                "max_results": 3
            },
            timeout=8
        )
        if resp.status_code == 200:
            data = resp.json()
            articles = []
            for item in data.get("results", []):
                articles.append({
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "snippet": item.get("content", "")[:280]
                })
            logger.info(f"  -> Tavily : {len(articles)} articles pertinents trouvés pour {ticker}")
            return articles
    except Exception as e:
        logger.warning(f"Erreur de recherche Tavily sur {ticker} : {e}")
    return []


def fetch_institutional_and_options_layer(ticker_obj: yf.Ticker, sym: str) -> Dict[str, Any]:
    """
    Extrait les flux d'options (Put/Call ratio, Volume, Open Interest)
    et les flux d'actionnariat institutionnel (Top détenteurs 13F, % institutionnel).
    """
    options_data = {
        "options_available": False,
        "front_expiration": None,
        "call_volume": 0,
        "put_volume": 0,
        "put_call_volume_ratio": None,
        "call_open_interest": 0,
        "put_open_interest": 0,
        "put_call_oi_ratio": None,
        "options_sentiment": "NO_OPTIONS_DATA"
    }

    try:
        expirations = ticker_obj.options
        if expirations and len(expirations) > 0:
            front_exp = expirations[0]
            chain = ticker_obj.option_chain(front_exp)
            calls = chain.calls
            puts = chain.puts

            call_vol = int(calls["volume"].fillna(0).sum()) if not calls.empty else 0
            put_vol = int(puts["volume"].fillna(0).sum()) if not puts.empty else 0
            call_oi = int(calls["openInterest"].fillna(0).sum()) if not calls.empty else 0
            put_oi = int(puts["openInterest"].fillna(0).sum()) if not puts.empty else 0

            pc_vol_ratio = round(put_vol / call_vol, 2) if call_vol > 0 else None
            pc_oi_ratio = round(put_oi / call_oi, 2) if call_oi > 0 else None

            if pc_vol_ratio is not None:
                if pc_vol_ratio <= 0.60:
                    sentiment = "STRONG_BULLISH_CALL_DOMINANCE"
                elif pc_vol_ratio <= 0.85:
                    sentiment = "MODERATE_BULLISH"
                elif pc_vol_ratio <= 1.15:
                    sentiment = "NEUTRAL_BALANCED"
                else:
                    sentiment = "BEARISH_PUT_DOMINANCE"
            else:
                sentiment = "BALANCED"

            options_data = {
                "options_available": True,
                "front_expiration": str(front_exp),
                "call_volume": call_vol,
                "put_volume": put_vol,
                "put_call_volume_ratio": pc_vol_ratio,
                "call_open_interest": call_oi,
                "put_open_interest": put_oi,
                "put_call_oi_ratio": pc_oi_ratio,
                "options_sentiment": sentiment
            }
    except Exception as e:
        logger.debug(f"Pas de données d'options pour {sym}: {e}")

    institutional_data = {
        "institutional_ownership_pct": None,
        "top_holders": []
    }
    try:
        info = getattr(ticker_obj, "info", None) or {}
        inst_pct = info.get("heldPercentInstitutions")
        if inst_pct is not None:
            institutional_data["institutional_ownership_pct"] = round(inst_pct * 100.0, 2)

        holders_df = ticker_obj.institutional_holders
        if holders_df is not None and not holders_df.empty:
            top_list = []
            for _, row in holders_df.head(3).iterrows():
                holder_name = str(row.get("Holder", ""))
                shares = int(row.get("Shares", 0)) if pd.notnull(row.get("Shares")) else 0
                val = float(row.get("Value", 0)) if pd.notnull(row.get("Value")) else 0
                top_list.append({
                    "holder": holder_name,
                    "shares": shares,
                    "value_usd": round(val, 2)
                })
            institutional_data["top_holders"] = top_list
    except Exception as e:
        logger.debug(f"Erreur d'actionnariat pour {sym}: {e}")

    return {
        "options_flow_layer": options_data,
        "institutional_ownership_layer": institutional_data
    }


def build_instruction_dossier(output_file: str = "dossier.json") -> Dict[str, Any]:
    """
    Fonction principale assemblant le dossier d'instructions exhaustif.
    """
    logger.info("Démarrage de la construction du dossier d'instructions quantitatif...")
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1. Contexte du compte et des liquidités
    account_context = fetch_alpaca_account_context()

    # 2. Analyse quantitative de l'univers
    candidate_universe: Dict[str, Dict[str, Any]] = {}

    active_universe = get_target_universe()
    for sector, tickers in active_universe.items():
        candidate_universe[sector] = {}
        for sym in tickers:
            logger.info(f"Traitement du ticker : {sym:<5} ({sector})")
            try:
                t = yf.Ticker(sym)
                # 120 barres journalières OHLCV
                df = t.history(period="120d", interval="1d")
                if df.empty or len(df) < 50:
                    logger.warning(f"Données insuffisantes pour {sym}")
                    continue

                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [col[0] for col in df.columns]

                # Couche technique
                technicals = compute_market_technicals(df)
                if not technicals:
                    continue

                # Couche fondamentale & calendrier
                fund_cal = fetch_fundamentals_and_calendar(t, technicals["current_price"])

                # Couche de renseignement Web en direct via Tavily (catalyseurs récents)
                news_catalysts = []
                if sym in USER_LONG_TERM_PORTFOLIO:
                    news_catalysts = fetch_tavily_catalysts(sym)

                # Couche Flux d'Options & Actionnariat Institutionnel
                inst_opt = fetch_institutional_and_options_layer(t, sym)

                candidate_universe[sector][sym] = {
                    "sector": sector,
                    "market_technical_layer": technicals,
                    "calendar_layer": fund_cal["calendar_risk"],
                    "fundamental_layer": fund_cal["financial_metrics"],
                    "institutional_and_options_layer": inst_opt,
                    "realtime_web_catalysts": news_catalysts
                }
            except Exception as e:
                logger.error(f"Erreur d'ingestion sur {sym}: {e}")

    dossier = {
        "dossier_timestamp": now_utc,
        "account_context": account_context,
        "candidate_universe": candidate_universe
    }

    # Sauvegarde sur disque
    with open(output_file, "w") as f:
        json.dump(dossier, f, indent=2)

    logger.info(f"Dossier d'instructions sauvegardé avec succès dans '{output_file}'.")
    return dossier


if __name__ == "__main__":
    dossier = build_instruction_dossier("dossier.json")
    print(f"\nRésumé du dossier généré ({dossier['dossier_timestamp']}) :")
    print(f"  - Source compte : {dossier['account_context']['source']}")
    print(f"  - Total Equity  : ${dossier['account_context']['total_equity']:,.2f}")
    print(f"  - Cash Balance  : ${dossier['account_context']['cash_balance']:,.2f} ({dossier['account_context']['cash_ratio']*100:.1f}%)")
    for sec, syms in dossier["candidate_universe"].items():
        print(f"  - {sec:<8}      : {len(syms)} candidats vérifiés")
