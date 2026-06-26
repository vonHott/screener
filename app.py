# ======================================================================
# SCREENER DE REBOTES + FUNDAMENTAL — V FINAL (con 4 mejoras)
# Ejecuta automaticamente al cargar · Sin botones · Sin bandas
# 4 gatillos de rebote (EMA 50/200/325) + analisis fundamental
# Mejoras: filtro de regimen SPY, DI+/GIRO obligatorio, VALOR fuera del
#          score de swing, penalizacion de cuchillos de alta volatilidad
# ======================================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import math
import warnings
from concurrent.futures import ThreadPoolExecutor
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="Screener CRH",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');
:root {
    --bg:#080c14; --surface:#0d1220; --border:#1a2235; --border2:#243048;
    --text:#e2e8f0; --muted:#4a5568; --accent:#00d4ff;
    --green:#00e5a0; --red:#ff4d6d; --yellow:#ffd166; --purple:#b48cff;
}
html,body,[class*="css"]{font-family:'DM Mono',monospace;background:var(--bg)!important;color:var(--text)}
[data-testid="stSidebar"],[data-testid="collapsedControl"],#MainMenu,footer,header{display:none!important}
[data-testid="stHeaderActionElements"],.stMarkdown a.anchor-link,h1 a,h2 a,h3 a{display:none!important}
.block-container{padding:1rem 1.2rem 2rem!important;max-width:1500px!important}

.header{background:linear-gradient(135deg,var(--surface),#0f1928);border:1px solid var(--border2);border-radius:12px;padding:18px 24px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between}
.header h1{font-family:'Syne',sans-serif;font-size:clamp(15px,2.5vw,20px);font-weight:800;color:var(--text);margin:0 0 2px 0}
.header h1 span{color:var(--accent)}
.header p{color:var(--muted);font-size:10px;margin:0;letter-spacing:.08em}
.badge{background:#00d4ff15;border:1px solid #00d4ff44;color:var(--accent);font-size:10px;padding:4px 10px;border-radius:20px}

.idx-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px}
@media(max-width:700px){.idx-grid{grid-template-columns:1fr 1fr}}
.idx-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 14px}
.idx-label{color:var(--muted);font-size:9px;letter-spacing:.1em;text-transform:uppercase;margin-bottom:3px}
.idx-price{color:var(--text);font-size:clamp(14px,2vw,18px);font-weight:500}
.up{color:var(--green);font-size:11px}.down{color:var(--red);font-size:11px}

.ctx-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:16px}
@media(max-width:700px){.ctx-grid{grid-template-columns:1fr 1fr}}
.ctx-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 14px}
.ctx-label{color:var(--muted);font-size:9px;letter-spacing:.1em;text-transform:uppercase;margin-bottom:3px}
.ctx-val{color:var(--text);font-size:16px;font-weight:500}
.ctx-sub{font-size:11px;font-weight:500;margin-top:2px}
.ok{color:var(--green)}.warn{color:var(--yellow)}.bad{color:var(--red)}

