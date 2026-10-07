# Quantitative Allocation & Execution Bot (AI Infrastructure, Energy, Robotics)

Production-grade quantitative pipeline combining **Antigravity Lead Research & Allocation Agent** with an external deterministic **Risk Engine & Order Management System (OMS)**.

---

## Architecture Overview

```
[Marché US (NYSE / NASDAQ)]
       │ (15:30 ET / 21:30 Paris)
       ▼
[analyze_universe.py / screener.py] ──► Calcule RSI(14), ATR(14/20), EMA(20), RVOL(30)
       │
       ▼
[Antigravity Research Agent] ────────► Applique Hurdle Rate (20%), Falsifiabilité, Red Lines
       │
       ▼
[oms_payload.json] ──────────────────► Payload analytique structuré (Format strict JSON)
       │
       ▼
[risk_engine_oms.py] ────────────────► Filtres de risque pré-trade :
       ├── 1. Fractions d'actions & compte 10k$ (MOC Synthétique vs Alpaca)
       ├── 2. Plafond sectoriel consolidé (Compute + Power <= 70%)
       └── 3. Delta net d'ordres & suppression du churn sur HOLD
       │
       ▼
[executed_orders_batch.json] ────────► Envoi direct au broker (Alpaca / Interactive Brokers)
```

---

## Gestion des fuseaux horaires & Daylight Saving Time (DST)

Pour éviter les décalages de 1 heure lors des périodes de transition saisonnière (mars et fin octobre) entre Paris et New York :
* **Toujours caler le planificateur sur le fuseau de New York (`America/New_York`)**.
* Le script [`run_rebalance.py`](file:///c:/Users/cjose/antigravity%20project/BOT/run_rebalance.py) intègre `zoneinfo.ZoneInfo("America/New_York")` pour vérifier automatiquement l'horloge de Wall Street.

### Configuration Crontab recommandée

```bash
# Déclenchement automatique du lundi au vendredi à 15h30 heure de New York
CRON_TZ=America/New_York
30 15 * * 1-5 /usr/bin/python3 /app/run_rebalance.py >> /var/log/trading.log 2>&1
```

* **Heure normale (New York EDT / Paris CEST) :** 15h30 ET = **21h30 Paris**
* **Période de décalage DST (mars / fin octobre) :** 15h30 ET = **20h30 Paris** (Le cron s'adapte sans aucune intervention manuelle !)

---

## Fichiers du projet

* [`run_rebalance.py`](file:///c:/Users/cjose/antigravity%20project/BOT/run_rebalance.py) : Script maître orchestrateur du pipeline quotidien.
* [`analyze_universe.py`](file:///c:/Users/cjose/antigravity%20project/BOT/analyze_universe.py) : Screener quantitatif multi-actifs (données réelles yfinance).
* [`universe_analysis.csv`](file:///c:/Users/cjose/antigravity%20project/BOT/universe_analysis.csv) : Base technique consolidée des indicateurs.
* [`build_allocation_payload.py`](file:///c:/Users/cjose/antigravity%20project/BOT/build_allocation_payload.py) : Générateur de payload validé contre les lignes rouges opérationnelles.
* [`oms_payload.json`](file:///c:/Users/cjose/antigravity%20project/BOT/oms_payload.json) : Payload JSON conforme aux spécifications Antigravity.
* [`portfolio_state.json`](file:///c:/Users/cjose/antigravity%20project/BOT/portfolio_state.json) : État courant du portefeuille (positions, cours, liquidités).
* [`risk_engine_oms.py`](file:///c:/Users/cjose/antigravity%20project/BOT/risk_engine_oms.py) : Moteur de risque externe, calcul de delta net et routage fractionné.
* [`executed_orders_batch.json`](file:///c:/Users/cjose/antigravity%20project/BOT/executed_orders_batch.json) : Batch final d'ordres de trading prêts pour l'API du broker.

---

## Commandes d'exécution rapide

Exécuter le pipeline complet :
```bash
python run_rebalance.py
```

Tester le Risk Engine avec Interactive Brokers (mode MOC Synthétique) :
```bash
EXECUTION_MODE=SYNTHETIC_MOC BROKER_TARGET=IBKR python risk_engine_oms.py
```
