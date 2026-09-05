"""
Calcula la probabilidad implícita de reelección de Milei a partir de la tasa
forward entre AO27C y AO28C, neteada contra la curva forward de UST.

Pensado para correr una vez por día desde GitHub Actions. Necesita dos
variables de entorno: IOL_USER e IOL_PASS (las credenciales de tu cuenta de
InvertirOnline — se configuran como Secrets del repo, nunca en el código).

OJO — cosas para verificar en la primera corrida real:
  1. El endpoint de cotización de IOL (`iol_price`) y el nombre del campo
     `ultimoPrecio` están tomados de la documentación pública de la API
     (api.invertironline.com). Si el primer run falla acá, revisá la
     respuesta cruda que imprime el script y ajustá el nombre del campo.
  2. Los nombres de los campos de la curva UST (`BC_1YEAR`, `BC_2YEAR`,
     `BC_3YEAR`) son los que usa el feed XML de home.treasury.gov. También
     conviene chequearlos una vez con la salida cruda si algo no cierra.
  3. Los cronogramas de AO27C y AO28C están hardcodeados tal como los
     devolvió IOL el 04/09/2026. Son bonos bullet (todo el capital al
     vencimiento), así que no deberían cambiar mientras existan.
"""

import os
import json
import xml.etree.ElementTree as ET
from datetime import date

import requests

IOL_USER = os.environ["IOL_USER"]
IOL_PASS = os.environ["IOL_PASS"]

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "d": "http://schemas.microsoft.com/ado/2007/08/dataservices",
    "m": "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata",
}

# Escenarios de referencia para la conversión riesgo-país -> probabilidad.
# Son una hipótesis del analista, no un dato de mercado — se pueden ajustar.
MILEI_ANCHOR_BPS = 250
PERONISMO_ANCHOR_BPS = 2000

AO27C = {
    "maturity": date(2027, 10, 29),
    "cashflows": [
        (date(2026, 9, 30), 0.5), (date(2026, 10, 31), 0.5), (date(2026, 11, 30), 0.5),
        (date(2026, 12, 31), 0.5), (date(2027, 1, 31), 0.5), (date(2027, 2, 28), 0.5),
        (date(2027, 3, 31), 0.5), (date(2027, 4, 30), 0.5), (date(2027, 5, 31), 0.5),
        (date(2027, 6, 30), 0.5), (date(2027, 7, 31), 0.5), (date(2027, 8, 31), 0.5),
        (date(2027, 9, 30), 0.5), (date(2027, 10, 29), 100.5),
    ],
}
AO28C = {
    "maturity": date(2028, 10, 31),
    "cashflows": [
        (date(2026, 9, 30), 0.5), (date(2026, 10, 31), 0.5), (date(2026, 11, 30), 0.5),
        (date(2026, 12, 31), 0.5), (date(2027, 1, 31), 0.5), (date(2027, 2, 28), 0.5),
        (date(2027, 3, 31), 0.5), (date(2027, 4, 30), 0.5), (date(2027, 5, 31), 0.5),
        (date(2027, 6, 30), 0.5), (date(2027, 7, 31), 0.5), (date(2027, 8, 31), 0.5),
        (date(2027, 9, 30), 0.5), (date(2027, 10, 31), 0.5), (date(2027, 11, 30), 0.5),
        (date(2027, 12, 31), 0.5), (date(2028, 1, 31), 0.5), (date(2028, 2, 29), 0.5),
        (date(2028, 3, 31), 0.5), (date(2028, 4, 30), 0.5), (date(2028, 5, 31), 0.5),
        (date(2028, 6, 30), 0.5), (date(2028, 7, 31), 0.5), (date(2028, 8, 31), 0.5),
        (date(2028, 9, 30), 0.5), (date(2028, 10, 31), 100.5),
    ],
}


