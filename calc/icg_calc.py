"""
Chequea si hay un nuevo valor publicado del ICG (Índice de Confianza en el
Gobierno, UTDT) y, si lo hay, lo agrega al histórico con la conversión a
"intención de voto" implícita.

Fuente: ArgentinaDatos (api.argentinadatos.com), que toma el dato
directamente de la serie de la UTDT. API pública, documentada, sin
necesidad de autenticación — mucho más simple y confiable que levantar el
Excel de la UTDT a mano.

Se corre todos los días junto a los otros cálculos, pero solo escribe algo
nuevo en data/icg_history.json cuando el valor publicado cambia — el ICG
sale una vez por mes, así que la mayoría de los días este script no hace
nada.

Fórmulas de conversión (fuente: nota de Ámbito, "Cuidado con el ICG de la
UTDT y su uso en la proyección eleccionaria", 29/10/2025, sobre 13
elecciones):
  naive     = ICG × 20
  calibrada = 16.59 + 0.569 × naive   (regresión lineal contra el resultado real)
"""

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo


def hoy_arg():
    return datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()

import requests

URL = "https://api.argentinadatos.com/v1/politica/indices/confianza-gobierno/ultimo"
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "icg_history.json")


def main():
    r = requests.get(URL, timeout=30)
    r.raise_for_status()
    data = r.json()
    icg = float(data["valor"])
    periodo = data.get("fecha")

    naive = icg * 20
    calibrada = 16.59 + 0.569 * naive

    history = []
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, encoding="utf-8") as f:
            history = json.load(f)

    ya_cargado = any(abs(h["icg"] - icg) < 1e-9 and h.get("periodo") == periodo for h in history)
    if ya_cargado:
        print(f"Sin novedades: {periodo} / ICG {icg} ya está cargado.")
        return

    record = {
        "fecha_deteccion": hoy_arg().isoformat(),
        "periodo": periodo,
        "icg": round(icg, 3),
        "voto_naive": round(naive, 2),
        "voto_calibrado": round(calibrada, 2),
    }
    history.append(record)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    print(f"Nuevo dato de ICG cargado: {json.dumps(record, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
