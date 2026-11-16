"""
Mantiene data/icg_history.json al día con el ICG (Índice de Confianza en el
Gobierno, UTDT), convertido a intención de voto implícita.

Fuente: ArgentinaDatos (api.argentinadatos.com), que toma el dato
directamente de la serie de la UTDT. API pública, documentada, sin
necesidad de autenticación.

Primera corrida (o si el archivo tiene muy pocos registros): baja la SERIE
HISTÓRICA COMPLETA de una vez. Corridas siguientes: solo chequea el último
valor publicado y lo agrega (o lo corrige) si cambió — el ICG sale una vez
por mes, así que la mayoría de las veces no hace nada.

Se mantiene un único registro por mes. La fuente entrega el valor con 6
decimales y acá se guarda redondeado a 3, así que las comparaciones se hacen
siempre con el mismo redondeo (si no, cada corrida creería que el dato cambió).

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


def mes_de(periodo):
    return (periodo or "")[:7]


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


def deduplicar_por_mes(history):
    """Deja un solo registro por mes (el más reciente de los guardados)."""
    por_mes = {}
    for h in history:
        por_mes[mes_de(h.get("periodo"))] = h
    return sorted(por_mes.values(), key=lambda h: h.get("periodo") or "")


def cargar():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def guardar(history):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def backfill_completo():
    r = requests.get(URL_HISTORICO, timeout=30)
    r.raise_for_status()
    items = r.json()
    if not isinstance(items, list) or not items:
        raise RuntimeError(f"La serie histórica de ICG vino vacía o con formato inesperado: {items!r:.500}")

    history = deduplicar_por_mes([to_record(item) for item in items])
    guardar(history)
    print(f"Backfill completo: {len(history)} registros cargados desde la serie histórica.")


def chequeo_incremental():
    r = requests.get(URL_ULTIMO, timeout=30)
    r.raise_for_status()
    data = r.json()

    original = cargar()
    history = deduplicar_por_mes(original)
    sobraban = len(original) - len(history)
    if sobraban:
        print(f"Se eliminaron {sobraban} registros repetidos del mismo mes.")

    icg = float(data["valor"])
    periodo = data.get("fecha")
    mes = mes_de(periodo)

    # Se compara por mes (no por la fecha exacta) y con el mismo redondeo con el que se guarda.
    existente = next((h for h in history if mes_de(h.get("periodo")) == mes), None)
    if existente is not None and abs(existente["icg"] - round(icg, 3)) < 1e-9:
        print(f"Sin novedades: {mes} / ICG {round(icg, 3)} ya está cargado.")
        if sobraban:
            guardar(history)
        return

    record = to_record(data)
    if existente is not None:
        history[history.index(existente)] = record
        print(f"Se corrigió el valor de {mes}: {existente['icg']} -> {record['icg']}")
    else:
        history.append(record)
        print(f"Nuevo dato de ICG cargado: {json.dumps(record, ensure_ascii=False)}")

    history.sort(key=lambda h: h.get("periodo") or "")
    guardar(history)


def main():
    if len(cargar()) < UMBRAL_BACKFILL:
        backfill_completo()
    else:
        chequeo_incremental()


if __name__ == "__main__":
    main()
