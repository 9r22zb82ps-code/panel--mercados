"""
Panel de Mercados: genera index.html con los cierres diarios de Yahoo Finance.

Uso:
    python generar.py            # datos reales (necesita internet y yfinance)
    python generar.py --demo     # datos sintéticos, para probar el diseño

Para añadir o quitar valores, edita UNIVERSO más abajo. Cualquier ticker que
exista en finance.yahoo.com vale (acciones, ETFs, índices con ^, divisas =X,
futuros =F, cripto -USD).
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PLANTILLA = AQUI / "plantilla.html"
MARCA = "/*__DATOS__*/null"

# --------------------------------------------------------------------------
# Universo. "ref" es el índice o ETF contra el que se mide la fuerza relativa.
# tipo "tipo" en un valor: "rend" (rentabilidad de interés, se muestra en pb)
# --------------------------------------------------------------------------
UNIVERSO = [
    {
        "id": "resumen",
        "nombre": "Resumen",
        "ref": None,
        "valores": [
            ("^GSPC", "S&P 500"),
            ("^NDX", "Nasdaq 100"),
            ("^RUT", "Russell 2000"),
            ("^STOXX50E", "Euro Stoxx 50"),
            ("^IBEX", "IBEX 35"),
            ("^N225", "Nikkei 225"),
            ("EEM", "MSCI Emergentes"),
            ("^VIX", "VIX"),
            ("^TNX", "T-Note 10 años", "rend"),
            ("EURUSD=X", "EUR/USD"),
            ("BZ=F", "Brent"),
            ("GC=F", "Oro"),
            ("BTC-USD", "Bitcoin"),
        ],
    },
    {
        "id": "sectores-eeuu",
        "nombre": "Sectores EE. UU.",
        "ref": "SPY",
        "refNombre": "S&P 500 (SPY)",
        "valores": [
            ("XLK", "Tecnología"),
            ("XLC", "Comunicaciones"),
            ("XLY", "Consumo discrecional"),
            ("XLF", "Financiero"),
            ("XLI", "Industria"),
            ("XLV", "Salud"),
            ("XLP", "Consumo básico"),
            ("XLE", "Energía"),
            ("XLB", "Materiales"),
            ("XLU", "Utilities"),
            ("XLRE", "Inmobiliario"),
        ],
    },
    {
        "id": "estilos",
        "nombre": "Estilos y factores",
        "ref": "SPY",
        "refNombre": "S&P 500 (SPY)",
        "valores": [
            ("QQQ", "Nasdaq 100"),
            ("RSP", "S&P 500 equiponderado"),
            ("IJH", "Mid caps"),
            ("IWM", "Small caps"),
            ("IWF", "Growth"),
            ("IWD", "Value"),
            ("MTUM", "Momentum"),
            ("QUAL", "Calidad"),
            ("USMV", "Mínima volatilidad"),
        ],
    },
    {
        "id": "tematicos",
        "nombre": "Temáticos",
        "ref": "SPY",
        "refNombre": "S&P 500 (SPY)",
        "valores": [
            ("SMH", "Semiconductores"),
            ("IGV", "Software"),
            ("AIQ", "Inteligencia artificial"),
            ("CIBR", "Ciberseguridad"),
            ("SKYY", "Cloud"),
            ("BOTZ", "Robótica"),
            ("ITA", "Aeroespacial y defensa"),
            ("XBI", "Biotecnología"),
            ("PAVE", "Infraestructura EE. UU."),
            ("ICLN", "Energía limpia"),
            ("TAN", "Solar"),
            ("URA", "Uranio"),
            ("LIT", "Litio y baterías"),
            ("GDX", "Mineras de oro"),
            ("ARKK", "Innovación disruptiva"),
        ],
    },
    {
        "id": "europa",
        "nombre": "Europa",
        "ref": "EXSA.DE",
        "refNombre": "STOXX Europe 600 (EXSA)",
        "valores": [
            ("EXV1.DE", "Bancos"),
            ("EXH5.DE", "Seguros"),
            ("EXV3.DE", "Tecnología"),
            ("EXV4.DE", "Salud"),
            ("EXH4.DE", "Industria"),
            ("EXH1.DE", "Petróleo y gas"),
            ("EXV6.DE", "Recursos básicos"),
            ("EXH9.DE", "Utilities"),
            ("EXV5.DE", "Automóvil"),
            ("EXH3.DE", "Alimentación y bebidas"),
            ("EXH7.DE", "Consumo personal y lujo"),
            ("EXV2.DE", "Telecomunicaciones"),
            ("EXV8.DE", "Construcción"),
            ("EXI5.DE", "Inmobiliario"),
            ("^GDAXI", "Alemania · DAX"),
            ("^FCHI", "Francia · CAC 40"),
            ("^IBEX", "España · IBEX 35"),
            ("FTSEMIB.MI", "Italia · FTSE MIB"),
            ("^AEX", "Países Bajos · AEX"),
            ("^FTSE", "Reino Unido · FTSE 100"),
            ("^SSMI", "Suiza · SMI"),
        ],
    },
    {
        "id": "emergentes",
        "nombre": "Emergentes",
        "ref": "EEM",
        "refNombre": "MSCI Emergentes (EEM)",
        "valores": [
            ("MCHI", "China"),
            ("KWEB", "China internet"),
            ("INDA", "India"),
            ("EWT", "Taiwán"),
            ("EWY", "Corea del Sur"),
            ("EWZ", "Brasil"),
            ("EWW", "México"),
            ("EZA", "Sudáfrica"),
            ("EWJ", "Japón (desarrollado)"),
            ("ACWI", "MSCI Mundo (ACWI)"),
        ],
    },
    {
        "id": "macro",
        "nombre": "Macro",
        "ref": None,
        "valores": [
            ("^FVX", "T-Note 5 años", "rend"),
            ("^TNX", "T-Note 10 años", "rend"),
            ("^TYX", "T-Bond 30 años", "rend"),
            ("TLT", "Bonos EE. UU. 20+ años"),
            ("LQD", "Crédito investment grade"),
            ("HYG", "Crédito high yield"),
            ("DX-Y.NYB", "Índice dólar (DXY)"),
            ("EURUSD=X", "EUR/USD"),
            ("USDJPY=X", "USD/JPY"),
            ("GC=F", "Oro"),
            ("SI=F", "Plata"),
            ("HG=F", "Cobre"),
            ("BZ=F", "Brent"),
            ("NG=F", "Gas natural (Henry Hub)"),
            ("BTC-USD", "Bitcoin"),
            ("^VIX", "VIX"),
        ],
    },
]


def tickers_necesarios() -> tuple[list[str], dict]:
    meta: dict[str, dict] = {}
    for g in UNIVERSO:
        if g.get("ref"):
            meta.setdefault(g["ref"], {"nombre": g.get("refNombre", g["ref"]), "tipo": "precio"})
        for v in g["valores"]:
            t, nombre = v[0], v[1]
            tipo = v[2] if len(v) > 2 else "precio"
            meta.setdefault(t, {"nombre": nombre, "tipo": tipo})
    return list(meta), meta


# --------------------------------------------------------------------------
# Descarga real
# --------------------------------------------------------------------------
def descargar(tickers: list[str], periodo: str = "2y") -> dict[str, list[tuple[str, float]]]:
    import pandas as pd
    import yfinance as yf

    datos = yf.download(
        tickers,
        period=periodo,
        interval="1d",
        auto_adjust=True,
        group_by="ticker",
        progress=False,
        threads=True,
    )
    series: dict[str, list[tuple[str, float]]] = {}
    for t in tickers:
        try:
            col = datos[t]["Close"] if isinstance(datos.columns, pd.MultiIndex) else datos["Close"]
        except KeyError:
            print(f"  aviso: sin datos para {t}", file=sys.stderr)
            continue
        col = col.dropna()
        if col.empty:
            print(f"  aviso: sin datos para {t}", file=sys.stderr)
            continue
        series[t] = [(idx.strftime("%Y-%m-%d"), round(float(v), 4)) for idx, v in col.items()]
    return series


# --------------------------------------------------------------------------
# Datos de demostración (sintéticos)
# --------------------------------------------------------------------------
def dias_habiles(fin: date, n: int) -> list[date]:
    dias, d = [], fin
    while len(dias) < n:
        if d.weekday() < 5:
            dias.append(d)
        d -= timedelta(days=1)
    return dias[::-1]


NIVELES_DEMO = {
    "^GSPC": 4800, "^NDX": 17000, "^RUT": 2000, "^STOXX50E": 4500, "^IBEX": 10500,
    "^N225": 36000, "^VIX": 16, "EURUSD=X": 1.08, "USDJPY=X": 150, "DX-Y.NYB": 103,
    "BZ=F": 78, "GC=F": 2100, "SI=F": 24, "HG=F": 4, "NG=F": 2.8, "BTC-USD": 45000,
    "^GDAXI": 17000, "^FCHI": 7500, "FTSEMIB.MI": 31000, "^AEX": 820, "^FTSE": 7700, "^SSMI": 11200,
}


def generar_demo(tickers: list[str], meta: dict) -> dict[str, list[tuple[str, float]]]:
    rnd = random.Random(20261105)
    fechas = dias_habiles(date.today() - timedelta(days=1), 504)
    mercado = [rnd.gauss(0.0004, 0.009) for _ in fechas]
    series = {}
    for t in tickers:
        tipo = meta[t]["tipo"]
        beta = rnd.uniform(0.5, 1.5)
        deriva = rnd.gauss(0.0, 0.0006)
        giro = rnd.uniform(0.2, 0.8)
        vol = rnd.uniform(0.004, 0.012)
        nivel = NIVELES_DEMO.get(t, 4.2 if tipo == "rend" else rnd.uniform(20, 600))
        if t in ("EURUSD=X", "USDJPY=X", "DX-Y.NYB"):
            beta, vol, deriva = 0.05, 0.003, deriva / 4
        pts = []
        for i, f in enumerate(fechas):
            fase = math.sin(i / 504 * math.pi * 2 * giro + beta * 3)
            if tipo == "rend":
                nivel = max(0.5, nivel + rnd.gauss(0, 0.04))
            else:
                r = beta * mercado[i] + deriva * fase * 2 + rnd.gauss(0, vol)
                nivel *= math.exp(r)
            pts.append((f.isoformat(), round(nivel, 4)))
        series[t] = pts
    return series


# --------------------------------------------------------------------------
def construir(series: dict, meta: dict, demo: bool) -> dict:
    grupos = []
    for g in UNIVERSO:
        grupos.append({
            "id": g["id"],
            "nombre": g["nombre"],
            "ref": g.get("ref"),
            "valores": [v[0] for v in g["valores"] if v[0] in series],
        })
    return {
        "generado": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "demo": demo,
        "grupos": grupos,
        "meta": {t: meta[t] for t in series},
        "series": {t: {"f": [p[0] for p in s], "c": [p[1] for p in s]} for t, s in series.items()},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="usar datos sintéticos")
    ap.add_argument("--salida", default=str(AQUI / "web" / "index.html"))
    args = ap.parse_args()

    tickers, meta = tickers_necesarios()
    print(f"{len(tickers)} tickers")
    series = generar_demo(tickers, meta) if args.demo else descargar(tickers)
    if not series:
        sys.exit("No se ha podido descargar ningún dato.")
    faltan = [t for t in tickers if t not in series]
    if faltan:
        print("Sin datos:", ", ".join(faltan), file=sys.stderr)

    datos = construir(series, meta, args.demo)
    plantilla = PLANTILLA.read_text(encoding="utf-8")
    if MARCA not in plantilla:
        sys.exit("La plantilla no contiene la marca de datos.")
    carga = json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = plantilla.replace(MARCA, carga)

    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(html, encoding="utf-8")
    print(f"Escrito {salida} ({len(html) / 1024:.0f} KB, {len(series)} series)")


if __name__ == "__main__":
    main()
