"""
Trae el precio actual del outcome "Milei" en el mercado de Polymarket
"Argentina Presidential Election Winner" y lo agrega al histórico.

Corre cada 3 horas (Polymarket es un mercado en vivo). No necesita ningún
Secret: la API pública de Polymarket (Gamma) no pide autenticación para
leer datos de mercado.

Usa el endpoint documentado /events/slug/{slug} (devuelve el evento como un
único objeto, no una lista) — la versión anterior de este script usaba
/events?slug=... como parámetro de búsqueda, que Polymarket parece ignorar
en varios de sus endpoints, devolviendo una lista genérica en su lugar.
Eso probablemente explica por qué el precio se había quedado pegado en un
solo valor: el script encontraba el primer mercado con "milei" en el texto
de una lista de eventos que no tenía nada que ver con el nuestro.

Si el evento tiene más de un mercado que menciona a Milei, se prioriza el
que tiene groupItemTitle == "Javier Milei" exacto (así es como Polymarket
etiqueta cada candidato dentro de un evento con varios mercados) antes que
una coincidencia parcial de texto.
"""

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

EVENT_SLUG = "argentina-presidential-election-winner"
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "polymarket_history.json")


def hoy_arg():
    return datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()


def elegir_mercado_milei(markets):
    candidatos = [(m.get("groupItemTitle") or "", m.get("question", ""), m) for m in markets]

    for group_title, _, m in candidatos:
        if group_title.strip().lower() == "javier milei":
            return m

    for group_title, question, m in candidatos:
        if "milei" in group_title.lower() or "milei" in question.lower():
            return m

    print("No encontré un mercado de Milei. Mercados dentro del evento:")
    for group_title, question, _ in candidatos:
        print(f" - groupItemTitle={group_title!r} question={question!r}")
    raise RuntimeError("No se pudo identificar el mercado de Milei dentro del evento")


def find_milei_price():
    url = f"https://gamma-api.polymarket.com/events/slug/{EVENT_SLUG}"
    r = requests.get(url, timeout=30)

    if r.status_code == 404:
        # Fallback por si el slug cambió: buscarlo por texto.
        r2 = requests.get(
            "https://gamma-api.polymarket.com/public-search",
            params={"q": "Argentina presidential election", "events_status": "active"},
            timeout=30,
        )
        r2.raise_for_status()
        data = r2.json()
        events = data.get("events", data if isinstance(data, list) else [])
        if not events:
            raise RuntimeError(f"No encontré ningún evento con slug '{EVENT_SLUG}' ni por búsqueda de texto.")
        event = events[0]
    else:
        r.raise_for_status()
        event = r.json()

    markets = event.get("markets", [])
    if not markets:
        raise RuntimeError(f"El evento '{EVENT_SLUG}' no tiene mercados. Respuesta: {json.dumps(event)[:500]}")

    elegido = elegir_mercado_milei(markets)
    outcomes = json.loads(elegido["outcomes"])
    prices = json.loads(elegido["outcomePrices"])
    idx = outcomes.index("Yes") if "Yes" in outcomes else 0
    return float(prices[idx])


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
