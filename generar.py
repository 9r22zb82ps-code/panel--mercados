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
        "id": "fondos-ft",
        "nombre": "Fondos FT",
        "ref": None,
        "nota": "Valor liquidativo de la clase institucional frente a su índice de referencia "
                "(franklintempleton.com.es), medido con un ETF que lo replica.",
        # Cada fondo: ticker de Yahoo del VL, nombre, clase, ISIN, ticker del índice,
        # nombre del índice oficial y, si el ETF no replica exactamente ese índice, qué replica.
        "fondos": [
            {"t": "0P0000OQVK.F", "nombre": "Putnam US Research", "clase": "PR EUR Acc",
             "isin": "IE00B241FQ36", "ref": "SXR8.DE", "indice": "S&P 500 NR",
             "proxy": None},
            {"t": "0P0000G0R3.F", "nombre": "Franklin Technology", "clase": "I (acc) EUR",
             "isin": "LU0366762994", "ref": "XDWT.DE",
             "indice": "MSCI ACWI IT + Communication Services 10/40 NR",
             "proxy": "MSCI World IT (índice secundario del fondo)"},
            {"t": "0P000199LG.F", "nombre": "ClearBridge Infrastructure Value", "clase": "PR EUR Acc",
             "isin": "IE00BD4GV124", "ref": "IQQI.DE",
             "indice": "FTSE Global Core Infrastructure 50/50 NR",
             "proxy": "FTSE Global Core Infrastructure (sin el 50/50)"},
            {"t": "0P0000O30I", "nombre": "Franklin Gold and Precious Metals", "clase": "I (acc) USD",
             "isin": "LU0496368654", "ref": "GDX", "indice": "FTSE Gold Mines",
             "proxy": "NYSE Arca Gold Miners (GDX)"},
            {"t": "0P000125XH.F", "nombre": "Franklin Euro Short Duration", "clase": "I (acc) EUR",
             "isin": "LU1022658824", "ref": "IBGS.AS", "indice": "Bloomberg Euro Aggregate 1-3 años",
             "proxy": "Deuda pública euro 1-3 años"},
            {"t": "0P00000YQE.F", "nombre": "Franklin European Total Return", "clase": "I (acc) EUR",
             "isin": "LU0195952774", "ref": "SYBA.DE", "indice": "Bloomberg Euro Aggregate",
             "proxy": None},
        ],
        "valores": [],
    },
    {
        "id": "tipos",
        "nombre": "Tipos y crédito",
        "ref": None,
        "valores": [],
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
        for f in g.get("fondos", []):
            meta.setdefault(f["t"], {"nombre": f"{f['nombre']} {f['clase']}", "tipo": "precio"})
            meta.setdefault(f["ref"], {"nombre": f["indice"], "tipo": "precio"})
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
# Tipos, curvas y diferenciales de crédito (FRED y Banco Central Europeo)
# --------------------------------------------------------------------------
# tipo: "tasa" = tipo de interés en %, "spread" = diferencial en % que se muestra en pb.
# inv: True cuando una subida es mala noticia (diferenciales que se amplían).
TIPOS = [
    # clave interna, fuente, código, nombre, tipo, inv
    ("FED_TECHO", "fred", "DFEDTARU", "Fed funds (techo del rango)", "tasa", False),
    ("FED_SUELO", "fred", "DFEDTARL", "Fed funds (suelo del rango)", "tasa", False),
    ("EFFR", "fred", "EFFR", "Fed funds efectivo", "tasa", False),
    ("UST1A", "fred", "DGS1", "Treasury 1 año", "tasa", False),
    ("UST2A", "fred", "DGS2", "Treasury 2 años", "tasa", False),
    ("UST10A", "fred", "DGS10", "Treasury 10 años", "tasa", False),
    ("US2S10S", "fred", "T10Y2Y", "Pendiente EE. UU. 10a-2a", "spread", False),
    ("BCE_DEPO", "fred", "ECBDFR", "BCE facilidad de depósito", "tasa", False),
    ("ESTR", "fred", "ECBESTRVOLWGTTRMDMNRT", "€STR", "tasa", False),
    ("EUR1A", "bce", "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_1Y", "Deuda AAA euro 1 año", "tasa", False),
    ("EUR2A", "bce", "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y", "Deuda AAA euro 2 años", "tasa", False),
    ("EUR10A", "bce", "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y", "Deuda AAA euro 10 años", "tasa", False),
    ("EURTODOS10A", "bce", "YC/B.U2.EUR.4F.G_N_C.SV_C_YM.SR_10Y", "Deuda euro 10 años (todos los ratings)", "tasa", False),
    ("OAS_US_IG", "fred", "BAMLC0A0CM", "Crédito IG EE. UU.", "spread", True),
    ("OAS_US_HY", "fred", "BAMLH0A0HYM2", "High yield EE. UU.", "spread", True),
    ("OAS_EU_HY", "fred", "BAMLHE00EHYIOAS", "High yield euro", "spread", True),
    ("OAS_EM", "fred", "BAMLEMCBPIOAS", "Crédito corporativo emergente", "spread", True),
]
# Series calculadas a partir de otras: clave, (a, b) -> a - b
DERIVADAS = [
    ("EUR2S10S", ("EUR10A", "EUR2A"), "Pendiente euro AAA 10a-2a", "spread", False),
    ("EUR_SOBERANO", ("EURTODOS10A", "EUR10A"), "Prima soberana euro 10a (todos vs AAA)", "spread", True),
]
PROYECCIONES_FED = ("FEDTARMD", "FEDTARMDLR")  # medianas del FOMC por año y a largo plazo


NAVEGADOR = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


def _get(url: str, timeout: int = 20) -> str:
    from urllib.request import Request, urlopen
    req = Request(url, headers={"User-Agent": NAVEGADOR, "Accept": "text/csv,*/*"})
    with urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def _fred(codigo: str, desde: str | None) -> list[tuple[str, float]]:
    """FRED: API oficial si hay clave (secreto FRED_API_KEY), si no la descarga CSV pública."""
    import os
    clave = os.environ.get("FRED_API_KEY", "").strip()
    out = []
    if clave:
        url = (f"https://api.stlouisfed.org/fred/series/observations?series_id={codigo}"
               f"&api_key={clave}&file_type=json" + (f"&observation_start={desde}" if desde else ""))
        for o in json.loads(_get(url))["observations"]:
            try:
                out.append((o["date"], round(float(o["value"]), 4)))
            except ValueError:
                pass
        return out
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={codigo}" + (f"&cosd={desde}" if desde else "")
    for fila in _get(url).strip().splitlines()[1:]:
        f, _, v = fila.partition(",")
        try:
            out.append((f, round(float(v), 4)))
        except ValueError:
            pass  # días sin dato ('.')
    return out


def _bce(clave: str, desde: str) -> list[tuple[str, float]]:
    flujo, _, serie = clave.partition("/")
    url = f"https://data-api.ecb.europa.eu/service/data/{flujo}/{serie}?format=csvdata&startPeriod={desde}"
    import csv, io
    out = []
    for fila in csv.DictReader(io.StringIO(_get(url))):
        try:
            out.append((fila["TIME_PERIOD"], round(float(fila["OBS_VALUE"]), 4)))
        except (KeyError, ValueError):
            pass
    return out


def derivar(series: dict) -> None:
    for clave, (a, b), *_ in DERIVADAS:
        if a in series and b in series:
            mb = dict(series[b])
            series[clave] = [(f, round(v - mb[f], 4)) for f, v in series[a] if f in mb]


def descargar_tipos() -> tuple[dict, dict]:
    desde = (date.today() - timedelta(days=3 * 365)).isoformat()
    series = {}
    fallos_fred = 0
    for clave, fuente, codigo, *_ in TIPOS:
        if fuente == "fred" and fallos_fred >= 2:
            print(f"  aviso: FRED no responde, se omite {clave}", file=sys.stderr)
            continue
        try:
            datos = _fred(codigo, desde) if fuente == "fred" else _bce(codigo, desde)
            if datos:
                series[clave] = datos
            else:
                print(f"  aviso: sin datos para {clave} ({codigo})", file=sys.stderr)
        except Exception as e:  # una fuente caída no debe tumbar el panel
            print(f"  aviso: fallo al descargar {clave} ({codigo}): {e}", file=sys.stderr)
            fallos_fred += fuente == "fred"
    derivar(series)
    proy = {}
    try:
        if fallos_fred >= 2:
            raise RuntimeError("FRED no responde")
        anio = date.today().year
        proy["anual"] = [(f[:4], v) for f, v in _fred(PROYECCIONES_FED[0], None) if int(f[:4]) >= anio]
        lr = _fred(PROYECCIONES_FED[1], None)
        proy["largo"] = lr[-1][1] if lr else None
        proy["fecha"] = lr[-1][0] if lr else None
    except Exception as e:
        print(f"  aviso: sin proyecciones del FOMC: {e}", file=sys.stderr)
    return series, proy


def meta_tipos() -> dict:
    meta = {}
    for clave, _, codigo, nombre, tipo, inv in TIPOS:
        fuente = f"FRED · {codigo}" if codigo.isalnum() else "BCE · curva de tipos " + ("AAA" if "G_N_A" in codigo else "todos los ratings")
        meta[clave] = {"nombre": nombre, "tipo": tipo, "inv": inv, "fuente": fuente}
    for clave, _, nombre, tipo, inv in DERIVADAS:
        meta[clave] = {"nombre": nombre, "tipo": tipo, "inv": inv, "fuente": "Calculada con la curva del BCE"}
    return meta


def demo_tipos() -> tuple[dict, dict]:
    rnd = random.Random(7)
    fechas = [f.isoformat() for f in dias_habiles(date.today() - timedelta(days=1), 750)]
    base = {"FED_TECHO": 4.0, "FED_SUELO": 3.75, "EFFR": 3.87, "UST1A": 3.55, "UST2A": 3.45,
            "UST10A": 4.15, "US2S10S": 0.7, "BCE_DEPO": 2.0, "ESTR": 1.92, "EUR1A": 1.85,
            "EUR2A": 1.95, "EUR10A": 2.55, "EURTODOS10A": 3.05, "OAS_US_IG": 0.85,
            "OAS_US_HY": 3.1, "OAS_EU_HY": 3.2, "OAS_EM": 1.9}
    series = {}
    for clave, *_ in TIPOS:
        n, pts = base[clave] + 1.0, []
        oficial = clave in ("FED_TECHO", "FED_SUELO", "BCE_DEPO")
        for i, f in enumerate(fechas):
            if oficial:
                n = base[clave] + 1.0 - 0.25 * min(4, i // 150)
            else:
                n = max(0.2, n + rnd.gauss(-0.0013, 0.03 if "OAS" not in clave else 0.02))
            pts.append((f, round(n, 4)))
        series[clave] = pts
    derivar(series)
    proy = {"anual": [(str(date.today().year), 3.6), (str(date.today().year + 1), 3.4),
                      (str(date.today().year + 2), 3.1)], "largo": 3.0, "fecha": "ejemplo"}
    return series, proy


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
    fondos = {f["t"]: f["ref"] for g in UNIVERSO for f in g.get("fondos", [])}
    series = {}
    for t in [x for x in tickers if x not in fondos] + [x for x in tickers if x in fondos]:
        if t in fondos and fondos[t] in series:
            base, nivel, pts = series[fondos[t]], rnd.uniform(20, 150), []
            alfa = rnd.gauss(0, 0.0002)
            for i, (f, v) in enumerate(base):
                if i:
                    r = math.log(v / base[i - 1][1]) + alfa + rnd.gauss(0, 0.002)
                    nivel *= math.exp(r)
                pts.append((f, round(nivel, 4)))
            series[t] = pts[:-1]  # el VL llega con un día de retraso
            continue
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
            "nota": g.get("nota"),
            "valores": [v[0] for v in g["valores"] if v[0] in series],
            "nombres": {v[0]: v[1] for v in g["valores"]},
            "fondos": [f for f in g.get("fondos", []) if f["t"] in series and f["ref"] in series],
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
    s_tipos, proyecciones = demo_tipos() if args.demo else descargar_tipos()
    series.update(s_tipos)
    meta.update(meta_tipos())
    if not series:
        sys.exit("No se ha podido descargar ningún dato.")
    faltan = [t for t in tickers if t not in series]
    if faltan:
        print("Sin datos:", ", ".join(faltan), file=sys.stderr)

    datos = construir(series, meta, args.demo)
    datos["proyeccionesFed"] = proyecciones
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
