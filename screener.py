import yfinance as yf
import pandas as pd
import numpy as np
import json

TICKERS = {
    "COMPUTE": ["NVDA", "TSM", "AVGO", "MRVL", "ANET", "VRT", "ARM", "MU", "AMD", "CLS"],
    "POWER": ["CEG", "VST", "GEV", "TLN", "NRG", "NEE", "ETN", "CCJ", "SMR", "OKLO"],
    "ROBOTICS": ["SYM", "ISRG", "TER", "ROK", "ZBRA", "SERV", "PATH"]
}

def calculate_technicals(df):
    if len(df) < 50:
        return None
    
    close = df['Close']
    high = df['High']
    low = df['Low']
    volume = df['Volume']
    
    # 14-period RSI
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14, min_periods=14).mean()
    avg_loss = loss.rolling(window=14, min_periods=14).mean()
    
    # Wilder's smoothing
    for i in range(14, len(df)):
        avg_gain.iloc[i] = (avg_gain.iloc[i-1] * 13 + gain.iloc[i]) / 14
        avg_loss.iloc[i] = (avg_loss.iloc[i-1] * 13 + loss.iloc[i]) / 14
        
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_14 = 100 - (100 / (1 + rs))
    
    # True Range & ATR
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr_14 = tr.rolling(window=14).mean()
    atr_20 = tr.rolling(window=20).mean()
    
    # Moving Averages
    ema_20 = close.ewm(span=20, adjust=False).mean()
    sma_50 = close.rolling(window=50).mean()
    sma_200 = close.rolling(window=200).mean() if len(df) >= 200 else pd.Series(np.nan, index=df.index)
    
    # RVOL (30-day Volume Relative Ratio)
    vol_sma_30 = volume.rolling(window=30).mean()
    rvol_30 = volume / vol_sma_30.replace(0, np.nan)
    
    latest_idx = -1
    curr_close = float(close.iloc[latest_idx])
    curr_rsi = float(rsi_14.iloc[latest_idx])
    curr_atr14 = float(atr_14.iloc[latest_idx])
    curr_atr20 = float(atr_20.iloc[latest_idx])
    curr_ema20 = float(ema_20.iloc[latest_idx])
    curr_sma50 = float(sma_50.iloc[latest_idx])
    curr_sma200 = float(sma_200.iloc[latest_idx]) if not np.isnan(sma_200.iloc[latest_idx]) else None
    curr_rvol = float(rvol_30.iloc[latest_idx])
    
    # Distance from 20 EMA in % and in ATR multiples
    dist_ema20_pct = ((curr_close - curr_ema20) / curr_ema20) * 100
    dist_ema20_atr = ((curr_close - curr_ema20) / curr_atr20) if curr_atr20 > 0 else 0
    
    # Min stop distance = 1.8 * ATR(14)
    min_stop_distance = 1.8 * curr_atr14
    suggested_stop = curr_close - min_stop_distance
    
    # Extension flag: RSI > 72, dist_ema20_pct > 25%, or dist_ema20_atr > 3.0
    is_extended = (curr_rsi > 72.0) or (dist_ema20_pct > 25.0) or (dist_ema20_atr > 3.0)
    
    return {
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
        "min_stop_distance": round(min_stop_distance, 2),
        "suggested_stop": round(suggested_stop, 2),
        "is_extended": bool(is_extended)
    }

def screen_universe():
    results = {}
    for sector, tickers in TICKERS.items():
        results[sector] = {}
        for ticker in tickers:
            try:
                data = yf.download(ticker, period="1y", interval="1d", progress=False)
                if data.empty or len(data) < 50:
                    continue
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = [col[0] for col in data.columns]
                tech = calculate_technicals(data)
                if tech:
                    results[sector][ticker] = tech
            except Exception as e:
                print(f"Error {ticker}: {e}")
    return results

if __name__ == "__main__":
    res = screen_universe()
    with open("screener_results.json", "w") as f:
        json.dump(res, f, indent=2)
    print("Screening complete. Saved to screener_results.json")
