"""
=============================================================================
FINBOT WHATSAPP GATEWAY & INTERACTIVE ASSISTANT (TWILIO + GEMINI PRO / FLASH)
=============================================================================
Auteur       : Quantitative Portfolio Architecture Agent
Description  : Serveur FastAPI recevant les webhooks WhatsApp (Twilio) pour :
               1. Répondre en temps réel aux questions de l'utilisateur sur son
                  portefeuille, son PnL, les actions en watchlist et la stratégie.
               2. Fournir des raccourcis rapides (/pnl, /positions, /cash, /watchlist).
               3. Envoyer des notifications sortantes push (résumé de rebalancement).
=============================================================================
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, Form
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client as TwilioClient

# Charger l'environnement
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("WhatsAppBot")

app = FastAPI(title="FINBOT WhatsApp Gateway", version="1.0.0")

# ---------------------------------------------------------------------------
# UTILITAIRES : RÉCUPÉRATION DU CONTEXTE EN TEMPS RÉEL
# ---------------------------------------------------------------------------

def get_alpaca_live_context() -> Dict[str, Any]:
    """Interroge l'API Alpaca pour extraire l'état exact du compte et des positions."""
    api_key = os.getenv("APCA_API_KEY_ID")
    api_secret = os.getenv("APCA_API_SECRET_KEY")

    if not api_key or not api_secret:
        return {"error": "Clés Alpaca non configurées."}

    try:
        from alpaca.trading.client import TradingClient
        client = TradingClient(api_key, api_secret, paper=True)
        acc = client.get_account()
        positions = client.get_all_positions()

        eq = float(acc.equity)
        cash = float(acc.cash)
        cash_ratio = (cash / eq * 100.0) if eq > 0 else 0.0

        pos_list = []
        total_unrealized_pl = 0.0

        for p in positions:
            mkt_val = float(p.market_value)
            unrealized_pl = float(p.unrealized_pl)
            unrealized_plpc = float(p.unrealized_plpc) * 100.0
            total_unrealized_pl += unrealized_pl
            weight_pct = (mkt_val / eq * 100.0) if eq > 0 else 0.0

            pos_list.append({
                "symbol": p.symbol,
                "shares": round(float(p.qty), 4),
                "market_value": round(mkt_val, 2),
                "current_price": round(float(p.current_price), 2),
                "unrealized_pl": round(unrealized_pl, 2),
                "unrealized_plpc": round(unrealized_plpc, 2),
                "weight_pct": round(weight_pct, 1)
            })

        return {
            "equity": round(eq, 2),
            "cash": round(cash, 2),
            "cash_ratio_pct": round(cash_ratio, 1),
            "buying_power": round(float(acc.buying_power), 2),
            "positions_count": len(pos_list),
            "total_unrealized_pl": round(total_unrealized_pl, 2),
            "positions": pos_list
        }
    except Exception as e:
        logger.error(f"Erreur d'accès Alpaca: {e}")
        return {"error": str(e)}


def get_screener_context() -> Dict[str, Any]:
    """Charge la dernière watchlist et les meilleurs scores du screener."""
    res = {}
    if os.path.exists("watchlist.json"):
        try:
            with open("watchlist.json", "r", encoding="utf-8") as f:
                res["watchlist"] = json.load(f)
        except Exception:
            pass

    if os.path.exists("screener_results.json"):
        try:
            with open("screener_results.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                res["timestamp"] = data.get("screen_timestamp")
                top_leaders = {}
                for sec, cands in data.get("ranked_candidates", {}).items():
                    top_leaders[sec] = [
                        f"{c['ticker']} (Score: {c['composite_score']}, Upside: {c['upside_pct']}%)"
                        for c in cands[:3]
                    ]
                res["sector_leaders"] = top_leaders
        except Exception:
            pass
    return res


def get_last_rebalance_context() -> Dict[str, Any]:
    """Charge les dernières décisions d'allocation de l'IA (oms_payload.json)."""
    if os.path.exists("oms_payload.json"):
        try:
            with open("oms_payload.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                return {
                    "session_timestamp": data.get("session_timestamp"),
                    "summary": data.get("portfolio_summary", {}),
                    "allocations": [
                        {
                            "ticker": a.get("ticker"),
                            "action": a.get("action"),
                            "target_weight": a.get("target_weight"),
                            "sector": a.get("sector_bucket"),
                            "rationale": a.get("analytical_thesis", {}).get("rationale", [])[:2]
                        }
                        for a in data.get("allocations", [])
                    ]
                }
        except Exception:
            pass
    return {}


# ---------------------------------------------------------------------------
# COMMANDES RAPIDES SANS LLM (INSTANTANÉES ET ÉCONOMIQUES)
# ---------------------------------------------------------------------------

def handle_quick_commands(text: str) -> Optional[str]:
    cmd = text.strip().lower()

    if cmd in ["/pnl", "pnl", "perf", "performance"]:
        ctx = get_alpaca_live_context()
        if "error" in ctx:
            return f"⚠️ *Erreur Alpaca :* {ctx['error']}"

        pnl_sign = "+" if ctx["total_unrealized_pl"] >= 0 else ""
        emoji = "📈" if ctx["total_unrealized_pl"] >= 0 else "📉"

        msg = (
            f"{emoji} *RAPPORT PnL EN DIRECT*\n\n"
            f"💰 *Total Equity :* {ctx['equity']:,.2f} $\n"
            f"💵 *Cash disponible :* {ctx['cash']:,.2f} $ ({ctx['cash_ratio_pct']}%)\n"
            f"📊 *PnL latent :* {pnl_sign}{ctx['total_unrealized_pl']:,.2f} $\n"
            f"🎯 *Positions actives :* {ctx['positions_count']}\n\n"
            f"_Tapez *positions* pour voir le détail de chaque ligne._"
        )
        return msg

    elif cmd in ["/positions", "positions", "pos", "/pos"]:
        ctx = get_alpaca_live_context()
        if "error" in ctx:
            return f"⚠️ *Erreur Alpaca :* {ctx['error']}"

        lines = [f"📋 *POSITIONS OUVERTES ({ctx['positions_count']})* :\n"]
        for p in ctx["positions"]:
            sign = "+" if p["unrealized_plpc"] >= 0 else ""
            badge = "🟢" if p["unrealized_plpc"] >= 0 else "🔴"
            lines.append(
                f"{badge} *{p['symbol']}* : {p['shares']} actions (~{p['market_value']:,.1f} $ | {p['weight_pct']}%)\n"
                f"   Cours : {p['current_price']} $ | PnL : {sign}{p['unrealized_plpc']}%\n"
            )

        lines.append(f"💵 *Cash dispo :* {ctx['cash']:,.2f} $ ({ctx['cash_ratio_pct']}%)")
        return "\n".join(lines)

    elif cmd in ["/cash", "cash", "solde"]:
        ctx = get_alpaca_live_context()
        if "error" in ctx:
            return f"⚠️ *Erreur Alpaca :* {ctx['error']}"
        return (
            f"💵 *ÉTAT DES LIQUIDITÉS*\n\n"
            f"• *Cash libre :* {ctx['cash']:,.2f} $\n"
            f"• *Total portefeuille :* {ctx['equity']:,.2f} $\n"
            f"• *Ratio Cash :* {ctx['cash_ratio_pct']}%\n"
            f"• *Pouvoir d'achat :* {ctx['buying_power']:,.2f} $\n\n"
            f"_Le bot conserve une réserve stratégique pour acheter les replis (dips)._"
        )

    elif cmd in ["/watchlist", "watchlist", "wl"]:
        sc = get_screener_context()
        wl = sc.get("watchlist", {})
        if not wl:
            return "ℹ️ Aucune watchlist locale trouvée. Le screener se lance à 14h00 Paris."

        lines = ["🎯 *TOP WATCHLIST DYNAMIQUE (40 VALEURS)* :\n"]
        for sec, syms in wl.items():
            lines.append(f"*{sec}* : {', '.join(syms[:8])}")
        return "\n".join(lines)

    elif cmd in ["/help", "help", "aide", "menu", "start"]:
        return (
            "🤖 *FINBOT TRADING ASSISTANT*\n\n"
            "Voici les commandes rapides disponibles :\n\n"
            "• *pnl* : Résumé de la performance et valeur nette\n"
            "• *positions* : Liste détaillée de vos lignes en cours\n"
            "• *cash* : Détail des liquidités disponibles\n"
            "• *watchlist* : Les meilleures actions surveillées par secteur\n"
            "• *help* : Afficher ce message d'aide\n\n"
            "💬 *Vous pouvez aussi me poser n'importe quelle question en français !*\n"
            "Exemples :\n"
            "- _Pourquoi as-tu vendu RKLB ?_\n"
            "- _Que penses-tu de l'action MU en portefeuille ?_\n"
            "- _Quelles sont les meilleures biotechs du moment ?_\n"
            "- _Est-ce que le marché est en surchauffe ?_"
        )

    return None


# ---------------------------------------------------------------------------
# RAISONNEMENT IA GEMINI (QUESTIONS EN LANGAGE NATUREL)
# ---------------------------------------------------------------------------

def ask_gemini_assistant(user_prompt: str) -> str:
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        return "⚠️ Erreur : GEMINI_API_KEY n'est pas configurée dans les variables d'environnement."

    alpaca_data = get_alpaca_live_context()
    screener_data = get_screener_context()
    rebalance_data = get_last_rebalance_context()

    system_instruction = (
        "Tu es l'assistant de trading quantitatif mobile (FINBOT) de l'utilisateur sur WhatsApp.\n"
        "Tu gères un portefeuille quantitatif autonome axé sur 4 secteurs : COMPUTE (IA), POWER (Énergie), ROBOTICS et BIOTECH.\n"
        "Directives de réponse WhatsApp :\n"
        "- Sois précis, professionnel, percutant et pédagogue.\n"
        "- Utilise le formatage WhatsApp : mets en gras avec un seul astérisque (*mot*), pas de double astérisque.\n"
        "- N'utilise JAMAIS de titres markdown avec dièses (# ou ##).\n"
        "- Reste concis (maximum 150 à 250 mots) pour être facilement lisible sur smartphone.\n"
        "- Cite les vrais chiffres disponibles dans le contexte (prix, PnL, scores, ratios de cash).\n"
        "- Si l'utilisateur te demande pourquoi une action a été achetée ou vendue, réfère-toi aux principes de méritocratie quantitative et aux règles anti-FOMO (RSI > 72 = rejet).\n"
        "- Réponds toujours en français."
    )

    context_payload = {
        "live_alpaca_account": alpaca_data,
        "active_screener_leaders": screener_data.get("sector_leaders", {}),
        "last_rebalance_decisions": rebalance_data
    }

    prompt = (
        f"Contexte du portefeuille en direct :\n"
        f"```json\n{json.dumps(context_payload, indent=2)}\n```\n\n"
        f"Question de l'utilisateur sur WhatsApp : \"{user_prompt}\"\n\n"
        f"Donne une réponse claire, formatée pour WhatsApp."
    )

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=gemini_key)
        target_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        response = client.models.generate_content(
            model=target_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2
            )
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Erreur d'appel Gemini: {e}")
        return f"⚠️ Erreur lors de l'analyse IA : {str(e)}"


# ---------------------------------------------------------------------------
# WEBHOOK TWILIO WHATSAPP (POST /whatsapp)
# ---------------------------------------------------------------------------

@app.post("/whatsapp")
@app.post("/webhook")
@app.post("/w")
async def twilio_whatsapp_webhook(request: Request):
    """Point d'entrée HTTP appelé par Twilio à chaque message WhatsApp reçu."""
    form_data = await request.form()
    incoming_msg = form_data.get("Body", "").strip()
    sender_number = form_data.get("From", "")

    logger.info(f"Message reçu de {sender_number} : '{incoming_msg}'")

    if not incoming_msg:
        reply_text = "Bonjour ! Tapez *help* pour voir ce que je peux faire."
    else:
        # 1. Vérifier si c'est une commande rapide (pnl, positions, cash, help...)
        quick_reply = handle_quick_commands(incoming_msg)
        if quick_reply:
            reply_text = quick_reply
        else:
            # 2. Sinon, solliciter Gemini avec le contexte en temps réel
            reply_text = ask_gemini_assistant(incoming_msg)

    # Réponse au format TwiML XML requis par Twilio
    resp = MessagingResponse()
    resp.message(reply_text)

    return Response(content=str(resp), media_type="application/xml")


