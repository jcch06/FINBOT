"""
=============================================================================
DAILY QUANTITATIVE MARKET SCREENER & WATCHLIST DYNAMIC UPDATER
=============================================================================
Auteur       : Quantitative Portfolio Architecture Agent
Description  : Scanne un vivier élargi de ~45 valeurs d'infrastructures IA,
               énergie et robotique, calcule les scores multi-factoriels
               (Technique, Fondamentaux, Volatilité, Extension Anti-FOMO)
               et met à jour dynamiquement watchlist.json pour le bot de trading.
=============================================================================
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DynamicScreener")

# Vivier élargi de 120 candidats à screener (30 par thème)
SCREENER_POOL = {
    "COMPUTE": [
        "NVDA", "TSM", "AVGO", "MRVL", "ANET", "VRT", "ARM", "MU", "AMD", "CLS",
        "NBIS", "PLTR", "ASML", "QCOM", "CRWD", "SMCI", "MSFT", "AMZN", "GOOGL", "META",
        "AAPL", "ORCL", "DELL", "HPE", "CDNS", "WDC", "AMAT", "LRCX", "KLAC", "SNPS"
    ],
    "POWER": [
        "CEG", "VST", "GEV", "TLN", "NRG", "NEE", "ETN", "CCJ", "SMR", "OKLO",
        "BWXT", "NNE", "PWR", "FLR", "DUK", "SO", "AEP", "EXC", "SRE", "HUBB",
        "EMR", "LEU", "UEC", "NXE", "AES", "BE", "XEL", "KMI", "WMB", "PCG"
    ],
    "ROBOTICS": [
        "ISRG", "SYM", "TER", "ROK", "ZBRA", "PATH", "SERV", "ONDS", "RKLB", "ASTS",
        "JOBY", "ACHR", "AUR", "MBLY", "CGNX", "TSLA", "AVAV", "KTOS", "HON", "OUST",
        "INVZ", "AEVA", "KEYS", "ATS", "GXO", "IR", "LUNR", "PL", "LDOS", "AXON",
        "KRKNF"
    ],
    "BIOTECH": [
        "ABCL", "HIMS", "PRME", "CRSP", "BEAM", "NTLA", "EDIT", "DNA", "RXRX", "SDGR",
        "VRTX", "MRNA", "BNTX", "ALNY", "IONS", "BMRN", "INCY", "REGN", "ARGX", "ILMN",
        "PACB", "TXG", "NTRA", "TEM", "CRBU", "ROIV", "KYMR", "ARVN", "RPRX", "BBIO",
        "NAUT"
    ]
}

def compute_technicals(df: pd.DataFrame):
    if len(df) < 50:
        return None

    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']

    # 1. Wilder RSI(14)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_14 = 100.0 - (100.0 / (1.0 + rs))

    # 2. True Range & ATR(14 / 20)
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr_14 = tr.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    atr_20 = tr.ewm(alpha=1/20, min_periods=20, adjust=False).mean()

    # 3. Moyennes mobiles
    ema_20 = close.ewm(span=20, adjust=False).mean()
    sma_50 = close.rolling(window=50).mean()

    curr_close = float(close.iloc[-1])
    curr_rsi = float(rsi_14.iloc[-1])
    curr_atr14 = float(atr_14.iloc[-1])
    curr_atr20 = float(atr_20.iloc[-1])
    curr_ema20 = float(ema_20.iloc[-1])
    curr_sma50 = float(sma_50.iloc[-1]) if not np.isnan(sma_50.iloc[-1]) else curr_ema20

    dist_ema20_atr = ((curr_close - curr_ema20) / curr_atr20) if curr_atr20 > 0 else 0.0
    dist_ema20_pct = ((curr_close - curr_ema20) / curr_ema20) * 100.0

    is_extended = (curr_rsi > 72.0) or (dist_ema20_atr > 2.8)

    return {
        "current_price": round(curr_close, 2),
        "rsi_14": round(curr_rsi, 2),
        "atr_14": round(curr_atr14, 2),
        "dist_ema20_atr": round(dist_ema20_atr, 2),
        "dist_ema20_pct": round(dist_ema20_pct, 2),
        "is_extended": is_extended
    }

def run_screener(top_per_sector: int = 10):
    logger.info("Démarrage du screener quantitatif élargi...")
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    scored_candidates = {"COMPUTE": [], "POWER": [], "ROBOTICS": [], "BIOTECH": []}
    new_watchlist = {"COMPUTE": [], "POWER": [], "ROBOTICS": [], "BIOTECH": []}

    for sector, tickers in SCREENER_POOL.items():
        logger.info(f"Screening du secteur {sector} ({len(tickers)} candidats)...")
        for sym in tickers:
            try:
                t = yf.Ticker(sym)
                df = t.history(period="120d", interval="1d")
                if df.empty or len(df) < 50:
                    continue
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [col[0] for col in df.columns]

                tech = compute_technicals(df)
                if not tech:
                    continue

                info = t.info or {}
                gm = info.get("grossMargins")
                rev_growth = info.get("revenueGrowth")
                target_mean = info.get("targetMeanPrice")
                curr_px = tech["current_price"]

                upside_pct = round(((target_mean - curr_px) / curr_px) * 100.0, 2) if (target_mean and curr_px > 0) else 0.0
                gm_pct = round(gm * 100.0, 1) if gm is not None else 30.0
                growth_pct = round(rev_growth * 100.0, 1) if rev_growth is not None else 10.0

                # Calcul du Score Multi-Factoriel Composite
                # 1. Upside potentiel pondéré (max 50 pts)
                score_upside = min(max(upside_pct, -20.0), 100.0) * 0.4
                # 2. Croissance du CA (max 30 pts)
                score_growth = min(max(growth_pct, -20.0), 150.0) * 0.25
                # 3. Marge brute / Pricing Power (max 20 pts)
                score_margin = min(max(gm_pct, 0.0), 90.0) * 0.25
                # 4. Pénalité sévère si surachat / FOMO (> 72 RSI ou > 2.8 ATR)
                penalty_extended = -50.0 if tech["is_extended"] else 0.0

                composite_score = round(score_upside + score_growth + score_margin + penalty_extended, 2)

                cand = {
                    "ticker": sym,
                    "sector": sector,
                    "price": curr_px,
                    "rsi_14": tech["rsi_14"],
                    "dist_ema20_atr": tech["dist_ema20_atr"],
                    "is_extended": tech["is_extended"],
                    "upside_pct": upside_pct,
                    "gross_margin_pct": gm_pct,
                    "revenue_growth_pct": growth_pct,
                    "composite_score": composite_score
                }
                scored_candidates[sector].append(cand)
            except Exception as e:
                logger.warning(f"Erreur de scan sur {sym}: {e}")

        # Trier par score composite décroissant
        scored_candidates[sector].sort(key=lambda x: x["composite_score"], reverse=True)
        # Sélectionner les meilleurs pour la watchlist active
        top_selected = scored_candidates[sector][:top_per_sector]
        new_watchlist[sector] = [c["ticker"] for c in top_selected]

    # Sauvegarder watchlist.json
    with open("watchlist.json", "w", encoding="utf-8") as f:
        json.dump(new_watchlist, f, indent=2)
    logger.info("Nouvelle watchlist active enregistrée dans watchlist.json.")

    # Sauvegarder screener_results.json complet
    results_payload = {
        "screen_timestamp": now_utc,
        "watchlist": new_watchlist,
        "ranked_candidates": scored_candidates
    }
    with open("screener_results.json", "w", encoding="utf-8") as f:
        json.dump(results_payload, f, indent=2)

    # Affichage Console du Classement
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

    print("\n================================================================================")
    print("CLASSEMENT DU SCREENER QUANTITATIF (TOP VALEURS SÉLECTIONNÉES POUR LA WATCHLIST)")
    print("================================================================================")
    for sec in ["COMPUTE", "POWER", "ROBOTICS", "BIOTECH"]:
        print(f"\n--- SECTEUR : {sec} ---")
        print(f"{'RANG':<4} | {'SYM':<5} | {'SCORE':>6} | {'PRIX':>7} | {'RSI':>5} | {'DIST EMA':>8} | {'UPSIDE':>7} | {'MARGE':>6} | {'STATUT':<12}")
        print("--------------------------------------------------------------------------------")
        for i, c in enumerate(scored_candidates[sec][:top_per_sector], 1):
            stat = "[EXTENDED]" if c["is_extended"] else "[ELIGIBLE]"
            print(f"{i:<4} | {c['ticker']:<5} | {c['composite_score']:>6.1f} | {c['price']:>7.2f} | {c['rsi_14']:>5.1f} | {c['dist_ema20_atr']:>+7.2f}x | {c['upside_pct']:>+6.1f}% | {c['gross_margin_pct']:>5.1f}% | {stat:<12}")

    # GitHub Actions Step Summary
    gh_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if gh_summary:
        with open(gh_summary, "a", encoding="utf-8") as gf:
            gf.write(f"### 🔍 Daily Market Screener Report ({now_utc})\n\n")
            gf.write(f"Watchlist mise à jour : **{sum(len(v) for v in new_watchlist.values())} actions sélectionnées**.\n\n")
            for sec in ["COMPUTE", "POWER", "ROBOTICS", "BIOTECH"]:
                gf.write(f"#### Secteur : {sec}\n")
                gf.write("| Rang | Ticker | Score | Cours | RSI | Distance EMA | Upside Cible | Marge Brute | Statut |\n")
                gf.write("| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")
                for i, c in enumerate(scored_candidates[sec][:top_per_sector], 1):
                    badge = "🔴 EXTENDED" if c["is_extended"] else "🟢 ELIGIBLE"
                    gf.write(f"| {i} | **{c['ticker']}** | `{c['composite_score']:.1f}` | {c['price']:.2f}$ | {c['rsi_14']:.1f} | {c['dist_ema20_atr']:+.2f}x | {c['upside_pct']:+.1f}% | {c['gross_margin_pct']:.1f}% | {badge} |\n")

    return new_watchlist

if __name__ == "__main__":
    run_screener()
