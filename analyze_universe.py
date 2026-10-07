import yfinance as yf
import pandas as pd
import numpy as np
import json
import warnings
warnings.filterwarnings('ignore')

UNIVERSE = {
    "COMPUTE": ["NVDA", "TSM", "AVGO", "MRVL", "ANET", "VRT", "ARM", "MU", "AMD", "CLS", "NBIS"],
    "POWER": ["CEG", "VST", "GEV", "TLN", "NRG", "NEE", "ETN", "CCJ", "SMR", "OKLO"],
    "ROBOTICS": ["ISRG", "SYM", "TER", "ROK", "ZBRA", "PATH", "SERV", "ONDS", "RKLB"]
}

def analyze_ticker(ticker, sector):
    try:
        t = yf.Ticker(ticker)
        df = t.history(period="1y", interval="1d")
        if df.empty or len(df) < 50:
            return None
        
        # Flatten columns if multiindex
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
            
        close = df['Close']
        high = df['High']
        low = df['Low']
        volume = df['Volume']
        
        # RSI 14
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi_14 = 100 - (100 / (1 + rs))
        
        # ATR 14 & ATR 20
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr_14 = tr.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        atr_20 = tr.ewm(alpha=1/20, min_periods=20, adjust=False).mean()
        
        # Moving averages
        ema_20 = close.ewm(span=20, adjust=False).mean()
        sma_50 = close.rolling(window=50).mean()
        sma_200 = close.rolling(window=200).mean() if len(df) >= 200 else pd.Series(np.nan, index=df.index)
        
        # RVOL 30
        vol_sma_30 = volume.rolling(window=30).mean()
        rvol_30 = volume / vol_sma_30.replace(0, np.nan)
        
        curr_close = float(close.iloc[-1])
        curr_rsi = float(rsi_14.iloc[-1])
        curr_atr14 = float(atr_14.iloc[-1])
        curr_atr20 = float(atr_20.iloc[-1])
        curr_ema20 = float(ema_20.iloc[-1])
        curr_sma50 = float(sma_50.iloc[-1])
        curr_sma200 = float(sma_200.iloc[-1]) if not np.isnan(sma_200.iloc[-1]) else None
        curr_rvol = float(rvol_30.iloc[-1])
        
        dist_ema20_pct = ((curr_close - curr_ema20) / curr_ema20) * 100
        dist_ema20_atr = ((curr_close - curr_ema20) / curr_atr20) if curr_atr20 > 0 else 0
        min_stop_distance = 1.8 * curr_atr14
        
        # Overbought / extended checks
        rsi_extended = curr_rsi > 72.0
        pct_extended = dist_ema20_pct > 25.0
        atr_dist_extended = dist_ema20_atr > 3.0
        is_extended = rsi_extended or pct_extended or atr_dist_extended
        
        # Fundamental info
        info = t.info
        target_mean = info.get('targetMeanPrice')
        gross_margin = info.get('grossMargins')
        rev_growth = info.get('revenueGrowth')
        fwd_pe = info.get('forwardPE')
        market_cap = info.get('marketCap')
        
        # Upside to target
        upside_pct = ((target_mean - curr_close) / curr_close * 100) if target_mean else None
        
        return {
            "ticker": ticker,
            "sector": sector,
            "price": round(curr_close, 2),
            "rsi_14": round(curr_rsi, 2),
            "atr_14": round(curr_atr14, 2),
            "atr_20": round(curr_atr20, 2),
            "ema_20": round(curr_ema20, 2),
            "sma_50": round(curr_sma50, 2),
            "sma_200": round(curr_sma200, 2) if curr_sma200 else None,
            "rvol_30": round(curr_rvol, 2),
            "dist_ema20_pct": round(dist_ema20_pct, 2),
            "dist_ema20_atr": round(dist_ema20_atr, 2),
            "min_stop_dist": round(min_stop_distance, 2),
            "is_extended": is_extended,
            "rsi_extended": rsi_extended,
            "pct_extended": pct_extended,
            "atr_dist_extended": atr_dist_extended,
            "target_mean": round(target_mean, 2) if target_mean else None,
            "upside_pct": round(upside_pct, 2) if upside_pct else None,
            "gross_margin": round(gross_margin, 4) if gross_margin else None,
            "rev_growth": round(rev_growth, 4) if rev_growth else None,
            "fwd_pe": round(fwd_pe, 2) if fwd_pe else None
        }
    except Exception as e:
        print(f"Error {ticker}: {e}")
        return None

def run_analysis():
    results = []
    for sector, tickers in UNIVERSE.items():
        for ticker in tickers:
            res = analyze_ticker(ticker, sector)
            if res:
                results.append(res)
    return results

if __name__ == "__main__":
    res = run_analysis()
    df_res = pd.DataFrame(res)
    df_res.to_csv("universe_analysis.csv", index=False)
    print(df_res[["ticker", "sector", "price", "rsi_14", "dist_ema20_atr", "is_extended", "rvol_30", "target_mean", "upside_pct"]].to_string())
