"""
Calcula la probabilidad implícita "método spot" (Fernando Marull / FMyA):
toma el riesgo país de hoy tal cual —sin pasar por tasas forward— y lo pasa
por la misma regla de tres, usando los anclajes de su propia lámina:
  Milei = 200 pb · Oposición moderada = 800 pb · PJ extremo = 2.000 pb

Fuente del riesgo país: ArgentinaDatos (api.argentinadatos.com), que a su
vez toma el dato de Ámbito. Es una API pública, documentada, sin necesidad
de autenticación.

Corre todos los días junto a los otros cálculos.
"""

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo


def hoy_arg():
    return datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()

import requests

URL = "https://api.argentinadatos.com/v1/finanzas/indices/riesgo-pais/ultimo"
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "spot_history.json")

MILEI_ANCHOR = 200
MODERADO_ANCHOR = 800
EXTREMO_ANCHOR = 2000


def prob(anchor_rival, rp):
    p = (anchor_rival - rp) / (anchor_rival - MILEI_ANCHOR)
    return max(0.0, min(1.0, p))


def main():
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    data = r.json()
    rp = float(data["valor"])

    record = {
        "date": hoy_arg().isoformat(),
        "fecha_fuente": data.get("fecha"),
        "riesgo_pais": rp,
        "prob_vs_extremo": round(prob(EXTREMO_ANCHOR, rp) * 100, 1),
        "prob_vs_moderado": round(prob(MODERADO_ANCHOR, rp) * 100, 1),
    }

    history = []
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, encoding="utf-8") as f:
            history = json.load(f)

    today = record["date"]
    history = [h for h in history if h["date"] != today]
    history.append(record)
    history.sort(key=lambda h: h["date"])

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    print(json.dumps(record, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
