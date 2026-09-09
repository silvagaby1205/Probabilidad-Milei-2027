"""
Mantiene data/icg_history.json al día con el ICG (Índice de Confianza en el
Gobierno, UTDT), convertido a intención de voto implícita.

Fuente: ArgentinaDatos (api.argentinadatos.com), que toma el dato
directamente de la serie de la UTDT. API pública, documentada, sin
necesidad de autenticación.

Primera corrida (o si el archivo tiene muy pocos registros): baja la SERIE
HISTÓRICA COMPLETA de una vez, para no depender de reconstruir los datos a
mano. Corridas siguientes: solo chequea el último valor publicado y agrega
un registro nuevo si cambió — el ICG sale una vez por mes, así que la
mayoría de los días no hace nada.

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

import requests

URL_ULTIMO = "https://api.argentinadatos.com/v1/politica/indices/confianza-gobierno/ultimo"
URL_HISTORICO = "https://api.argentinadatos.com/v1/politica/indices/confianza-gobierno"
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "icg_history.json")
UMBRAL_BACKFILL = 5  # si hay menos registros que esto, se asume que falta la serie completa


def hoy_arg():
    return datetime.now(ZoneInfo("America/Argentina/Buenos_Aires")).date()


def to_record(item):
    icg = float(item["valor"])
    periodo = item.get("fecha")
    naive = icg * 20
    calibrada = 16.59 + 0.569 * naive
    return {
        "fecha_deteccion": hoy_arg().isoformat(),
        "periodo": periodo,
        "icg": round(icg, 3),
        "voto_naive": round(naive, 2),
        "voto_calibrado": round(calibrada, 2),
    }


def backfill_completo():
    r = requests.get(URL_HISTORICO, timeout=30)
    r.raise_for_status()
    items = r.json()
    if not isinstance(items, list) or not items:
        raise RuntimeError(f"La serie histórica de ICG vino vacía o con formato inesperado: {items!r:.500}")

    history = [to_record(item) for item in items]
    history.sort(key=lambda h: h["periodo"])
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    print(f"Backfill completo: {len(history)} registros cargados desde la serie histórica.")


def chequeo_incremental():
    r = requests.get(URL_ULTIMO, timeout=30)
    r.raise_for_status()
    data = r.json()

    history = []
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, encoding="utf-8") as f:
            history = json.load(f)

    icg = float(data["valor"])
    periodo = data.get("fecha")
    ya_cargado = any(abs(h["icg"] - icg) < 1e-9 and h.get("periodo") == periodo for h in history)
    if ya_cargado:
        print(f"Sin novedades: {periodo} / ICG {icg} ya está cargado.")
        return

    record = to_record(data)
    history.append(record)
    history.sort(key=lambda h: h["periodo"])
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    print(f"Nuevo dato de ICG cargado: {json.dumps(record, ensure_ascii=False)}")


def main():
    history = []
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, encoding="utf-8") as f:
            history = json.load(f)

    if len(history) < UMBRAL_BACKFILL:
        backfill_completo()
    else:
        chequeo_incremental()


if __name__ == "__main__":
    main()
