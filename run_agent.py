"""
=============================================================================
TIER 2: ANALYTICAL REASONING & ALLOCATION ENGINE (HYBRIDE FLASH / PRO)
=============================================================================
Auteur       : Quantitative Research & Portfolio Architecture Agent
Description  : Jonglage dynamique entre Gemini 2.5 Flash (routine quotidienne 0$)
               et Gemini 2.5 Pro (comité d'arbitrage & hurdle rate) pour optimiser
               les crédits tout en maximisant la rigueur décisionnelle.
=============================================================================
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Charger les variables du fichier .env
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RunAgent")

SYSTEM_PROMPT = """You are the Lead Portfolio Analyst and Allocation Agent for an automated quantitative portfolio covering AI Infrastructure, Power/Energy, and Robotics.

CORE MANDATES:
1. Concentration: exactly 10 positions max (High Conviction Focus). Minimum 10.0% cash buffer (e.g. 12.0% cash, 88.0% invested capital).
2. Anti-FOMO De-risking: Strictly reject or exclude any ticker with RSI(14) > 72.0 or Distance to EMA20 > 2.8 ATR (e.g. TSM, AMD, VST, TLN).
3. Hurdle Rate & High Conviction: Select the top 10 best stocks in the entire universe based on composite score (fundamental moat, upside potential, clean technicals, earnings safety).
4. Falsification First: Every thesis must have an explicit stop loss price (at least 1.8 * ATR14 below price) and a fundamental invalidation trigger.
5. Single stock max weight: 0.10 (10.0%). Min entry size: 0.05 (5.0%). Target weights around 0.08 to 0.10 (total 0.88).
6. Mandatory Long-Term Core Holdings: The user specifically holds ONDS, NBIS, and RKLB in their long-term conviction portfolio. You MUST include ONDS, NBIS, and RKLB in the 10 positions, plus the top 7 best champions across COMPUTE, POWER, and ROBOTICS.
7. Institutional & Options Smart Money Surveillance: Leverage `institutional_and_options_layer` in the instruction dossier (Put/Call volume ratio, Options Sentiment, Top Institutional 13F holders like BlackRock, Vanguard, State Street) to confirm institutional backing.

