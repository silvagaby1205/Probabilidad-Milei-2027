"""
Trae el precio actual del outcome "Milei" en el mercado de Polymarket
"Argentina Presidential Election Winner" y lo agrega al histórico.

Corre todos los días junto a los otros dos cálculos. No necesita ningún
Secret: la API pública de Polymarket (Gamma) no pide autenticación para
leer datos de mercado.

OJO — esta es la pieza menos probada de las tres. Polymarket organiza estos
mercados como un "evento" que contiene un mercado Sí/No por candidato, pero
no pude confirmar en vivo el slug exacto ni la forma final de la respuesta.
En la primera corrida, si falla, el script imprime la lista de mercados que
sí encontró dentro del evento — con eso se ajusta el filtro de "milei" en
dos minutos.
"""

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo


def hoy_arg():
    return datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()

import requests

EVENT_SLUG = "argentina-presidential-election-winner"
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "polymarket_history.json")


def find_milei_price():
    r = requests.get("https://gamma-api.polymarket.com/events", params={"slug": EVENT_SLUG}, timeout=30)
    r.raise_for_status()
    events = r.json()

    if not events:
        r = requests.get(
            "https://gamma-api.polymarket.com/public-search",
            params={"q": "Argentina presidential election", "events_status": "active"},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        events = data.get("events", data if isinstance(data, list) else [])

    if not events:
        raise RuntimeError(f"No encontré ningún evento con slug '{EVENT_SLUG}'. Puede que el slug haya cambiado.")

    event = events[0]
    markets = event.get("markets", [])

    for m in markets:
        texto = f"{m.get('question', '')} {m.get('groupItemTitle', '')}".lower()
        if "milei" in texto:
            outcomes = json.loads(m["outcomes"])
            prices = json.loads(m["outcomePrices"])
            idx = outcomes.index("Yes") if "Yes" in outcomes else 0
            return float(prices[idx])

    print("No encontré un mercado de Milei. Mercados dentro del evento:")
    for m in markets:
        print(" -", m.get("question"))
    raise RuntimeError("No se pudo identificar el mercado de Milei dentro del evento")


def main():
    price = find_milei_price()
    pct = round(price * 100, 2)
    today = hoy_arg().isoformat()

    history = []
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, encoding="utf-8") as f:
            history = json.load(f)

    history = [h for h in history if h["date"] != today]
    history.append({"date": today, "prob_milei": pct})
    history.sort(key=lambda h: h["date"])

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    print(f"Polymarket hoy: {pct}%")


if __name__ == "__main__":
    main()
