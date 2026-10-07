"""
=============================================================================
VALIDATION ET AUDIT DE CONNEXION : GEMINI PRO, ALPACA & TAVILY
=============================================================================
"""

import sys
import os
from dotenv import load_dotenv

# Sécuriser l'encodage console Windows pour éviter les crashs charmap cp1252
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Charger les variables du fichier .env
load_dotenv()

def test_environment():
    print("\n========================================================")
    print("AUDIT DE CONFIGURATION DE L'ENVIRONNEMENT QUANTITATIF")
    print("========================================================")

    # 1. Test Clé Gemini (Google AI Studio)
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key or gemini_key.startswith("AIzaSy..."):
        print("[!] Clé Gemini (GEMINI_API_KEY) : NON CONFIGUREE ou valeur d'exemple dans .env")
        print("    -> Obtenez-la gratuitement sur : https://aistudio.google.com")
    else:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            models = client.models.list()
            print("[OK] Clé Gemini Pro : VALIDE & CONNECTEE (Google AI Studio OK)")
        except Exception as e:
            print(f"[ERREUR] Clé Gemini présente mais échec API : {e}")

    # 2. Test Alpaca Paper Trading
    alpaca_key = os.getenv("APCA_API_KEY_ID")
    alpaca_secret = os.getenv("APCA_API_SECRET_KEY")

    if not alpaca_key or alpaca_key.startswith("PK..."):
        print("[!] Clés Alpaca Paper (APCA_API_KEY_ID) : NON CONFIGUREES ou valeur d'exemple")
        print("    -> Créez votre compte Paper Trading sur : https://alpaca.markets")
    else:
        try:
            from alpaca.trading.client import TradingClient
            client = TradingClient(api_key=alpaca_key, secret_key=alpaca_secret, paper=True)
            account = client.get_account()
            print("[OK] Alpaca Paper Trading : CONNECTE")
            print(f"     - Statut du compte    : {account.status}")
            print(f"     - Cash virtuel dispo  : ${float(account.cash):,.2f}")
            print(f"     - Valeur portefeuille : ${float(account.portfolio_value):,.2f}")
            print(f"     - Pouvoir d'achat     : ${float(account.buying_power):,.2f}")
        except Exception as e:
            print(f"[ERREUR] Clés Alpaca présentes mais échec d'authentification : {e}")

    # 3. Test Tavily (Optionnel)
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key and not tavily_key.startswith("tvly-..."):
        print("[OK] Clé Tavily (Recherche Web) : CONFIGUREE")
    else:
        print("[INFO] Clé Tavily : Non configurée (Optionnelle pour la recherche synthétique)")

    print("========================================================\n")

if __name__ == "__main__":
    test_environment()