You MUST output ONLY a strictly valid JSON object adhering to this schema:
{
  "session_timestamp": "YYYY-MM-DDTHH:MM:SSZ",
  "portfolio_summary": {
    "proposed_invested_capital_ratio": 0.88,
    "proposed_cash_ratio": 0.12,
    "active_positions_count": 10,
    "turnover_intent_ratio": 0.88
  },
  "user_long_term_focus_analysis": {
    "ONDS": {
      "company_name": "Ondas Holdings",
      "sector": "ROBOTICS",
      "technical_diagnostic": {
        "price": 7.41,
        "rsi_14": 46.41,
        "is_extended": false,
        "hard_stop_price": 6.68
      },
      "fundamental_assessment": "Summary of drone robotics moat, contracts, margins and growth.",
      "tactical_verdict": "ACCUMULATE | HOLD_CORE | TRIM_RISK",
      "invalidation_catalyst": "Explicit falsification trigger."
    },
    "NBIS": {
      "company_name": "Nebius Group",
      "sector": "COMPUTE",
      "technical_diagnostic": {
        "price": 249.87,
        "rsi_14": 58.74,
        "is_extended": false,
        "hard_stop_price": 220.36
      },
      "fundamental_assessment": "Summary of GPU cloud infrastructure, gross margin 74%, growth.",
      "tactical_verdict": "ACCUMULATE | HOLD_CORE | TRIM_RISK",
      "invalidation_catalyst": "Explicit falsification trigger."
    },
    "RKLB": {
      "company_name": "Rocket Lab",
      "sector": "ROBOTICS",
      "technical_diagnostic": {
        "price": 75.06,
        "rsi_14": 59.78,
        "is_extended": false,
        "hard_stop_price": 67.79
      },
      "fundamental_assessment": "Summary of space robotics, Electron cadence, Neutron development.",
      "tactical_verdict": "ACCUMULATE | HOLD_CORE | TRIM_RISK",
      "invalidation_catalyst": "Explicit falsification trigger."
    }
  },
  "allocations": [
    {
      "ticker": "STRING",
      "action": "BUY_NEW | ADD | HOLD | TRIM | EXIT",
      "target_weight": 0.045,
      "sector_bucket": "COMPUTE | POWER | ROBOTICS",
      "forecasts": {
        "1_session": "BULLISH | NEUTRAL | BEARISH",
        "5_session": "BULLISH | NEUTRAL | BEARISH",
        "20_session": "BULLISH | NEUTRAL | BEARISH"
      },
      "risk_parameters": {
        "stop_loss_price": 0.0,
        "profit_taking_ladder": [
          {"target_price": 0.0, "trim_fraction": 0.4},
          {"target_price": 0.0, "trim_fraction": 0.3}
        ],
        "time_stop_sessions": 15,
        "invalidation_trigger": "Explicit condition."
      },
      "analytical_thesis": {
        "rationale": ["Fact 1", "Fact 2"],
        "counterarguments": ["Risk 1", "Risk 2"],
        "hurdle_score_vs_incumbent": 1.25
      }
    }
  ]
}
"""

def call_gemini(model_name: str, dossier_data: dict, api_key: str) -> dict:
    from google import genai
    from google.genai import types

    logger.info(f"Envoi du dossier d'instructions à {model_name}...")
    client = genai.Client(api_key=api_key)

    user_content = f"Instruction Dossier:\n```json\n{json.dumps(dossier_data, indent=2)}\n```\n\nGenerate the complete quantitative allocation intents JSON payload adhering strictly to the schema."

    response = client.models.generate_content(
        model=model_name,
        contents=user_content,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1,
            response_mime_type="application/json"
        )
    )

    payload_text = response.text.strip()
    if payload_text.startswith("```json"):
        payload_text = payload_text[7:]
    if payload_text.endswith("```"):
        payload_text = payload_text[:-3]

    return json.loads(payload_text)


def run_agent_reasoning(
    dossier_file: str = "dossier.json",
    output_payload_file: str = "oms_payload.json",
    model_override: str = None
):
    if not os.path.exists(dossier_file):
        logger.error(f"{dossier_file} introuvable. Exécutez d'abord build_dossier.py !")
        return

    with open(dossier_file, "r") as f:
        dossier = json.load(f)

    gemini_api_key = os.getenv("GEMINI_API_KEY")

    # Sélection du modèle : CLI > .env > défaut Flash
    if model_override:
        target_model = "gemini-3.1-pro-preview" if "pro" in model_override.lower() else "gemini-3.8-flash"
    else:
        target_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    auto_escalate = (os.getenv("AUTO_ESCALATE_TO_PRO", "true").lower() == "true")

    logger.info(f"Dossier chargé ({dossier['dossier_timestamp']}). Stratégie de modèle : {target_model}")

    if gemini_api_key and not gemini_api_key.startswith("AIzaSy..."):
        try:
            # 1. Évaluation par le modèle cible (ex: Flash)
            logger.info(f"[Phase 1] Analyse avec {target_model}...")
            payload = call_gemini(target_model, dossier, gemini_api_key)

            # 2. Logique d'escalade automatique (Smart Escalation) vers Pro si Flash est sélectionné
            if target_model == "gemini-3.8-flash" and auto_escalate:
                turnover_actions = [a for a in payload.get("allocations", []) if a["action"] in ["BUY_NEW", "EXIT"]]
                if turnover_actions:
                    logger.info(f"ROTATION D'ACTIFS DETECTEE ({len(turnover_actions)} opérations : {[a['ticker'] for a in turnover_actions]}).")
                    logger.info("   -> Escalade automatique vers GEMINI PRO pour arbitrage de précision du Hurdle Rate...")
                    try:
                        payload_pro = call_gemini("gemini-3.1-pro-preview", dossier, gemini_api_key)
                        payload = payload_pro
                        logger.info("Arbitrage Pro validé avec succès.")
                    except Exception as e_pro:
                        logger.warning(f"Échec de l'escalade Pro ({e_pro}), maintien du payload Flash.")
                else:
                    logger.info("Séance calme (Zéro rotation BUY_NEW / EXIT). Payload Flash validé à coût 0,00$.")

            with open(output_payload_file, "w") as f:
                json.dump(payload, f, indent=2)

            logger.info(f"Payload d'allocation sauvegardé dans '{output_payload_file}'.")
            return payload

        except Exception as e:
            logger.error(f"Erreur d'appel API Gemini ({e}). Repli sur le payload local de secours.")

    # Repli hors-ligne / sandbox
    if os.path.exists(output_payload_file):
        logger.info(f"Mode simulation locale : Utilisation de '{output_payload_file}' existant.")
        with open(output_payload_file, "r") as f:
            return json.load(f)


if __name__ == "__main__":
    cli_model = None
    if "--pro" in sys.argv:
        cli_model = "gemini-2.5-pro"
    elif "--flash" in sys.argv:
        cli_model = "gemini-2.5-flash"

    run_agent_reasoning(model_override=cli_model)