@app.get("/")
@app.get("/health")
def health_check():
    """Vérifie que le serveur est en ligne et accessible."""
    now_utc = datetime.now(timezone.utc).isoformat()
    alpaca = get_alpaca_live_context()
    return {
        "status": "online",
        "service": "FINBOT WhatsApp Connector",
        "timestamp": now_utc,
        "alpaca_connected": "error" not in alpaca,
        "equity": alpaca.get("equity")
    }


# ---------------------------------------------------------------------------
# NOTIFICATION SORTANTE PUSH (Pour GitHub Actions / alertes fin de journée)
# ---------------------------------------------------------------------------

def send_whatsapp_push_notification(message: str, to_number: Optional[str] = None) -> bool:
    """
    Envoie un message WhatsApp sortant proactif via l'API REST Twilio.
    Peut être invoqué par run_rebalance.py à 21h30 pour notifier la fin du rebalancement.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_whatsapp = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
    target_number = to_number or os.getenv("USER_PHONE_NUMBER")

    if not account_sid or not auth_token or not target_number:
        logger.warning("Configuration Twilio incomplète (TWILIO_ACCOUNT_SID, AUTH_TOKEN ou USER_PHONE_NUMBER manquant).")
        return False

    if not target_number.startswith("whatsapp:"):
        target_number = f"whatsapp:{target_number}"

    try:
        twilio_client = TwilioClient(account_sid, auth_token)
        msg = twilio_client.messages.create(
            body=message,
            from_=from_whatsapp,
            to=target_number
        )
        logger.info(f"Notification WhatsApp envoyée avec succès (SID: {msg.sid}) à {target_number}")
        return True
    except Exception as e:
        logger.error(f"Échec de l'envoi de la notification WhatsApp: {e}")
        return False


# ---------------------------------------------------------------------------
# CLI TESTING & ENTRYPOINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    if "--test-query" in sys.argv:
        # Test local sans Twilio : python whatsapp_bot.py --test-query "Quel est mon PnL ?"
        idx = sys.argv.index("--test-query")
        query = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else "Quel est mon PnL ?"
        print(f"\n--- TEST DE REQUÊTE : '{query}' ---")
        reply = handle_quick_commands(query) or ask_gemini_assistant(query)
        print("\nRéponse générée :\n")
        print(reply)
    elif "--send" in sys.argv:
        idx = sys.argv.index("--send")
        msg = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else "Test FINBOT"
        send_whatsapp_push_notification(msg)
    else:
        import uvicorn
        port = int(os.getenv("PORT", 8000))
        logger.info(f"Démarrage du serveur WhatsApp Gateway sur le port {port}...")
        uvicorn.run("whatsapp_bot:app", host="0.0.0.0", port=port, reload=True)
