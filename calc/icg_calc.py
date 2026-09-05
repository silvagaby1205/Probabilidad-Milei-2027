"""
Chequea si la Universidad Torcuato Di Tella publicó un nuevo dato del ICG
(Índice de Confianza en el Gobierno) y, si es así, lo agrega al histórico
con la conversión a "intención de voto" implícita.

Se corre todos los días junto al cálculo de bonos, pero solo escribe algo
nuevo en data/icg_history.json cuando el valor publicado cambia — el ICG
sale una vez por mes, así que la mayoría de los días este script no hace
nada, tal como se pidió.

OJO — esto es lo menos verificado de los tres cálculos del sitio, porque no
pude previsualizar el archivo real (utdt.edu bloquea el acceso automatizado
de mi lado). En la primera corrida, revisá el log: si `latest_icg()` no
encuentra la fila correcta, imprime las últimas filas de la hoja para que
sea fácil ajustar la lógica de parseo.

Fórmulas de conversión (fuente: nota de Ámbito, "Cuidado con el ICG de la
UTDT y su uso en la proyección eleccionaria", 29/10/2025, sobre 13
elecciones):
  naive       = ICG × 20
  calibrada   = 16.59 + 0.569 × naive   (regresión lineal contra el resultado real)
"""

import io
import json
import os
import re
from datetime import date

import pandas as pd
import requests

DESCARGA_URL = "https://www.utdt.edu/listado_contenidos.php?id_item_menu=28756"
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "icg_history.json")


def find_excel_url():
    r = requests.get(DESCARGA_URL, timeout=30)
    r.raise_for_status()
    m = re.search(r'https://www\.utdt\.edu/download\.php\?fname=[^"\')\s]+\.xls', r.text)
    if not m:
        raise RuntimeError("No encontré el link del Excel del ICG en la página de descarga de UTDT")
    return m.group(0)


def latest_icg():
    url = find_excel_url()
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    df = pd.read_excel(io.BytesIO(r.content), engine="xlrd", header=None)

    # Recorremos de atrás para adelante buscando la última fila donde haya
    # un número que parezca un ICG (entre 0 y 5) en alguna columna, y una
    # fecha/etiqueta de mes en otra.
    for i in range(len(df) - 1, -1, -1):
        row = df.iloc[i]
        icg_val = None
        label = None
        for val in row:
            if isinstance(val, (int, float)) and 0 <= val <= 5:
                icg_val = float(val)
            elif val is not None and str(val).strip() not in ("", "nan"):
                label = str(val).strip()
        if icg_val is not None:
            print(f"Fila detectada como último dato: {row.tolist()}")
            return label, icg_val

    print("No encontré una fila válida. Últimas 10 filas de la hoja para depurar:")
    print(df.tail(10).to_string())
    raise RuntimeError("No se pudo identificar el último valor del ICG")


def main():
    label, icg = latest_icg()
    naive = icg * 20
    calibrada = 16.59 + 0.569 * naive

    history = []
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, encoding="utf-8") as f:
            history = json.load(f)

    ya_cargado = any(abs(h["icg"] - icg) < 1e-9 and h.get("periodo") == label for h in history)
    if ya_cargado:
        print(f"Sin novedades: {label} / ICG {icg} ya está cargado.")
        return

    record = {
        "fecha_deteccion": date.today().isoformat(),
        "periodo": label,
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