def iol_token():
    r = requests.post(
        "https://api.invertironline.com/token",
        data={"username": IOL_USER, "password": IOL_PASS, "grant_type": "password"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def iol_price(token, simbolo, mercado="bCBA"):
    url = f"https://api.invertironline.com/api/{mercado}/Titulos/{simbolo}/Cotizacion"
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "ultimoPrecio" not in data:
        raise RuntimeError(f"Campo 'ultimoPrecio' no encontrado en la respuesta de {simbolo}: {data}")
    return float(data["ultimoPrecio"])


def irr_from_cashflows(price, cashflows, settlement):
    def npv(rate):
        total = -price
        for d, cf in cashflows:
            t = (d - settlement).days / 365.0
            if t <= 0:
                continue
            total += cf / (1 + rate) ** t
        return total

    lo, hi = -0.5, 2.0
    if npv(lo) * npv(hi) > 0:
        raise RuntimeError("No se encontró una TIR en el rango [-50%, 200%] — revisar precio/flujos")
    for _ in range(100):
        mid = (lo + hi) / 2
        if npv(lo) * npv(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def ust_curve(year):
    url = (
        "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/"
        f"pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value={year}"
    )
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    entries = root.findall("atom:entry", NS)
    if not entries:
        raise RuntimeError(f"El feed de UST para {year} no devolvió entradas")
    last = entries[-1]
    props = last.find("atom:content/m:properties", NS)

    def get(tag):
        el = props.find(f"d:{tag}", NS)
        return float(el.text) / 100.0 if el is not None and el.text else None

    return {1: get("BC_1YEAR"), 2: get("BC_2YEAR"), 3: get("BC_3YEAR")}


def interp(curve, t):
    pts = sorted((k, v) for k, v in curve.items() if v is not None)
    if t <= pts[0][0]:
        return pts[0][1]
    if t >= pts[-1][0]:
        return pts[-1][1]
    for (t0, y0), (t1, y1) in zip(pts, pts[1:]):
        if t0 <= t <= t1:
            return y0 + (t - t0) / (t1 - t0) * (y1 - y0)


def forward_rate(y1, t1, y2, t2):
    return ((1 + y2) ** t2 / (1 + y1) ** t1) ** (1 / (t2 - t1)) - 1


def main():
    settlement = date.today()
    token = iol_token()

    p27 = iol_price(token, "AO27C")
    p28 = iol_price(token, "AO28C")

    y27 = irr_from_cashflows(p27, AO27C["cashflows"], settlement)
    y28 = irr_from_cashflows(p28, AO28C["cashflows"], settlement)

    t27 = (AO27C["maturity"] - settlement).days / 365
    t28 = (AO28C["maturity"] - settlement).days / 365

    f_sob = forward_rate(y27, t27, y28, t28)

    curve = ust_curve(settlement.year)
    f_ust = forward_rate(interp(curve, t27), t27, interp(curve, t28), t28)

    rp_fwd_bps = (f_sob - f_ust) * 10000
    prob = (PERONISMO_ANCHOR_BPS - rp_fwd_bps) / (PERONISMO_ANCHOR_BPS - MILEI_ANCHOR_BPS)
    prob = max(0.0, min(1.0, prob))

    record = {
        "date": settlement.isoformat(),
        "ao27c_tir": round(y27 * 100, 3),
        "ao28c_tir": round(y28 * 100, 3),
        "forward_soberano": round(f_sob * 100, 3),
        "forward_ust": round(f_ust * 100, 3),
        "riesgo_pais_forward_bps": round(rp_fwd_bps, 1),
        "milei_anchor_bps": MILEI_ANCHOR_BPS,
        "peronismo_anchor_bps": PERONISMO_ANCHOR_BPS,
        "prob_milei": round(prob * 100, 2),
    }

    path = os.path.join(os.path.dirname(__file__), "..", "data", "history.json")
    history = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            history = json.load(f)
    history = [h for h in history if h["date"] != record["date"]]
    history.append(record)
    history.sort(key=lambda h: h["date"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    print(json.dumps(record, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