.sec{font-family:'Syne',sans-serif;font-size:13px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:14px 0 6px;border-bottom:1px solid var(--border2);margin:18px 0 10px}
.sec-os{color:var(--green);border-bottom-color:var(--green)}
.sec-mas{color:var(--yellow);border-bottom-color:var(--yellow)}
.sec-bb{color:var(--accent);border-bottom-color:var(--accent)}
.sec-cr{color:var(--purple);border-bottom-color:var(--purple)}
.glosario{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 14px;margin-bottom:10px;font-size:11px;color:var(--muted);line-height:1.9}
.glosario b{color:#718096}
[data-testid="stDataFrame"]{border:1px solid var(--border)!important;border-radius:10px!important;font-family:'DM Mono',monospace!important;font-size:11px!important}
/* ===== TABLA HTML PERSONALIZADA — ticker-link + fila resaltada ===== */
.tw{overflow-x:auto;border:1px solid var(--border);border-radius:10px;margin-bottom:10px;-webkit-overflow-scrolling:touch}
.tw table{border-collapse:collapse;width:100%;font-family:'DM Mono',monospace;font-size:11px;white-space:nowrap}
.tw th{background:#0a0e18;color:#718096;font-weight:500;text-transform:uppercase;font-size:9px;letter-spacing:.06em;padding:9px 12px;text-align:right;border-bottom:1px solid var(--border2);position:sticky;top:0}
.tw th:first-child,.tw th:nth-child(2){text-align:left}
.tw td{padding:8px 12px;text-align:right;border-bottom:1px solid var(--border);color:var(--text)}
.tw td:first-child{text-align:right;color:var(--muted);font-size:10px}
.tw td:nth-child(2){text-align:left;font-weight:600}
.tw tr{transition:background .08s}
/* fila resaltada completa al pasar cursor o tocar */
.tw tbody tr:hover td{background:rgba(0,212,255,0.13)!important}
.tw tbody tr:active td{background:rgba(0,212,255,0.22)!important}
.tw a.tk{color:#00d4ff;text-decoration:none;font-weight:700;border-bottom:1px dotted #00d4ff55}
.tw a.tk:hover{border-bottom:1px solid #00d4ff}
.tw th{cursor:pointer;user-select:none}
.tw th:hover{color:#00d4ff;background:#0d1424}
.tw th .ar{margin-left:3px;font-size:8px;opacity:.7}
.footer{color:var(--border2);font-size:10px;text-align:center;padding:16px 0 4px}
</style>
""", unsafe_allow_html=True)

# ======================================================================
# WATCHLIST
# ======================================================================
TICKERS = [
    "CHWY","ALT","PLTR","RBRK","MORN","CBRS","ISRG","MDT","DG","EPAM",
    "BRK-B","NCLH","CLS","GILD","FSLR","RTX","PSX","NBIS","ZTS","FICO",
    "BAC","GS","NOW","RMBS","MRVL","COF","BHP","SOL-USD","BTI","SAP",
    "FDX","TME","INTU","SONY","COHR","GDDY","PM","TSM","CRDO","NNE",
    "NRG","BLK","ENPH","LMT","DPZ","IONQ","VRT","VRTX","MSFT","AAPL",
    "MMM","HD","GOOGL","EBAY","SOFI","MPWR","LULU","CPRT","ETN","TJX",
    "ADP","NEE","DHR","T","VZ","QQQ","MU","TXN","OKTA","ZS",
    "AFRM","GME","BABA","RIOT","ARM","XLP","XLK","XLI","XLV","XLE",
    "IWM","SPY","UBER","PYPL","INTC","LRCX","AMAT","REGN","SHOP","HOOD",
    "NET","CRWD","DDOG","SNOW","MDB","MARA","COIN","AVGO","CSCO","ACN",
    "LIN","TMO","LLY","ABBV","ABNB","MRNA","AMT","ASTS","PANW","APH",
    "SMCI","DELL","ANET","STX","WDC","RCL","BKNG","TMUS","DE","CRM",
    "ADBE","TGT","COST","CVX","XOM","GE","ABT","AMZN","BTC-USD","SOUN",
    "IBM","SMH","URA","CEG","NVO","MRK","SPOT","EQIX","BA","FCX",
    "AEM","MSTR","PEP","KO","WMT","PFE","DIS","JNJ","MCD","JPM",
    "MA","CAT","SBUX","PG","UNH","NVDA","NFLX","MELI","NKE","META",
    "ORCL","ASML","TSLA","AMD","QQQM","VOO","ACHR","LINK-USD","AVAX-USD",
    "CL=F","NG=F","SI=F","HG=F","GC=F","NQ=F",
    "EURUSD=X","USDCHF=X","GBPUSD=X","USDJPY=X","USDCOP=X","USDCLP=X","USDBRL=X",
    "ZIM","DLTR","BBY","WBD","GT","WYNN","MGM","SNAP","CVNA","ROKU",
    "HUM","ELV","UHS","ILMN","SWK","FNV","SBSW","GOLD","SQM","ALB",
    "GSK","AZN","BAYN.DE","ROG.SW","9988.HK",
    "GM","UPS","SYY","CNC","V","CL","ON","BUD","NXPI","WM",
    "HSY","TSN","TSCO","PINS","SPGI","MDLZ","SNDK","PSA","CMG","STLD",
    "CLF","ALK","IBKR","MCO","UNP","HON","HCA","MSCI","VST","CI",
    "LEVI","AZO","CSGP","HIVE","SCHW","ONDS","PRZO","WVE","NOK","NU",
    "LOW","DECK","NASA","XYZ","IGV","HMC","SIDU","ETH-USD","OTIS","ESLT",
    "BLZE","LITE","CRWV","HII","GFI","CLX","NVAX","ZBH","PSKY","FIG",
    "D","KEYS","B","IGM","PATH","U","TX","BMNR","UL","MNST",
    "QTUM","IYW","IP","ARKQ","BITX","ETHU","CRML","UA","XT","O",
    "CRCL","RACE","CMCSA",
]

# ======================================================================
# TICKERS COMPARTIDOS — leer/escribir desde GitHub Gist
# ======================================================================
import urllib.request, json as _json

GIST_ID = "00c849548b7f82e35530eb837df20a3a"

def finviz_url(sym):
    """URL de finviz para el ticker (limpia sufijos no soportados)."""
    base = sym.replace("-USD","").replace("=F","").replace("=X","")
    return f"https://finviz.com/quote.ashx?t={base}&p=d"

def _gist_token():
    try:
        return st.secrets["GITHUB_TOKEN"]
    except Exception:
        return None

@st.cache_data(ttl=60, show_spinner=False)
def leer_tickers_compartidos():
    """Lee la lista de tickers que agregaron los amigos desde el Gist."""
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = _json.loads(r.read().decode())
        contenido = data["files"]["tickers.txt"]["content"]
        # formato: tickers separados por coma o salto de linea
        items = [t.strip().upper() for t in contenido.replace("\n", ",").split(",")]
        return [t for t in items if t]
    except Exception:
        return []

def escribir_tickers_compartidos(lista):
    """Sobrescribe el Gist con la lista (ya deduplicada)."""
    token = _gist_token()
    if not token:
        return False, "No hay token configurado en Secrets."
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        payload = _json.dumps({
            "files": {"tickers.txt": {"content": ",".join(lista)}}
        }).encode()
        req = urllib.request.Request(url, data=payload, method="PATCH", headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })
        with urllib.request.urlopen(req, timeout=8) as r:
            return (r.status in (200, 201)), "ok"
    except Exception as e:
        return False, str(e)

import re as _re
def normalizar_ticker(t):
    """Normaliza formato yfinance: BRK.B -> BRK-B, mayusculas. Limpia simbolos."""
    t = t.strip().upper()
    t = t.replace("$", "").replace(" ", "")  # quitar $ y espacios internos
    t = t.replace(".B", "-B").replace(".A", "-A")
    return t

def ticker_valido(t):
    """Valida formato de ticker yfinance: letras/numeros + sufijos (-USD, =F, =X, .HK, etc).
    Rechaza nombres de empresa, texto libre, tickers muy largos."""
    if not t or len(t) > 12:
        return False
    # Formatos válidos: AAPL, BRK-B, BTC-USD, CL=F, EURUSD=X, 9988.HK, BAYN.DE, ROG.SW
    return bool(_re.match(r'^[A-Z0-9]{1,7}([\-\.=][A-Z0-9]{1,4})?$', t))


# ======================================================================
# FUNDAMENTALES — fair value, target 12M, P/E, P/B, P/S, consensus
# ======================================================================
def _num(s):
    """Convierte string de Finviz a float. '17.45'->17.45, '20.65%'->0.2065, '-'->None, '5.04B'->5.04e9."""
    if s is None: return None
    s = str(s).strip()
    if s in ("-", "", "—"): return None
    try:
        pct = s.endswith("%")
        s2 = s.replace("%", "").replace(",", "").replace("$", "")
        mult = 1.0
        if s2 and s2[-1] in "BMK":
            mult = {"B":1e9, "M":1e6, "K":1e3}[s2[-1]]
            s2 = s2[:-1]
        v = float(s2) * mult
        return v/100.0 if pct else v
    except Exception:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def fetch_finviz(sym):
    """Fundamentales desde Finviz (más completo, incluye crecimiento real EPS next 5Y)."""
    # Finviz no soporta cripto/forex/futuros/internacionales
    if any(x in sym for x in ['-USD','-F','=X','=F','.DE','.SW','.HK']):
        return None
    try:
        from finvizfinance.quote import finvizfinance
        # Finviz usa BRK-B con formato BRK-B; algunos con punto
        fv_sym = sym.replace("-", "-")
        stock = finvizfinance(fv_sym)
        f = stock.ticker_fundament()
        if not f or not isinstance(f, dict):
            return None

        # Target price y Recom
        target = _num(f.get("Target Price"))
        recom  = _num(f.get("Recom"))  # 1=Strong Buy .. 5=Sell

        # Crecimiento: prioriza EPS next 5Y, luego EPS next Y
        growth = _num(f.get("EPS next 5Y"))
        if growth is None:
            growth = _num(f.get("EPS next Y"))

        return {
            "target_mean":  target,
            "n_analysts":   None,            # Finviz no da número de analistas
            "rec_mean":     recom,
            "pe_ttm":       _num(f.get("P/E")),
            "pe_fwd":       _num(f.get("Forward P/E")),
            "eps_ttm":      _num(f.get("EPS (ttm)")),
            "fwd_eps":      None,             # se deriva si hace falta
            "book_value":   _num(f.get("Book/sh")),
            "growth":       growth,
            "_fuente":      "finviz",
        }
    except Exception:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def fetch_yf(sym):
    """Fundamentales desde yfinance (respaldo)."""
    import time
    for intento in range(2):
        try:
            info = yf.Ticker(sym).info
            if info and len(info) >= 10 and (info.get("targetMeanPrice") or info.get("trailingPE") or info.get("trailingEps")):
                return {
                    "target_mean":   info.get("targetMeanPrice"),
                    "n_analysts":    info.get("numberOfAnalystOpinions"),
                    "rec_mean":      info.get("recommendationMean"),
                    "pe_ttm":        info.get("trailingPE"),
                    "pe_fwd":        info.get("forwardPE"),
                    "eps_ttm":       info.get("trailingEps"),
                    "fwd_eps":       info.get("forwardEps"),
                    "book_value":    info.get("bookValue"),
                    "growth":        info.get("earningsGrowth"),
                    "_fuente":       "yfinance",
                }
        except Exception:
            pass
        time.sleep(0.4 * (intento + 1))
    return None

@st.cache_data(ttl=300, show_spinner=False)
def fetch_fundamentales(sym):
    """Finviz como fuente principal (más completa). yfinance como respaldo.
    Rellena huecos de uno con el otro."""
    fv = fetch_finviz(sym)
    yf_data = None

    # Si Finviz falló por completo, usar yfinance
    if fv is None:
        return fetch_yf(sym)

    # Si Finviz no trae target o rec, completar con yfinance
    if fv.get("target_mean") is None or fv.get("rec_mean") is None:
        yf_data = fetch_yf(sym)
        if yf_data:
            if fv.get("target_mean") is None:
                fv["target_mean"] = yf_data.get("target_mean")
            if fv.get("rec_mean") is None:
                fv["rec_mean"] = yf_data.get("rec_mean")
            if fv.get("n_analysts") is None:
                fv["n_analysts"] = yf_data.get("n_analysts")

    return fv

def calc_upside(precio_actual, target_mean):
    """% entre precio actual y Target 12M de analistas. Devuelve (texto, raw, bajo_target)."""
    if not target_mean or target_mean <= 0:
        return ("—", None, False)
    up = (target_mean - precio_actual) / precio_actual * 100
    bajo_target = precio_actual < target_mean
    if up >= 15:   txt = f"🟢 +{up:.0f}%"
    elif up >= 0:  txt = f"⚪ +{up:.0f}%"
    elif up >= -10: txt = f"🟡 {up:.0f}%"
    else:          txt = f"🔴 {up:.0f}%"
    return (txt, up, bajo_target)


def calc_fair_value(fund, pe_hist, precio_actual):
    """FV: promedio de Graham + Forward P/E + Crecimiento descontado.
    Modelo original (el que mejor generaliza con datos gratuitos).
    Es un valor APROXIMADO por multiplos, no un veredicto. Validar en TSIT.
    Devuelve (texto_fv, upside_txt, upside_raw)."""
    import math as _math
    eps   = fund.get("eps_ttm")
    bv    = fund.get("book_value")
    feps  = fund.get("fwd_eps")
    g     = fund.get("growth")
    pe_fwd_val = fund.get("pe_fwd")

    modelos = []

    # Modelo 1: Graham sqrt(22.5 x EPS x BV) - ancla de valor conservadora
    if eps and bv and eps > 0 and bv > 0:
        modelos.append(_math.sqrt(22.5 * eps * bv))

    # P/E de referencia: TTM -> Forward -> 18 (mercado)
    if pe_hist and pe_hist > 0:
        pe_ref = pe_hist
    elif pe_fwd_val and pe_fwd_val > 0:
        pe_ref = pe_fwd_val
    else:
        pe_ref = 18.0
    pe_ok = max(8, min(pe_ref, 40))  # rango 8-40

    # Modelo 2: Forward EPS x P/E de referencia
    if feps and feps > 0:
        modelos.append(feps * pe_ok)

    # Modelo 3: EPS proyectado 5A con crecimiento (cap 25%), descontado al 10%
    if eps and eps > 0:
        gr = max(-0.05, min(g if g else 0.08, 0.25))
        modelos.append((eps * (1 + gr) ** 5 * pe_ok) / (1.10 ** 5))

    # Modelo 4: si hay EPS forward pero no TTM, estima con forward
    if (not eps or eps <= 0) and feps and feps > 0:
        gr = max(-0.05, min(g if g else 0.08, 0.25))
        modelos.append((feps * (1 + gr) ** 4 * pe_ok) / (1.10 ** 4))

    if not modelos:
        return ("—", "—", None)

    fv = sum(modelos) / len(modelos)

    up = (fv - precio_actual) / precio_actual * 100
    if up >= 15:   txt = f"🟢 +{up:.0f}%"
    elif up >= 0:  txt = f"⚪ +{up:.0f}%"
    elif up >= -15: txt = f"🟡 {up:.0f}%"
    else:          txt = f"🔴 {up:.0f}%"
    return (f"${fv:.0f}", txt, up)


def consenso(rec_mean, n_analysts):
    """recommendationMean (1-5) a texto + emoji. n analistas opcional."""
    if rec_mean is None or rec_mean <= 0:
        return "—"
    if rec_mean <= 1.5:   tag = "🟢 Strong Buy"
    elif rec_mean <= 2.5: tag = "🟢 Buy"
    elif rec_mean <= 3.5: tag = "⚪ Hold"
    elif rec_mean <= 4.5: tag = "🔴 Sell"
    else:                 tag = "🔴 Strong Sell"
    if n_analysts and n_analysts > 0:
        return f"{tag} ({int(n_analysts)})"
    return tag

# ======================================================================
# MARKET DATA
# ======================================================================
@st.cache_data(ttl=300, show_spinner=False)
def get_market_data():
    import math as _m
    # ^GSPC/^IXIC/^DJI fallan a veces uno por uno; descargar en batch es más fiable.
    indices = {"S&P 500":"^GSPC","Nasdaq":"^IXIC","Dow":"^DJI","Russell":"^RUT"}
    result = {}

    def _pct_de(h):
        """Extrae (precio, %) de un history, o None si no hay datos válidos."""
        try:
            cl = h['Close'].dropna()
            if len(cl) >= 2:
                prev = float(cl.iloc[-2]); curr = float(cl.iloc[-1])
                if prev > 0 and not _m.isnan(curr) and not _m.isnan(prev):
                    return curr, (curr - prev) / prev * 100
        except Exception:
            pass
        return None

    # Intento 1: batch (una sola petición para todos los índices)
    try:
        syms = list(indices.values())
        batch = yf.download(syms, period="5d", interval="1d",
                            group_by="ticker", progress=False, threads=True)
        for name, sym in indices.items():
            try:
                h = batch[sym] if sym in batch.columns.get_level_values(0) else None
                r = _pct_de(h) if h is not None else None
                if r: result[name] = {"price": r[0], "pct": r[1]}
            except Exception:
                pass
    except Exception:
        pass

    # Intento 2: lo que falte, individual (fallback)
    for name, sym in indices.items():
        if name in result:
            continue
        try:
            h = yf.Ticker(sym).history(period="5d", interval="1d")
            r = _pct_de(h)
            if r: result[name] = {"price": r[0], "pct": r[1]}
        except Exception:
            pass

    # Garantizar que SIEMPRE exista la clave (evita "nan" en la UI)
    for name in indices:
        if name not in result or result[name].get("price") in (None, 0) or _m.isnan(result[name].get("price", 0)):
            result.setdefault(name, {"price": None, "pct": None})

    vix = None
    try:
        h = yf.Ticker("^VIX").history(period="5d", interval="1d")
        cl = h['Close'].dropna()
        if len(cl) >= 1: vix = float(cl.iloc[-1])
    except Exception: pass

    btc_pct = None; btc_price = None
    try:
        h = yf.Ticker("BTC-USD").history(period="5d", interval="1d")
        cl = h['Close'].dropna()
        if len(cl) >= 2:
            btc_price = float(cl.iloc[-1])
            btc_pct = (btc_price - float(cl.iloc[-2])) / float(cl.iloc[-2]) * 100
    except Exception: pass

    return result, vix, btc_pct, btc_price

# ======================================================================
# REGIMEN DE MERCADO (CAMBIO 1) — SPY vs su EMA50
# ======================================================================
@st.cache_data(ttl=300, show_spinner=False)
def regimen_alcista():
    """True si el SPY cotiza sobre su EMA50 (régimen alcista).
    En downtrend castigamos los cuchillos (reversión sin DI+ y bajo su MA200)."""
    try:
        spy = yf.Ticker("SPY").history(period="1y")['Close'].dropna()
        if len(spy) < 50:
            return True                       # sin datos suficientes → neutral
        ema50 = spy.ewm(span=50, adjust=False).mean()
        return float(spy.iloc[-1]) > float(ema50.iloc[-1])
    except Exception:
        return True                           # ante fallo → no castigar

# ======================================================================
# ANALIZAR TICKER — 4 gatillos de rebote (recibe df ya descargado)
# Incluye: filtro DI+/GIRO (cambio 2) y penalización de cuchillo vol (cambio 4)
# ======================================================================
def analizar_ticker(sym, df):
    if df is None or df.empty or len(df) < 200:
        return None
    df = df.dropna(subset=['Close','Volume'])
    df = df[df['Volume']>0].copy()
    if len(df) < 200:
        return None

    # ── Medias (EMA 20/50/200/325) ──
    df['MA20']  = df['Close'].ewm(span=20,adjust=False).mean()
    df['MA50']  = df['Close'].ewm(span=50,adjust=False).mean()
    df['MA200'] = df['Close'].ewm(span=200,adjust=False).mean()
    df['MA325'] = df['Close'].ewm(span=325,adjust=False).mean()

    # ── ATR ──
    hl=(df['High']-df['Low']); hpc=(df['High']-df['Close'].shift(1)).abs(); lpc=(df['Low']-df['Close'].shift(1)).abs()
    df['ATR'] = pd.concat([hl,hpc,lpc],axis=1).max(axis=1).rolling(14).mean()

    # ── ADX (con DI+ / DI-) ──
    hd=df['High']-df['High'].shift(1); ld=df['Low'].shift(1)-df['Low']
    dmp=np.where((hd>0)&(hd>ld),hd,0); dmm=np.where((ld>0)&(ld>hd),ld,0)
    t14=pd.concat([hl,hpc,lpc],axis=1).max(axis=1).rolling(14).sum().replace(0,1e-8)
    pdi=pd.Series(dmp,index=df.index).rolling(14).sum()*100/t14
    mdi=pd.Series(dmm,index=df.index).rolling(14).sum()*100/t14
    df['PDI'] = pdi
    df['MDI'] = mdi
    df['ADX'] = (abs(pdi-mdi)/(pdi+mdi).replace(0,1e-8)*100).rolling(9).mean()

    # ── KDJ ──
    lm=df['Low'].rolling(9).min(); hm=df['High'].rolling(9).max()
    rsv=(df['Close']-lm)/(hm-lm).replace(0,1e-8)*100
    k=rsv.ewm(alpha=1/3,adjust=False).mean()
    d=k.ewm(alpha=1/3,adjust=False).mean()
    df['K']=k; df['D']=d; df['J']=3*k-2*d
    df['GIRO_J']   = df['J'] > df['J'].shift(1)
    df['CROSS_KD'] = (k>d) & (k.shift(1) <= d.shift(1))

    # ── RSI Wilder ──
    delta=df['Close'].diff(); gain=delta.clip(lower=0); loss=(-delta).clip(lower=0)
    df['RSI'] = 100-(100/(1+(gain.ewm(alpha=1/14,adjust=False).mean()/loss.ewm(alpha=1/14,adjust=False).mean().replace(0,1e-8))))

    # ── MACD ──
    dif = df['Close'].ewm(span=12,adjust=False).mean() - df['Close'].ewm(span=26,adjust=False).mean()
    dea = dif.ewm(span=9,adjust=False).mean()
    hist = dif - dea
    df['GIRO_MACD'] = (hist > hist.shift(1)) & (hist.shift(1) <= hist.shift(2))
    df['CROSS_MACD']= (dif > dea) & (dif.shift(1) <= dea.shift(1))

    # ── Bollinger ──
    df['BB_MID'] = df['Close'].rolling(20).mean()
    df['BB_STD'] = df['Close'].rolling(20).std(ddof=0)
    df['BB_DN']  = df['BB_MID'] - 2*df['BB_STD']

    # ── Volumen ──
    df['VOL_MA'] = df['Volume'].rolling(20).mean()
    df['VOL_OK'] = df['Volume'] > df['VOL_MA'] * 0.85

    rsi_v = float(df['RSI'].iloc[-1]) if not pd.isna(df['RSI'].iloc[-1]) else 50
    j_v   = float(df['J'].iloc[-1])   if not pd.isna(df['J'].iloc[-1])  else 50
    adx_v = float(df['ADX'].iloc[-1]) if not pd.isna(df['ADX'].iloc[-1]) else 0
    precio= float(df['Close'].iloc[-1])

    # ── ATR 14d en dólares (Wilder, estándar igual que RSI) — para SL/TP ──
    atr_abs = float(df['ATR'].iloc[-1]) if not pd.isna(df['ATR'].iloc[-1]) else 0

    # ── BANDA DE VOLATILIDAD (estilo CRH: STD de retornos 60d, suavizada 20d) ──
    ret = df['Close'].pct_change() * 100
    beta_raw = ret.rolling(60).std()
    beta_smooth = beta_raw.rolling(20).mean()
    bs_v = float(beta_smooth.iloc[-1]) if not pd.isna(beta_smooth.iloc[-1]) else 1.5
    # Banda 1 = tranquila, 2 = híbrida, 3 = volátil (mismos cortes que el CRH)
    if bs_v < 1.0:   banda = 1
    elif bs_v < 1.8: banda = 2
    else:            banda = 3
    banda_txt = {1:"🟦 B1", 2:"🟨 B2", 3:"🟥 B3"}[banda]

    ma50_v  = float(df['MA50'].iloc[-1])
    ma200_v = float(df['MA200'].iloc[-1])
    ma325_v = float(df['MA325'].iloc[-1])

    # ══════════════════════════════════════════════════════════
    # PUNTOS DE SCORE CON PESOS DIFERENCIADOS
    #   Giro confirmado = 2 (señal rara y potente)
    #   RSI, Toque, DI  = 1 cada uno  (techo técnico = 5)
    # ══════════════════════════════════════════════════════════

    # ── RSI < 35 (sobreventa) CON CONTEXTO de tendencia ──
    p_rsi = rsi_v < 35
    # sobreventa "sana" (sobre MA200) vs "en caída" (bajo MA200 = cuchillo cayendo)
    rsi_sana = p_rsi and precio > ma200_v

    # ── GIRO KDJ + CRUCE MACD + volumen + cierre sobre min ayer (PESO 2) ──
    cierre_sobre_min = precio > float(df['Low'].iloc[-2])
    vol_ok = bool(df['VOL_OK'].iloc[-1])
    p_giro = (
        bool(df['CROSS_KD'].iloc[-1] or df['CROSS_KD'].iloc[-2] or df['GIRO_J'].iloc[-1]) and
        bool(df['GIRO_MACD'].iloc[-1] or df['CROSS_MACD'].iloc[-1] or df['CROSS_MACD'].iloc[-2]) and
        cierre_sobre_min and
        vol_ok
    )

    # ── TOQUE DE SOPORTE — Bollinger inf. O EMA 50/200/325 desde arriba ──
    low_v   = float(df['Low'].iloc[-1])
    bb_dn_y = float(df['BB_DN'].iloc[-2])
    low_y   = float(df['Low'].iloc[-2])
    bb_dn   = float(df['BB_DN'].iloc[-1])

    toca_ema = (
        (low_v <= ma50_v  * 1.015 and precio > ma50_v  * 0.985) or
        (low_v <= ma200_v * 1.015 and precio > ma200_v * 0.985) or
        (low_v <= ma325_v * 1.015 and precio > ma325_v * 0.985)
    )
    toca_bb = (low_y <= bb_dn_y and precio > bb_dn)
    p_toque = (toca_ema or toca_bb) and cierre_sobre_min and vol_ok

    # ── DIRECCIÓN DI+ > DI- (cambio real vs trampa bajista) ──
    pdi_v = float(df['PDI'].iloc[-1]) if not pd.isna(df['PDI'].iloc[-1]) else 0
    mdi_v = float(df['MDI'].iloc[-1]) if not pd.isna(df['MDI'].iloc[-1]) else 0
    p_di = pdi_v > mdi_v

    if not (p_rsi or p_giro or p_toque):
        return None

    # Score técnico CON PESOS: Giro vale 2, el resto 1 (techo = 5)
    score_tecnico = (2 if p_giro else 0) + (1 if p_rsi else 0) + (1 if p_toque else 0) + (1 if p_di else 0)

    # ═══ CAMBIO 2: DI+/GIRO como confirmación obligatoria ═══
    # Reversión "desnuda" (sobreventa o toque) sin ningún giro real → es cuchillo
    if (p_rsi or p_toque) and not p_giro and not p_di:
        score_tecnico = max(0, score_tecnico - 1)

    # ═══ CAMBIO 4: castigar el perfil de cuchillo de alta volatilidad ═══
    if banda == 3 and precio < ma200_v:
        score_tecnico = max(0, score_tecnico - 1)      # B3 bajo MA200 = cae en vertical
    if banda == 3 and not (p_giro or p_di):
        score_tecnico = max(0, score_tecnico - 1)      # B3 sin confirmar = fuera del TOP

    return {
        "sym": sym,
        "precio": precio,
        "precio_str": f"${precio:.2f}",
        "rsi": rsi_v, "rsi_str": f"{rsi_v:.1f}",
        "j": j_v, "j_str": f"{j_v:.1f}",
        "adx": adx_v, "adx_str": f"{adx_v:.1f}",
        "score": score_tecnico,
        "p_rsi":   p_rsi,
        "rsi_sana": rsi_sana,
        "p_giro":  p_giro,
        "p_toque": p_toque,
        "p_di":    p_di,
        "atr_abs": atr_abs,
        "atr_str": f"${atr_abs:.2f}" if atr_abs > 0 else "—",
        "banda": banda,
        "banda_txt": banda_txt,
        "beta_smooth": bs_v,
        "ma200": ma200_v,          # ← CAMBIO 1: lo necesita el filtro de régimen
        # detalle de qué soporte tocó (para mostrar)
        "toca_ema": toca_ema,
        "toca_bb":  toca_bb,
    }

# ======================================================================
# HELPERS DE ESTILO
# ======================================================================
def cr(v):
    try:
        r=float(str(v))
        if r<33: return "color:#ff4d6d;font-weight:600"
        if r>65: return "color:#00e5a0;font-weight:600"
    except: pass
    return "color:#4a5568"
def cj(v):
    try:
        r=float(str(v))
        if r<20: return "color:#ff4d6d;font-weight:600"
        if r>80: return "color:#ffd166;font-weight:600"
    except: pass
    return "color:#4a5568"
def cs(v):
    s=str(v)
    if "🟢" in s: return "color:#00e5a0;font-weight:600"
    if "🔴" in s: return "color:#ff4d6d;font-weight:600"
    if "🟡" in s: return "color:#ffd166;font-weight:600"
    return "color:#4a5568"
def csc(v):
    try:
        n = int(v)
        if n >= 4: return "background-color:#003d25;color:#00e5a0;font-weight:700;text-align:center"
        if n == 3: return "background-color:#1e3a5f;color:#00d4ff;font-weight:600;text-align:center"
        if n == 2: return "background-color:#2d2540;color:#b48cff;font-weight:600;text-align:center"
    except: pass
    return "color:#4a5568;text-align:center"

# ======================================================================
# HEADER
# ======================================================================
st.markdown("""
<div class="header">
  <div>
    <h1>🔥 Rebote <span>Screener</span> 🔥</h1>
    <p>REBOTE EMA 50/200/325 · SOBREVENTA · BOLLINGER · KDJ+MACD · FUNDAMENTAL · FILTRO RÉGIMEN</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ======================================================================
# MARKET DATA
# ======================================================================
indices, vix, btc_pct, btc_price = get_market_data()
st.markdown('<div class="idx-grid">', unsafe_allow_html=True)
for name, data in indices.items():
    p=data.get("price"); pct=data.get("pct")
    if p is None or pct is None:
        # dato no disponible: mostrar guion en vez de "nan"
        st.markdown(f'<div class="idx-card"><div class="idx-label">{name}</div><div class="idx-price" style="color:#4a5568">—</div><div style="color:#4a5568">s/d</div></div>', unsafe_allow_html=True)
        continue
    cls="up" if pct>=0 else "down"; sig="+" if pct>=0 else ""
    st.markdown(f'<div class="idx-card"><div class="idx-label">{name}</div><div class="idx-price">{p:,.0f}</div><div class="{cls}">{sig}{pct:.2f}%</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

sp_pct=(indices.get("S&P 500",{}).get("pct") or 0)
_vix_val = vix if vix is not None else 0
vcls="ok" if _vix_val<18 else ("warn" if _vix_val<25 else "bad")
_btc_pct_val = btc_pct if btc_pct is not None else 0
bcls="up" if _btc_pct_val>=0 else "down"
bsig="+" if _btc_pct_val>=0 else ""
bp=f"${btc_price:,.0f}" if (btc_price and btc_price>0) else "—"

# Régimen del SPY (mismo criterio que usa el screener para castigar cuchillos)
_alcista_ui = regimen_alcista()
if _vix_val<18 and sp_pct>0 and _alcista_ui:   ctx_cls,ctx_txt="ok","✅ Condiciones favorables"
elif _vix_val>25 or sp_pct<-1 or not _alcista_ui: ctx_cls,ctx_txt="bad","⚠️ Mercado defensivo (cuchillos penalizados)" if not _alcista_ui else "⚠️ Mercado defensivo"
else:                          ctx_cls,ctx_txt="warn","⚪ Contexto mixto"

st.markdown(f"""
<div class="ctx-grid">
  <div class="ctx-card"><div class="ctx-label">VIX</div><div class="ctx-val">{(f"{_vix_val:.1f}" if vix is not None else "—")}</div><div class="ctx-sub {vcls}">{"✅ Tranquilo" if _vix_val<18 else ("⚠️ Moderado" if _vix_val<25 else "🔴 Alto")}</div></div>
  <div class="ctx-card"><div class="ctx-label">BTC</div><div class="ctx-val {bcls}">{bp}</div><div class="ctx-sub {bcls}">{(f"{bsig}{_btc_pct_val:.2f}%" if btc_pct is not None else "s/d")}</div></div>
  <div class="ctx-card"><div class="ctx-label">Régimen SPY</div><div class="ctx-val" style="font-size:12px;margin-top:4px;">&nbsp;</div><div class="ctx-sub {ctx_cls}" style="font-size:12px;">{("🟢 Alcista (>EMA50)" if _alcista_ui else "🔴 Bajista (<EMA50)")}</div></div>
</div>
""", unsafe_allow_html=True)

# ======================================================================
# BOX DE TICKERS COMPARTIDOS (amigos agregan, sin duplicar)
# ======================================================================
compartidos = leer_tickers_compartidos()

with st.expander(f"➕ Agregar tickers a la watchlist compartida ({len(compartidos)} agregados)", expanded=False):
    st.markdown('<div style="font-size:11px;color:#4a5568;margin-bottom:6px;">Escribe uno o varios tickers separados por coma (ej: <b>ALK, PYPL, V</b>). Se guardan para todos y no se repiten.</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([4,1])
    with col1:
        nuevos_input = st.text_input("Tickers", placeholder="ALK, PYPL, V", label_visibility="collapsed")
    with col2:
        agregar = st.button("Agregar", use_container_width=True)

    if agregar and nuevos_input.strip():
        # normalizar y deduplicar contra base + compartidos
        base_set = set(TICKERS)
        comp_set = set(compartidos)
        pedidos = [normalizar_ticker(t) for t in nuevos_input.replace("\n", ",").split(",")]
        pedidos = [t for t in pedidos if t]

        nuevos_unicos, ya_existen, invalidos = [], [], []
        for t in pedidos:
            if not ticker_valido(t):
                invalidos.append(t)
            elif t in base_set or t in comp_set or t in nuevos_unicos:
                ya_existen.append(t)
            else:
                nuevos_unicos.append(t)

        if nuevos_unicos:
            lista_final = compartidos + nuevos_unicos
            ok, msg = escribir_tickers_compartidos(lista_final)
            if ok:
                aviso = f"✅ Agregados: {', '.join(nuevos_unicos)}"
                if ya_existen: aviso += f" · Ya existían: {', '.join(ya_existen)}"
                if invalidos:  aviso += f" · ⚠️ Formato inválido (omitidos): {', '.join(invalidos)}"
                st.success(aviso)
                st.info("Guardados. Entran en el próximo barrido. Usa el botón 🔄 de abajo para escanearlos ahora.")
                leer_tickers_compartidos.clear()  # limpiar cache para releer la lista
            else:
                st.error(f"No se pudo guardar: {msg}")
        else:
            msg_w = ""
            if ya_existen: msg_w += f"Ya estaban: {', '.join(ya_existen)}. "
            if invalidos:  msg_w += f"⚠️ Formato inválido: {', '.join(invalidos)} (usa el símbolo bursátil, ej: AAPL, no el nombre)."
            st.warning(msg_w or "Nada que agregar.")

    if compartidos:
        st.markdown(f'<div style="font-size:10px;color:#4a5568;margin-top:8px;">Compartidos actuales: {", ".join(compartidos)}</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
    if st.button("🔄 Re-escanear ahora (incluye tickers nuevos)", use_container_width=True):
        st.cache_data.clear()           # limpiar todos los caches (barrido incluido)
        st.rerun()

# ── Fusionar base + compartidos, SIN duplicados (orden estable) ──
_vistos = set()
WATCHLIST = []
for t in list(TICKERS) + compartidos:
    if t not in _vistos:
        WATCHLIST.append(t)
        _vistos.add(t)

# ======================================================================
# HISTORIAL 15 DIAS - fotos diarias de TOP PICKS (GitHub Actions)
# ======================================================================
def leer_historial():
    """Lee las fotos diarias guardadas por el snapshot automatico."""
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = _json.loads(r.read().decode())
        if "historial.json" in data["files"]:
            return _json.loads(data["files"]["historial.json"]["content"])
    except Exception:
        pass
    return []

_hist = leer_historial()
# ======================================================================
# ESCANEO AUTOMATICO - barrido COMPLETO cacheado (rerun instantaneo)
# ======================================================================
@st.cache_data(ttl=300, show_spinner=False)
def descargar_batch(tickers_tuple):
    return yf.download(
        list(tickers_tuple), period="2y", group_by="ticker",
        progress=False, auto_adjust=True, threads=True,
    )


def fetch_fund(item):
    sym = item["sym_original"]
    skip = any(x in sym for x in ['-USD','-F','=X','=F','.DE','.SW','.HK'])
    # defaults
    item["target"]=item["consenso"]=item["pe_ttm"]=item["pe_fwd"]="—"
    item["upside"]="—"
    item["fv"]="—"
    item["fv_up"]="—"
    item["valor_pts"]=0
    if skip:
        return item
    fund = fetch_fundamentales(sym)
    if not fund:
        return item

    tm = fund.get("target_mean")
    item["target"] = f"${tm:.0f}" if tm else "—"
    up_txt, target_up_raw, bajo_t = calc_upside(item["precio"], tm)
    item["upside"] = up_txt

    item["consenso"] = consenso(fund.get("rec_mean"), fund.get("n_analysts"))

    pe = fund.get("pe_ttm")
    item["pe_ttm"] = f"{pe:.1f}" if pe and pe > 0 else "—"
    pef = fund.get("pe_fwd")
    item["pe_fwd"] = f"{pef:.1f}" if pef and pef > 0 else "—"

    # Fair Value: promedio Graham + Fwd P/E + Crecimiento (valor aproximado)
    pe_hist_raw = fund.get("pe_ttm")
    fv_txt, fv_up_txt, fv_up_raw = calc_fair_value(fund, pe_hist_raw, item["precio"])
    item["fv"] = fv_txt
    item["fv_up"] = fv_up_txt

    # ── VALOR: señal de LARGO PLAZO → solo distintivo visual, NO suma al score (CAMBIO 3) ──
    # El 💎 sigue siendo útil para la decisión de largo plazo, pero NO infla el ranking de swing.
    fv_ok     = (fv_up_raw is not None and fv_up_raw >= 15)
    target_ok = (target_up_raw is not None and target_up_raw >= 15)
    if fv_ok and target_ok:
        item["valor_pts"] = 2                  # 💎💎 (barato por FV y por Target)
    elif fv_ok:
        item["valor_pts"] = 1                  # 💎
    else:
        item["valor_pts"] = 0

    return item

@st.cache_data(ttl=300, show_spinner=False)
def precios_actuales(watchlist_tuple):
    """Último precio de cierre de CADA ticker de la watchlist (pase o no el filtro).
    Sirve para el 'Precio hoy' del historial. Reutiliza el batch cacheado."""
    df_batch = descargar_batch(watchlist_tuple)
    precios = {}
    for sym in watchlist_tuple:
        try:
            if isinstance(df_batch.columns, pd.MultiIndex):
                if sym in df_batch.columns.get_level_values(0):
                    cl = df_batch[sym]["Close"].dropna()
                    if len(cl) > 0:
                        precios[sym] = float(cl.iloc[-1])
            else:
                cl = df_batch["Close"].dropna()
                if len(cl) > 0:
                    precios[sym] = float(cl.iloc[-1])
        except Exception:
            pass
    return precios

@st.cache_data(ttl=300, show_spinner=False)
def barrido_completo(watchlist_tuple):
    """Barrido completo cacheado: descarga + indicadores + fundamentales + filtro de régimen.
    Mientras la watchlist no cambie, un rerun reutiliza este resultado (instantaneo)."""
    df_batch = descargar_batch(watchlist_tuple)

    # Fase indicadores
    resultados = []
    for sym in watchlist_tuple:
        try:
            if isinstance(df_batch.columns, pd.MultiIndex):
                df_sym = df_batch[sym].copy() if sym in df_batch.columns.get_level_values(0) else None
            else:
                df_sym = df_batch.copy()
            datos = analizar_ticker(sym, df_sym)
        except Exception:
            datos = None
        if datos is not None:
            datos["sym_original"] = sym
            resultados.append(datos)

    # Fase fundamentales en paralelo
    with ThreadPoolExecutor(max_workers=4) as executor:
        todos = list(executor.map(fetch_fund, resultados))

    for x in todos:
        if "valor_pts" not in x:
            x["valor_pts"] = 0

    # ── CAMBIO 1: filtro de régimen — SPY bajo EMA50 → castigar cuchillos ──
    # Se aplica DENTRO del cache para que no se mute el objeto en cada rerun.
    if not regimen_alcista():
        for x in todos:
            if not x.get("p_di") and x["precio"] < x.get("ma200", x["precio"]):
                x["score"] = max(0, x["score"] - 2)

    return todos

# Ejecutar (o reutilizar cache). Spinner solo la primera vez.
with st.spinner(f"Escaneando {len(WATCHLIST)} tickers..."):
    todos = barrido_completo(tuple(WATCHLIST))

# Precio REAL de hoy de TODA la watchlist (no solo candidatos) para el historial
_precios_hoy = precios_actuales(tuple(WATCHLIST))

def _precio_num_h(s):
    try: return float(str(s).replace("$","").replace(",","").strip())
    except: return None

_label = f"\U0001F4F8 Historial TOP PICKS - ultimos {len(_hist)} dias (cierre NY)" if _hist else "\U0001F4F8 Historial TOP PICKS - se llena solo tras el cierre de NY"
with st.expander(_label, expanded=False):
    st.markdown('<div style="font-size:11px;color:#4a5568;margin-bottom:8px;">Foto automatica de las TOP (score >= 4) al cierre de NY. Memoria de 15 dias.</div>', unsafe_allow_html=True)
    if not _hist:
        st.markdown('<div style="color:#718096;font-size:12px;padding:8px 0;">Aun no hay fotos guardadas. La primera aparecera tras la proxima ejecucion automatica (tras el cierre de NY, lun-vie).</div>', unsafe_allow_html=True)
    else:
        for foto in reversed(_hist):
            fecha = foto.get("fecha","?")
            tops = foto.get("tops",[])
            if not tops:
                st.markdown(f'<div style="color:#718096;font-size:12px;margin:6px 0;"><b>{fecha}</b> - sin TOP PICKS</div>', unsafe_allow_html=True)
                continue
            filas = ""
            for t in tops:
                sym = t["sym"]
                precio_top = t.get("precio","-")          # precio el día que fue TOP
                precio_hoy = _precios_hoy.get(sym)         # precio real de hoy (del barrido)
                # construir celda "Precio hoy" con color según subió/bajó vs el día TOP
                if precio_hoy is None:
                    celda_hoy = '<td style="color:#4a5568">—</td>'
                else:
                    p0 = _precio_num_h(precio_top)
                    ph = precio_hoy
                    if p0 and ph and p0 > 0:
                        chg = (ph - p0) / p0 * 100
                        col = "#00e5a0" if chg >= 0 else "#ff4d6d"
                        sig = "+" if chg >= 0 else ""
                        celda_hoy = '<td style="font-weight:700;color:' + col + '">$' + f"{ph:.2f}" + ' <span style="font-size:9px;font-weight:400">(' + sig + f"{chg:.1f}" + '%)</span></td>'
                    else:
                        celda_hoy = '<td style="font-weight:700">$' + f"{ph:.2f}" + '</td>'
                filas += '<tr><td style="text-align:left"><a class="tk" href="' + finviz_url(sym) + '" target="_blank">' + sym + '</a></td><td style="text-align:center;color:#00e5a0;font-weight:700">' + str(t["score"]) + '</td><td style="font-size:10px">' + t.get("gatillos","") + '</td><td>' + precio_top + '</td>' + celda_hoy + '<td>' + t.get("fv","-") + '</td><td>' + t.get("upside","-") + '</td><td>' + t.get("rsi","-") + '</td><td style="font-size:10px">' + t.get("consenso","-") + '</td></tr>'
            titulo = '<div style="font-family:Syne,sans-serif;font-weight:700;color:#00d4ff;font-size:13px;margin-bottom:4px;">' + fecha + ' - ' + str(len(tops)) + ' picks</div>'
            tabla = '<div class="tw"><table><thead><tr><th style="text-align:left">Ticker</th><th style="text-align:center">Sc</th><th>Gatillos</th><th>Precio</th><th style="color:#00d4ff">Precio hoy</th><th>FV</th><th>Upside</th><th>RSI</th><th>Consenso</th></tr></thead><tbody>' + filas + '</tbody></table></div>'
            st.markdown('<div style="margin:10px 0;">' + titulo + tabla + '</div>', unsafe_allow_html=True)


# ======================================================================
# CALCULADORA DE GESTION (candidato del barrido o manual)
# ======================================================================
with st.expander("🧮 Calculadora de gestion (SL / TP / tamano de posicion)", expanded=False):
    # Explicacion de las bandas de volatilidad para todos (amigos incluidos)
    st.markdown("""<div style='font-size:11px;color:#a0aec0;line-height:1.6;background:#0d1424;border:1px solid #1e3a5f;border-radius:8px;padding:10px 12px;margin-bottom:10px;'>
<b style='color:#00d4ff'>¿Que es la banda de volatilidad?</b> Mide cuanto se mueve normalmente la accion. Define cuanto margen darle al Stop Loss: una accion mas movida necesita un stop mas lejano para no salir por ruido.<br>
🟦 <b>B1 tranquila</b> (poca volatilidad, tipo blue chip): SL <b>1.3× ATR</b> · TP1 2.0× · TP2 3.5×<br>
🟨 <b>B2 hibrida</b> (volatilidad media): SL <b>1.5× ATR</b> · TP1 2.2× · TP2 4.0×<br>
🟥 <b>B3 volatil</b> (mucho movimiento / especulativa): SL <b>2.0× ATR</b> · TP1 2.8× · TP2 5.0×<br>
<span style='color:#718096'>El ATR es el rango medio que recorre la accion en un dia. SL/TP se calculan como multiplos del ATR segun la banda.</span>
</div>""", unsafe_allow_html=True)

    modo = st.radio("Modo", ["Desde candidato del barrido", "Manual (cualquier accion)"], horizontal=True, label_visibility="collapsed")

    _mapa = {x["sym_original"]: x for x in todos}
    _syms = sorted(_mapa.keys())

    # Valores que se definiran segun el modo
    sym_label = ""; precio_actual = 0.0; atr = 0.0; banda = 2

    if modo == "Desde candidato del barrido":
        if not _syms:
            st.info("Sin candidatos en el barrido de hoy. Usa el modo Manual.")
        else:
            cc1, cc2 = st.columns([3,3])
            with cc1:
                sym_sel = st.selectbox("Ticker (candidato)", _syms)
            x = _mapa[sym_sel]
            sym_label = sym_sel
            precio_actual = x["precio"]
            atr = x.get("atr_abs", 0) or 0
            banda = x.get("banda", 2)
            with cc2:
                st.markdown("<div style='font-size:11px;color:#718096;padding-top:30px;'>Autocompletado: " + x.get("banda_txt","?") + " · ATR $" + f"{atr:.2f}" + " · actual $" + f"{precio_actual:.2f}" + "</div>", unsafe_allow_html=True)
    else:
        # Modo manual: el usuario ingresa todo
        m1, m2, m3 = st.columns([2,2,2])
        with m1:
            sym_label = st.text_input("Ticker", value="", placeholder="ej: AAPL")
        with m2:
            precio_actual = st.number_input("Precio actual ($)", min_value=0.0, value=100.0, step=0.01, format="%.2f")
        with m3:
            atr = st.number_input("ATR ($) — de Moomoo/Finviz", min_value=0.0, value=2.0, step=0.01, format="%.2f")
        banda_label = st.radio("Banda de volatilidad (elige segun cuanto se mueve la accion)",
                               ["🟦 B1 tranquila", "🟨 B2 hibrida", "🟥 B3 volatil"],
                               index=1, horizontal=True)
        banda = {"🟦 B1 tranquila":1, "🟨 B2 hibrida":2, "🟥 B3 volatil":3}[banda_label]

    # Entrada y monto (comun a ambos modos)
    e1, e2, e3 = st.columns([2,2,2])
    with e1:
        usar_actual = st.checkbox("Usar precio actual como entrada", value=True)
    with e2:
        if usar_actual:
            entrada = precio_actual
            st.markdown("<div style='font-size:12px;color:#a0aec0;padding-top:8px;'>Entrada: <b>$" + f"{entrada:.2f}" + "</b></div>", unsafe_allow_html=True)
        else:
            entrada = st.number_input("Precio de entrada ($)", min_value=0.0, value=float(round(precio_actual,2)) if precio_actual>0 else 0.0, step=0.01, format="%.2f")
    with e3:
        monto = st.number_input("Monto a invertir (USD)", min_value=0.0, value=100.0, step=50.0, format="%.0f")

    sl_mult  = {1: 1.3, 2: 1.5, 3: 2.0}[banda]
    tp1_mult = {1: 2.0, 2: 2.2, 3: 2.8}[banda]
    tp2_mult = {1: 3.5, 2: 4.0, 3: 5.0}[banda]

    if entrada > 0 and atr > 0:
        sl  = entrada - atr * sl_mult
        tp1 = entrada + atr * tp1_mult
        tp2 = entrada + atr * tp2_mult
        riesgo_usd = (entrada - sl)
        rr1 = (tp1 - entrada) / riesgo_usd if riesgo_usd > 0 else 0
        rr2 = (tp2 - entrada) / riesgo_usd if riesgo_usd > 0 else 0
        acciones = (monto / entrada) if entrada > 0 else 0   # fracciones (Moomoo lo permite)
        riesgo_total = acciones * riesgo_usd
        riesgo_pct = (riesgo_total / monto * 100) if monto > 0 else 0
        b_txt = {1:"🟦 B1 tranquila", 2:"🟨 B2 hibrida", 3:"🟥 B3 volatil"}[banda]
        titulo = (sym_label or "Accion") + "  ·  " + b_txt
        st.markdown("<div style='font-family:Syne,sans-serif;font-weight:700;color:#00d4ff;font-size:14px;margin:6px 0;'>" + titulo + "</div>", unsafe_allow_html=True)
        # resultado en $ de cada nivel: VALOR FINAL (monto + neto) y neto entre paréntesis
        res_sl  = acciones * (sl - entrada)    # neto negativo (pérdida)
        res_tp1 = acciones * (tp1 - entrada)   # neto ganancia
        res_tp2 = acciones * (tp2 - entrada)   # neto ganancia
        def _fmt_res(neto):
            final = monto + neto
            signo = "+" if neto >= 0 else "-"
            return "$" + f"{final:.2f}" + " <span style='font-size:9px;color:#718096'>(" + signo + "$" + f"{abs(neto):.2f}" + ")</span>"
        filas = [
            ("Stop Loss", "$" + f"{sl:.2f}", "-" + f"{(entrada-sl)/entrada*100:.1f}" + "%", _fmt_res(res_sl), f"{sl_mult}" + "x ATR"),
            ("Take Profit 1", "$" + f"{tp1:.2f}", "+" + f"{(tp1-entrada)/entrada*100:.1f}" + "%", _fmt_res(res_tp1), f"{tp1_mult}" + "x ATR · R:R " + f"{rr1:.1f}"),
            ("Take Profit 2", "$" + f"{tp2:.2f}", "+" + f"{(tp2-entrada)/entrada*100:.1f}" + "%", _fmt_res(res_tp2), f"{tp2_mult}" + "x ATR · R:R " + f"{rr2:.1f}"),
        ]
        html = '<div class="tw"><table><thead><tr><th style="text-align:left">Nivel</th><th>Precio</th><th>%</th><th>Resultado</th><th>Base</th></tr></thead><tbody>'
        for n, p, pct, res, base in filas:
            col = "#00e5a0" if "Profit" in n else "#ff4d6d"
            html += '<tr><td style="text-align:left;color:' + col + ';font-weight:600">' + n + '</td><td>' + p + '</td><td style="color:' + col + '">' + pct + '</td><td style="color:' + col + ';font-weight:600">' + res + '</td><td style="font-size:10px;color:#718096">' + base + '</td></tr>'
        html += "</tbody></table></div>"
        st.markdown(html, unsafe_allow_html=True)
        resumen = ("💰 <b>" + f"{acciones:.2f}" + " acciones</b> con $" + f"{monto:.0f}" + " a $" + f"{entrada:.2f}"
                   + " · Riesgo si toca SL: <b style='color:#ff4d6d'>$" + f"{abs(riesgo_total):.2f}" + "</b> (" + f"{riesgo_pct:.1f}" + "%)")
        st.markdown("<div style='font-size:12px;color:#a0aec0;margin-top:8px;line-height:1.7;'>" + resumen + "</div>", unsafe_allow_html=True)

        # ── GESTION POR ETAPAS: 50% en TP1 + breakeven + 50% en TP2 ──
        mitad = acciones / 2
        gan_tp1_mitad = mitad * (tp1 - entrada)      # ganancia al cerrar 50% en TP1
        gan_tp2_mitad = mitad * (tp2 - entrada)      # ganancia del 50% restante si llega a TP2
        # Escenario A: llega a TP1, cierra 50%, sube stop a BE, y la otra mitad cae a BE
        esc_be = gan_tp1_mitad + 0                   # la 2da mitad sale a $0 (breakeven)
        # Escenario B: llega a TP1 (cierra 50%) y luego a TP2 (cierra resto)
        esc_full = gan_tp1_mitad + gan_tp2_mitad

        etapas_html = ("<div style='background:#0d1424;border:1px solid #1e3a5f;border-radius:8px;padding:10px 12px;margin-top:10px;font-size:12px;color:#a0aec0;line-height:1.7;'>"
            + "<b style='color:#00d4ff'>📊 Plan de salida por etapas</b><br>"
            + "<b>1.</b> En <b style='color:#00e5a0'>TP1 ($" + f"{tp1:.2f}" + ")</b>: cierras <b>50%</b> → aseguras <b style='color:#00e5a0'>+$" + f"{gan_tp1_mitad:.2f}" + "</b> y subes el stop a <b>breakeven ($" + f"{entrada:.2f}" + ")</b><br>"
            + "<b>2.</b> El <b>50% restante</b> corre con riesgo CERO (si cae, sale a tu precio de entrada)<br>"
            + "<b>3.</b> En <b style='color:#00e5a0'>TP2 ($" + f"{tp2:.2f}" + ")</b>: cierras el resto → +$" + f"{gan_tp2_mitad:.2f}" + " extra<br>"
            + "<div style='margin-top:6px;padding-top:6px;border-top:1px solid #1e3a5f;'>"
            + "🛡️ Si solo llega a TP1 y vuelve a BE: ganas <b style='color:#00e5a0'>+$" + f"{esc_be:.2f}" + "</b> con la otra mitad a riesgo cero<br>"
            + "🚀 Si llega hasta TP2: ganas <b style='color:#00e5a0'>+$" + f"{esc_full:.2f}" + "</b> en total (valor final $" + f"{monto + esc_full:.2f}" + ")"
            + "</div></div>")
        st.markdown(etapas_html, unsafe_allow_html=True)

        st.markdown("<div style='font-size:10px;color:#4a5568;margin-top:6px;'>SL/TP por ATR ajustados a la banda. Plan de salida 50%/50% con breakeven tras TP1. Referencial, no es recomendacion. Gestiona en Moomoo.</div>", unsafe_allow_html=True)
    else:
        st.info("Completa precio de entrada y ATR (mayores a 0) para calcular.")

# Resumen
n_rsi   = sum(1 for x in todos if x["p_rsi"])
n_giro  = sum(1 for x in todos if x["p_giro"])
n_toque = sum(1 for x in todos if x["p_toque"])
n_di    = sum(1 for x in todos if x.get("p_di"))
n_valor = sum(1 for x in todos if x.get("valor_pts",0) > 0)
# Robustez: cuantos candidatos quedaron sin fundamentales (FV en "-")
n_sin_fund = sum(1 for x in todos if x.get("fv","-") in ("-", "—"))
pct_sin = (n_sin_fund / len(todos) * 100) if todos else 0

# Sello de frescura del dato (hora de NY al momento del escaneo)
from datetime import datetime as _dt, timezone as _tz, timedelta as _td
_ahora_ny = _dt.now(_tz(_td(hours=-5)))
_sello = _ahora_ny.strftime("%Y-%m-%d %H:%M")

_reg_txt = "🟢 régimen alcista" if _alcista_ui else "🔴 régimen bajista (cuchillos −2)"
st.markdown(f'<div style="text-align:center;color:var(--muted);font-size:12px;padding:8px 0 4px;letter-spacing:.05em;">✅ {len(WATCHLIST)} tickers · {len(todos)} candidatos · 🔴 {n_rsi} RSI&lt;35 · 🟣 {n_giro} giro · 🟡 {n_toque} soporte · 🟢 {n_di} DI+ · 💎 {n_valor} valor · {_reg_txt}</div>', unsafe_allow_html=True)

# Linea de frescura + robustez de datos
_aviso_fund = ""
if pct_sin >= 30:
    _aviso_fund = f' · <span style="color:#ffd166">⚠ {n_sin_fund} sin fundamentales ({pct_sin:.0f}%) — FV poco fiable hoy</span>'
elif n_sin_fund > 0:
    _aviso_fund = f' · {n_sin_fund} sin fundamentales'
st.markdown(f'<div style="text-align:center;color:#4a5568;font-size:10px;padding:0 0 14px;letter-spacing:.04em;">🕑 datos al cierre/escaneo {_sello} hora NY{_aviso_fund}</div>', unsafe_allow_html=True)

# ======================================================================
# HELPER: construir filas con todas las columnas
# ======================================================================
def construir_gatillos(x):
    gs = []
    if x["p_rsi"]:
        # RSI sana (sobre MA200) vs en caída (bajo MA200)
        gs.append("🔴RSI" if x.get("rsi_sana") else "🔻RSI")
    if x["p_giro"]:  gs.append("🟣GIRO")
    if x["p_toque"]:
        if x.get("toca_bb"): gs.append("🔵BB")
        else:                gs.append("🟡EMA")
    if x.get("p_di"): gs.append("🟢DI+")
    vp = x.get("valor_pts",0)
    if vp == 2:   gs.append("💎💎VALOR")
    elif vp == 1: gs.append("💎VALOR")
    return " ".join(gs)

def _color_estilo(col, val):
    """Devuelve estilo inline segun la columna y valor (replica cr/cj/cs/csc)."""
    s = str(val)
    if col == "RSI":
        try:
            r=float(s)
            if r<33: return "color:#ff4d6d;font-weight:600"
            if r>65: return "color:#00e5a0;font-weight:600"
        except: pass
        return "color:#4a5568"
    if col == "J(KDJ)":
        try:
            r=float(s)
            if r<20: return "color:#ff4d6d;font-weight:600"
            if r>80: return "color:#ffd166;font-weight:600"
        except: pass
        return "color:#4a5568"
    if col in ("Upside","vs FV","Consenso"):
        if "🟢" in s: return "color:#00e5a0;font-weight:600"
        if "🔴" in s: return "color:#ff4d6d;font-weight:600"
        if "🟡" in s: return "color:#ffd166;font-weight:600"
        return "color:#4a5568"
    if col == "Score":
        try:
            n=int(float(s))
            if n>=5: return "color:#00e5a0;font-weight:700;text-align:center"
            if n==4: return "color:#00d4ff;font-weight:700;text-align:center"
            if n==3: return "color:#00d4ff;font-weight:600;text-align:center"
            if n==2: return "color:#b48cff;font-weight:600;text-align:center"
        except: pass
        return "color:#4a5568;text-align:center"
    if col == "ATR":
        return "color:#a0aec0"   # informativo, en dólares (para SL/TP)
    return ""

import re as _re2
_TABLA_N = [0]  # contador para id unico por tabla

def _valor_sort(col, raw, idx):
    """Extrae valor numerico para ordenar. Devuelve float o texto."""
    s = str(raw)
    if col == "#":
        return idx
    if col == "Ticker":
        # ordenar alfabetico: usar el simbolo
        m = _re2.search(r'>([^<]+)</a>', s)
        return m.group(1) if m else s
    if col == "ATR":
        try: return float(s.replace("$",""))
        except: return -1
    if col in ("Gatillos","Consenso"):
        # Consenso: ordenar por nivel (Strong Buy=5 ... Sell=1)
        if "Strong Buy" in s: return 5
        if "Buy" in s: return 4
        if "Hold" in s: return 3
        if "Sell" in s and "Strong" in s: return 1
        if "Sell" in s: return 2
        return 0
    # numerico: extraer primer numero (con signo) de la celda
    m = _re2.search(r'-?\d+\.?\d*', s.replace(",",""))
    if m:
        return float(m.group())
    return -999999  # los "—" van al fondo

def tabla_html(lista, con_score=True):
    """Tabla HTML ordenable por columna (JS en navegador) + ticker-link + fila resaltada."""
    _TABLA_N[0] += 1
    tid = f"tw{_TABLA_N[0]}"

    if con_score:
        cols = ["#","Ticker","Score","Gatillos","Precio","Fair Value","vs FV",
                "Target 12M","Upside","RSI","J(KDJ)","ADX","ATR","P/E","P/E fwd","Consenso"]
    else:
        cols = ["#","Ticker","Precio","Fair Value","vs FV",
                "Target 12M","Upside","RSI","J(KDJ)","ADX","ATR","P/E","P/E fwd","Consenso"]

    head = "".join(f'<th>{c}<span class="ar"></span></th>' for c in cols)

    filas_html = []
    for i, x in enumerate(lista, 1):
        celdas = {
            "#": str(i),
            "Ticker": f'<a class="tk" href="{finviz_url(x["sym"])}" target="_blank">{x["sym"]}</a>',
            "Score": str(x.get("score","")),
            "Gatillos": construir_gatillos(x),
            "Precio": x["precio_str"],
            "Fair Value": x.get("fv","—"), "vs FV": x.get("fv_up","—"),
            "Target 12M": x.get("target","—"), "Upside": x.get("upside","—"),
            "RSI": x["rsi_str"], "J(KDJ)": x["j_str"], "ADX": x["adx_str"],
            "ATR": x.get("atr_str","—"),
            "P/E": x.get("pe_ttm","—"), "P/E fwd": x.get("pe_fwd","—"),
            "Consenso": x.get("consenso","—"),
        }
        tds = []
        for c in cols:
            sval = _valor_sort(c, celdas[c], i)
            if c in ("#","Ticker"):
                tds.append(f'<td data-s="{sval}">{celdas[c]}</td>')
            else:
                estilo = _color_estilo(c, celdas[c])
                tds.append(f'<td data-s="{sval}" style="{estilo}">{celdas[c]}</td>')
        filas_html.append("<tr>" + "".join(tds) + "</tr>")

    cuerpo = "".join(filas_html)
    return f'<div class="tw"><table id="{tid}"><thead><tr>' + head + '</tr></thead><tbody>' + cuerpo + '</tbody></table></div>'

# ======================================================================
# TOP PICKS — TABLAS SEPARADAS POR PUNTAJE (5 · 4 · 3 · 2 · 1)
# ======================================================================
# ======================================================================
# QUE CAMBIO VS AYER (usa el historial guardado)
# ======================================================================
def _cambios_vs_ayer():
    """Compara el escaneo de hoy con la ultima foto del historial."""
    # Buscar la foto mas reciente que NO sea de hoy
    foto_prev = None
    for foto in reversed(_hist):
        if foto.get("fecha") != _ahora_ny.strftime("%Y-%m-%d"):
            foto_prev = foto
            break
    if not foto_prev:
        return None, None, None
    # Mapas de score por ticker
    prev = {t["sym"]: t.get("score", 0) for t in foto_prev.get("tops", [])}
    hoy_tops = {x["sym"]: x["score"] for x in todos if x["score"] >= 4}
    nuevos = [s for s in hoy_tops if s not in prev]
    subieron = [s for s in hoy_tops if s in prev and hoy_tops[s] > prev[s]]
    return foto_prev.get("fecha"), nuevos, subieron

_fecha_prev, _nuevos, _subieron = _cambios_vs_ayer()
if _fecha_prev and (_nuevos or _subieron):
    partes = []
    if _nuevos:
        partes.append('<span style="color:#00e5a0;font-weight:600">🆕 Nuevos en TOP:</span> ' + ", ".join(_nuevos))
    if _subieron:
        partes.append('<span style="color:#00d4ff;font-weight:600">⬆ Subieron score:</span> ' + ", ".join(_subieron))
    st.markdown(f'<div style="background:#0d1424;border:1px solid #1e3a5f;border-radius:10px;padding:10px 14px;margin:8px 0 14px;font-size:12px;color:#a0aec0;">Cambios vs {_fecha_prev}: ' + " &nbsp;·&nbsp; ".join(partes) + '</div>', unsafe_allow_html=True)

st.markdown('<div class="sec sec-os">⭐ TOP PICKS POR PUNTAJE</div>', unsafe_allow_html=True)
st.markdown("""<div class="glosario">
<b>Puntaje técnico con pesos (máx 5)</b> &nbsp;·&nbsp;
<b>🟣GIRO (vale 2)</b> giro KDJ + MACD + cierre&gt;mín ayer + volumen — la señal más fuerte &nbsp;·&nbsp;
<b>🔴RSI</b> sobreventa sana (sobre MA200) · <b>🔻RSI</b> sobreventa en caída (bajo MA200, cuchillo) &nbsp;·&nbsp;
<b>🟡EMA / 🔵BB</b> toque EMA 50/200/325 o Bollinger + cierre&gt;mín + volumen &nbsp;·&nbsp;
<b>🟢DI+</b> DI+&gt;DI- (presión alcista, separa giro real de trampa) &nbsp;·&nbsp;
<b>💎VALOR</b> FV ≥+15% (solo visual, NO suma al score) · <b>💎💎</b> FV Y Target ambos ≥+15% &nbsp;·&nbsp;
<b>Penalizaciones</b>: reversión sin DI+/GIRO −1 · B3 bajo MA200 −1 · B3 sin confirmar −1 · régimen SPY bajista: cuchillo −2 &nbsp;·&nbsp;
<b>ATR</b> rango medio diario en $ (14d, Wilder) — úsalo para fijar Stop Loss y Take Profit &nbsp;·&nbsp;
<b>Fair Value</b> aprox: Graham + Fwd P/E + crecimiento (referencial) · <b>Upside</b> % vs Target
</div>""", unsafe_allow_html=True)

def tabla_puntaje(titulo, lista, color):
    if not lista:
        return
    st.markdown(f'<div style="font-family:Syne,sans-serif;font-weight:700;font-size:12px;color:{color};margin:14px 0 4px;letter-spacing:.05em;">{titulo} ({len(lista)})</div>', unsafe_allow_html=True)
    ordenada = sorted(lista, key=lambda x:(-x["score"], x["rsi"]))
    st.markdown(tabla_html(ordenada, con_score=True), unsafe_allow_html=True)

g5  = [x for x in todos if x["score"] >= 5]
g4  = [x for x in todos if x["score"] == 4]
g3  = [x for x in todos if x["score"] == 3]
g2  = [x for x in todos if x["score"] == 2]
g1  = [x for x in todos if x["score"] == 1]

tabla_puntaje("🏆 PUNTAJE 5 — MÁXIMA CONVICCIÓN", g5, "#00e5a0")
tabla_puntaje("🥇 PUNTAJE 4 — MUY FUERTE", g4, "#00d4ff")
tabla_puntaje("🥈 PUNTAJE 3 — FUERTE", g3, "#00d4ff")
tabla_puntaje("🥉 PUNTAJE 2 — MODERADO", g2, "#b48cff")
tabla_puntaje("• PUNTAJE 1 — VIGILANCIA", g1, "#718096")

# ======================================================================
# LISTAS POR ITEM INDIVIDUAL
# ======================================================================
def render_seccion(titulo, css, key, glosario):
    items = sorted([x for x in todos if x.get(key)], key=lambda x: x["rsi"])
    st.markdown(f'<div class="sec {css}">{titulo}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="glosario">{glosario}</div>', unsafe_allow_html=True)
    if not items:
        st.info("Sin candidatos en esta categoría hoy.")
        return
    st.markdown(tabla_html(items, con_score=False), unsafe_allow_html=True)

GLOS_FUND = "<b>Fair Value</b>: aprox por múltiplos (Graham + Fwd P/E + crecimiento), referencial &nbsp;·&nbsp; <b>vs FV</b>: % vs Fair Value &nbsp;·&nbsp; <b>Target 12M</b>: objetivo analistas &nbsp;·&nbsp; <b>Upside</b>: % vs Target"

render_seccion(
    "🔴 RSI EN SOBREVENTA — RSI < 35", "sec-os", "p_rsi",
    "<b>Criterio</b>: RSI &lt;35 — lista de vigilancia de sobreventa &nbsp;·&nbsp; " + GLOS_FUND
)
render_seccion(
    "🟣 GIRO KDJ + CRUCE MACD", "sec-cr", "p_giro",
    "<b>Criterio</b>: KDJ girando/cruzando + MACD gira/cruza + cierre sobre mínimo de ayer + volumen ≥85% &nbsp;·&nbsp; " + GLOS_FUND
)
render_seccion(
    "🟡 TOCANDO SOPORTE — EMA 50/200/325 o BOLLINGER", "sec-mas", "p_toque",
    "<b>Criterio</b>: toca EMA 50/200/325 o banda inferior Bollinger desde arriba + cierre sobre mínimo de ayer + volumen ≥85% &nbsp;·&nbsp; " + GLOS_FUND
)
render_seccion(
    "🟢 PRESIÓN ALCISTA — DI+ > DI-", "sec-cr", "p_di",
    "<b>Criterio</b>: DI+ domina sobre DI- (componentes del ADX) — la presión compradora supera a la vendedora, separa giros reales de trampas bajistas &nbsp;·&nbsp; " + GLOS_FUND
)


# ======================================================================
# JS DE ORDENAMIENTO POR COLUMNA (corre en el navegador, sin reruns)
# ======================================================================
import streamlit.components.v1 as components
components.html("""
<script>
function ordenar(tabla, col, th){
    const tbody = tabla.querySelector('tbody');
    const filas = Array.from(tbody.querySelectorAll('tr'));
    const asc = th.getAttribute('data-asc') !== 'true';
    tabla.querySelectorAll('th').forEach(h=>{h.removeAttribute('data-asc'); const a=h.querySelector('.ar'); if(a)a.textContent='';});
    th.setAttribute('data-asc', asc);
    const ar = th.querySelector('.ar'); if(ar) ar.textContent = asc ? ' \u25B2' : ' \u25BC';
    filas.sort((ra,rb)=>{
        let a = ra.children[col].getAttribute('data-s');
        let b = rb.children[col].getAttribute('data-s');
        const na = parseFloat(a), nb = parseFloat(b);
        if(!isNaN(na) && !isNaN(nb)){ return asc ? na-nb : nb-na; }
        a=(a||'').toString(); b=(b||'').toString();
        return asc ? a.localeCompare(b) : b.localeCompare(a);
    });
    filas.forEach(f=>tbody.appendChild(f));
}
function activar(){
    const doc = window.parent.document;
    const tablas = doc.querySelectorAll('.tw table');
    tablas.forEach(tabla=>{
        if(tabla.getAttribute('data-sortable')) return;  // ya activada
        tabla.setAttribute('data-sortable','1');
        const ths = tabla.querySelectorAll('th');
        ths.forEach((th, idx)=>{
            th.style.cursor='pointer';
            th.addEventListener('click', ()=>ordenar(tabla, idx, th));
        });
    });
}
// reintentar varias veces hasta que las tablas existan en el DOM padre
let intentos = 0;
const timer = setInterval(()=>{
    activar();
    intentos++;
    if(intentos > 20) clearInterval(timer);
}, 400);
</script>
""", height=0)

st.markdown('<p class="footer">Rebote Screener · Técnico + Fundamental · Solo fines educativos · No es asesoría financiera</p>', unsafe_allow_html=True)
