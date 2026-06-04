# ======================================================================
# SCREENER DE REBOTES + FUNDAMENTAL — V FINAL
# Ejecuta automaticamente al cargar · Sin botones · Sin bandas
# 4 gatillos de rebote (EMA 50/200/325) + analisis fundamental
# Score extra si esta bajo FV y bajo Target
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
@st.cache_data(ttl=300, show_spinner=False)
def fetch_fundamentales(sym):
    """Datos fundamentales del ticker desde yfinance. Reintenta si Yahoo no responde."""
    import time
    for intento in range(3):
        try:
            tk = yf.Ticker(sym)
            info = tk.info
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
                }
        except Exception:
            pass
        time.sleep(0.4 * (intento + 1))  # pausa escalonada: 0.4s, 0.8s, 1.2s
    return None

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
    """FV promedio de 3 modelos: Graham + Forward P/E + Crecimiento.
    Devuelve (texto_fv, upside_txt, upside_raw)."""
    eps   = fund.get("eps_ttm")
    bv    = fund.get("book_value")
    feps  = fund.get("fwd_eps")
    g     = fund.get("growth")

    modelos = []

    # Modelo 1: Graham √(22.5×EPS×BV)
    if eps and bv and eps > 0 and bv > 0:
        modelos.append(math.sqrt(22.5 * eps * bv))

    # P/E histórico saneado (rango 8-40 para evitar extremos)
    pe_ok = None
    if pe_hist and pe_hist > 0:
        pe_ok = max(8, min(pe_hist, 40))

    # Modelo 2: Forward EPS × P/E histórico propio
    if feps and feps > 0 and pe_ok:
        modelos.append(feps * pe_ok)

    # Modelo 3: EPS proyectado 5A con crecimiento, descontado al 10%
    if eps and eps > 0 and pe_ok:
        gr = max(-0.05, min(g if g else 0.08, 0.25))
        eps_fut = eps * (1 + gr) ** 5
        modelos.append((eps_fut * pe_ok) / (1.10 ** 5))

    if not modelos:
        return ("—", "—", None)

    fv = sum(modelos) / len(modelos)
    up = (fv - precio_actual) / precio_actual * 100
    if up >= 15:   txt = f"🟢 +{up:.0f}%"
    elif up >= 0:  txt = f"⚪ +{up:.0f}%"
    elif up >= -15: txt = f"🟡 {up:.0f}%"
    else:          txt = f"🔴 {up:.0f}%"
    return (f"${fv:.0f}", txt, up)
    try:
        fv = math.sqrt(22.5 * eps_ttm * book_value)
        up = (fv - precio_actual) / precio_actual * 100
        if up >= 15:   txt = f"🟢 +{up:.0f}%"
        elif up >= 0:  txt = f"⚪ +{up:.0f}%"
        elif up >= -15: txt = f"🟡 {up:.0f}%"
        else:          txt = f"🔴 {up:.0f}%"
        return (f"${fv:.0f}", txt, up)
    except:
        return ("—", "—", None)

def consenso(rec_mean, n_analysts):
    """recommendationMean (1-5) a texto + emoji + n analistas."""
    if rec_mean is None or n_analysts is None or n_analysts == 0:
        return "—"
    if rec_mean <= 1.5:   tag = "🟢 Strong Buy"
    elif rec_mean <= 2.5: tag = "🟢 Buy"
    elif rec_mean <= 3.5: tag = "⚪ Hold"
    elif rec_mean <= 4.5: tag = "🔴 Sell"
    else:                 tag = "🔴 Strong Sell"
    return f"{tag} ({int(n_analysts)})"

# ======================================================================
# MARKET DATA
# ======================================================================
@st.cache_data(ttl=300, show_spinner=False)
def get_market_data():
    indices = {"S&P 500":"^GSPC","Nasdaq":"^NDX","Dow":"^DJI","Russell":"^RUT"}
    result = {}
    for name, sym in indices.items():
        try:
            h = yf.Ticker(sym).history(period="5d",interval="1d")
            if len(h)>=2:
                prev=float(h['Close'].iloc[-2]); curr=float(h['Close'].iloc[-1])
                result[name]={"price":curr,"pct":(curr-prev)/prev*100}
        except: result[name]={"price":0,"pct":0}
    vix=0
    try:
        h=yf.Ticker("^VIX").history(period="5d",interval="1d")
        if not h.empty: vix=float(h['Close'].iloc[-1])
    except: pass
    btc_pct=0; btc_price=0
    try:
        h=yf.Ticker("BTC-USD").history(period="5d",interval="1d")
        if len(h)>=2:
            btc_price=float(h['Close'].iloc[-1])
            btc_pct=(btc_price-float(h['Close'].iloc[-2]))/float(h['Close'].iloc[-2])*100
    except: pass
    return result, vix, btc_pct, btc_price

# ======================================================================
# ANALIZAR TICKER — 4 gatillos de rebote (recibe df ya descargado)
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

    # ── ADX ──
    hd=df['High']-df['High'].shift(1); ld=df['Low'].shift(1)-df['Low']
    dmp=np.where((hd>0)&(hd>ld),hd,0); dmm=np.where((ld>0)&(ld>hd),ld,0)
    t14=pd.concat([hl,hpc,lpc],axis=1).max(axis=1).rolling(14).sum().replace(0,1e-8)
    pdi=pd.Series(dmp,index=df.index).rolling(14).sum()*100/t14
    mdi=pd.Series(dmm,index=df.index).rolling(14).sum()*100/t14
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

    # ══════════════════════════════════════════════════════════
    # 5 PUNTOS INDEPENDIENTES DE SCORE
    # ══════════════════════════════════════════════════════════

    # ── PUNTO 1: RSI < 35 (sobreventa) ──
    p_rsi = rsi_v < 35

    # ── PUNTO 2: GIRO KDJ + CRUCE MACD + volumen + cierre sobre min ayer ──
    cierre_sobre_min = precio > float(df['Low'].iloc[-2])
    vol_ok = bool(df['VOL_OK'].iloc[-1])
    p_giro = (
        bool(df['CROSS_KD'].iloc[-1] or df['CROSS_KD'].iloc[-2] or df['GIRO_J'].iloc[-1]) and
        bool(df['GIRO_MACD'].iloc[-1] or df['CROSS_MACD'].iloc[-1] or df['CROSS_MACD'].iloc[-2]) and
        cierre_sobre_min and
        vol_ok
    )

    # ── PUNTO 3: TOQUE DE SOPORTE — Bollinger inf. O EMA 20/50/200/325 desde arriba ──
    ma20_v  = float(df['MA20'].iloc[-1])
    ma50_v  = float(df['MA50'].iloc[-1])
    ma200_v = float(df['MA200'].iloc[-1])
    ma325_v = float(df['MA325'].iloc[-1])
    low_v   = float(df['Low'].iloc[-1])
    bb_dn_y = float(df['BB_DN'].iloc[-2])
    low_y   = float(df['Low'].iloc[-2])
    bb_dn   = float(df['BB_DN'].iloc[-1])

    toca_ema = (
        (low_v <= ma20_v  * 1.015 and precio > ma20_v  * 0.985) or
        (low_v <= ma50_v  * 1.015 and precio > ma50_v  * 0.985) or
        (low_v <= ma200_v * 1.015 and precio > ma200_v * 0.985) or
        (low_v <= ma325_v * 1.015 and precio > ma325_v * 0.985)
    )
    toca_bb = (low_y <= bb_dn_y and precio > bb_dn)
    # Toque válido solo con volumen y cierre sobre mínimo de ayer
    p_toque = (toca_ema or toca_bb) and cierre_sobre_min and vol_ok

    # ── PUNTO 4-5: VALOR (se calcula en fetch_fund, +1 o +2) ──
    # Aqui solo registramos el score tecnico de 3 puntos.
    # El bonus de valor (1 o 2) se suma despues en fetch_fund.

    if not (p_rsi or p_giro or p_toque):
        return None

    score_tecnico = sum([p_rsi, p_giro, p_toque])

    return {
        "sym": sym,
        "precio": precio,
        "precio_str": f"${precio:.2f}",
        "rsi": rsi_v, "rsi_str": f"{rsi_v:.1f}",
        "j": j_v, "j_str": f"{j_v:.1f}",
        "adx": adx_v, "adx_str": f"{adx_v:.1f}",
        "score": score_tecnico,
        "p_rsi":   p_rsi,
        "p_giro":  p_giro,
        "p_toque": p_toque,
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
    <p>REBOTE EMA 50/200/325 · SOBREVENTA · BOLLINGER · KDJ+MACD · FUNDAMENTAL</p>
  </div>
  <div class="badge">WIP</div>
</div>
""", unsafe_allow_html=True)

# ======================================================================
# MARKET DATA
# ======================================================================
indices, vix, btc_pct, btc_price = get_market_data()
st.markdown('<div class="idx-grid">', unsafe_allow_html=True)
for name, data in indices.items():
    p=data["price"]; pct=data["pct"]
    cls="up" if pct>=0 else "down"; sig="+" if pct>=0 else ""
    st.markdown(f'<div class="idx-card"><div class="idx-label">{name}</div><div class="idx-price">{p:,.0f}</div><div class="{cls}">{sig}{pct:.2f}%</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

sp_pct=indices.get("S&P 500",{}).get("pct",0)
vcls="ok" if vix<18 else ("warn" if vix<25 else "bad")
bcls="up" if btc_pct>=0 else "down"
bsig="+" if btc_pct>=0 else ""
bp=f"${btc_price:,.0f}" if btc_price>0 else "—"
if vix<18 and sp_pct>0:   ctx_cls,ctx_txt="ok","✅ Condiciones favorables"
elif vix>25 or sp_pct<-1: ctx_cls,ctx_txt="bad","⚠️ Mercado defensivo"
else:                      ctx_cls,ctx_txt="warn","⚪ Contexto mixto"

st.markdown(f"""
<div class="ctx-grid">
  <div class="ctx-card"><div class="ctx-label">VIX</div><div class="ctx-val">{vix:.1f}</div><div class="ctx-sub {vcls}">{"✅ Tranquilo" if vix<18 else ("⚠️ Moderado" if vix<25 else "🔴 Alto")}</div></div>
  <div class="ctx-card"><div class="ctx-label">BTC</div><div class="ctx-val {bcls}">{bp}</div><div class="ctx-sub {bcls}">{bsig}{btc_pct:.2f}%</div></div>
  <div class="ctx-card"><div class="ctx-label">Contexto</div><div class="ctx-val" style="font-size:12px;margin-top:4px;">&nbsp;</div><div class="ctx-sub {ctx_cls}" style="font-size:12px;">{ctx_txt}</div></div>
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
                leer_tickers_compartidos.clear()  # limpiar cache para releer
                st.rerun()
            else:
                st.error(f"No se pudo guardar: {msg}")
        else:
            msg_w = ""
            if ya_existen: msg_w += f"Ya estaban: {', '.join(ya_existen)}. "
            if invalidos:  msg_w += f"⚠️ Formato inválido: {', '.join(invalidos)} (usa el símbolo bursátil, ej: AAPL, no el nombre)."
            st.warning(msg_w or "Nada que agregar.")

    if compartidos:
        st.markdown(f'<div style="font-size:10px;color:#4a5568;margin-top:8px;">Compartidos actuales: {", ".join(compartidos)}</div>', unsafe_allow_html=True)

# ── Fusionar base + compartidos, SIN duplicados (orden estable) ──
_vistos = set()
WATCHLIST = []
for t in list(TICKERS) + compartidos:
    if t not in _vistos:
        WATCHLIST.append(t)
        _vistos.add(t)

# ======================================================================
# ESCANEO AUTOMATICO — batch download + threading
# ======================================================================
prog = st.progress(0, text=f"Descargando {len(WATCHLIST)} tickers en batch...")

@st.cache_data(ttl=300, show_spinner=False)
def descargar_batch(tickers_tuple):
    return yf.download(
        list(tickers_tuple), period="2y", group_by="ticker",
        progress=False, auto_adjust=True, threads=True,
    )

df_batch = descargar_batch(tuple(WATCHLIST))
prog.progress(40, text="Calculando indicadores...")

# Fase 2: indicadores
resultados = []
for idx, sym in enumerate(WATCHLIST):
    if idx % 30 == 0:
        prog.progress(40 + int(idx/len(WATCHLIST)*30), text=f"Indicadores · {idx}/{len(WATCHLIST)}")
    try:
        if isinstance(df_batch.columns, pd.MultiIndex):
            df_sym = df_batch[sym].copy() if sym in df_batch.columns.get_level_values(0) else None
        else:
            df_sym = df_batch.copy()
        datos = analizar_ticker(sym, df_sym)
    except:
        datos = None
    if datos is not None:
        datos["sym_original"] = sym
        resultados.append(datos)

# Fase 3: fundamentales en paralelo
prog.progress(70, text=f"Fundamentales para {len(resultados)} candidatos...")

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

    # Fair Value promedio de 3 modelos (Graham + Fwd P/E + Crecimiento)
    pe_hist_raw = fund.get("pe_ttm")
    fv_txt, fv_up_txt, fv_up_raw = calc_fair_value(fund, pe_hist_raw, item["precio"])
    item["fv"] = fv_txt
    item["fv_up"] = fv_up_txt

    # ── PUNTO 4-5: VALOR (+1 o +2) ──
    # +1 si FV >= +15% (barata vs fair value)
    # +2 si ADEMÁS Target 12M >= +15% (doble confirmación: FV Y analistas)
    fv_ok     = (fv_up_raw is not None and fv_up_raw >= 15)
    target_ok = (target_up_raw is not None and target_up_raw >= 15)
    if fv_ok and target_ok:
        item["score"] = item["score"] + 2
        item["valor_pts"] = 2
    elif fv_ok:
        item["score"] = item["score"] + 1
        item["valor_pts"] = 1
    else:
        item["valor_pts"] = 0

    return item

with ThreadPoolExecutor(max_workers=4) as executor:
    todos = list(executor.map(fetch_fund, resultados))

# asegurar valor_pts en todos
for x in todos:
    if "valor_pts" not in x:
        x["valor_pts"] = 0

prog.progress(100, text="¡Listo!")
prog.empty()

# Resumen
n_rsi   = sum(1 for x in todos if x["p_rsi"])
n_giro  = sum(1 for x in todos if x["p_giro"])
n_toque = sum(1 for x in todos if x["p_toque"])
n_valor = sum(1 for x in todos if x.get("valor_pts",0) > 0)

st.markdown(f'<div style="text-align:center;color:var(--muted);font-size:12px;padding:8px 0 16px;letter-spacing:.05em;">✅ {len(WATCHLIST)} tickers · {len(todos)} candidatos · 🔴 {n_rsi} RSI&lt;35 · 🟣 {n_giro} giro+MACD · 🟡 {n_toque} soporte · 💎 {n_valor} valor</div>', unsafe_allow_html=True)

# ======================================================================
# HELPER: construir filas con todas las columnas
# ======================================================================
def construir_gatillos(x):
    gs = []
    if x["p_rsi"]:   gs.append("🔴RSI")
    if x["p_giro"]:  gs.append("🟣GIRO")
    if x["p_toque"]:
        if x.get("toca_bb"): gs.append("🔵BB")
        else:                gs.append("🟡EMA")
    vp = x.get("valor_pts",0)
    if vp == 2:   gs.append("💎VALOR×2")
    elif vp == 1: gs.append("💎VALOR×1")
    return " ".join(gs)

def finviz_url(sym):
    """URL de finviz para el ticker (limpia sufijos no soportados)."""
    base = sym.replace("-USD","").replace("=F","").replace("=X","")
    return f"https://finviz.com/quote.ashx?t={base}&p=d"

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
            if n>=4: return "color:#00e5a0;font-weight:700;text-align:center"
            if n==3: return "color:#00d4ff;font-weight:600;text-align:center"
            if n==2: return "color:#b48cff;font-weight:600;text-align:center"
        except: pass
        return "color:#4a5568;text-align:center"
    return ""

def tabla_html(lista, con_score=True):
    """Genera tabla HTML: ticker como link a Finviz + fila resaltada completa."""
    if con_score:
        cols = ["#","Ticker","Score","Gatillos","Precio","Fair Value","vs FV",
                "Target 12M","Upside","RSI","J(KDJ)","ADX","P/E","P/E fwd","Consenso"]
    else:
        cols = ["#","Ticker","Precio","Fair Value","vs FV",
                "Target 12M","Upside","RSI","J(KDJ)","ADX","P/E","P/E fwd","Consenso"]

    head = "".join(f"<th>{c}</th>" for c in cols)
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
            "P/E": x.get("pe_ttm","—"), "P/E fwd": x.get("pe_fwd","—"),
            "Consenso": x.get("consenso","—"),
        }
        tds = []
        for c in cols:
            if c in ("#","Ticker"):
                tds.append(f"<td>{celdas[c]}</td>")
            else:
                estilo = _color_estilo(c, celdas[c])
                tds.append(f'<td style="{estilo}">{celdas[c]}</td>')
        filas_html.append("<tr>" + "".join(tds) + "</tr>")

    cuerpo = "".join(filas_html)
    return '<div class="tw"><table><thead><tr>' + head + '</tr></thead><tbody>' + cuerpo + '</tbody></table></div>'

# ======================================================================
# TOP PICKS — TABLAS SEPARADAS POR PUNTAJE (4-5 · 3 · 2 · 1)
# ======================================================================
st.markdown('<div class="sec sec-os">⭐ TOP PICKS POR PUNTAJE</div>', unsafe_allow_html=True)
st.markdown("""<div class="glosario">
<b>5 puntos posibles</b> &nbsp;·&nbsp;
<b>🔴RSI</b> RSI&lt;35 sobreventa &nbsp;·&nbsp;
<b>🟣GIRO</b> giro KDJ + cruce MACD + cierre&gt;mín ayer + volumen &nbsp;·&nbsp;
<b>🟡EMA / 🔵BB</b> toque EMA 20/50/200/325 o Bollinger + cierre&gt;mín ayer + volumen &nbsp;·&nbsp;
<b>💎VALOR×1</b> Fair Value ≥+15% · <b>💎VALOR×2</b> FV Y Target 12M ambos ≥+15% &nbsp;·&nbsp;
<b>Fair Value</b> promedio de 3 modelos (Graham + Fwd P/E + Crecimiento) &nbsp;·&nbsp;
<b>Upside</b> % vs Target 12M analistas
</div>""", unsafe_allow_html=True)

def tabla_puntaje(titulo, lista, color):
    if not lista:
        return
    st.markdown(f'<div style="font-family:Syne,sans-serif;font-weight:700;font-size:12px;color:{color};margin:14px 0 4px;letter-spacing:.05em;">{titulo} ({len(lista)})</div>', unsafe_allow_html=True)
    ordenada = sorted(lista, key=lambda x:(-x["score"], x["rsi"]))
    st.markdown(tabla_html(ordenada, con_score=True), unsafe_allow_html=True)

g45 = [x for x in todos if x["score"] >= 4]
g3  = [x for x in todos if x["score"] == 3]
g2  = [x for x in todos if x["score"] == 2]
g1  = [x for x in todos if x["score"] == 1]

tabla_puntaje("🏆 PUNTAJE 4-5 — MÁXIMA CONVICCIÓN", g45, "#00e5a0")
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

GLOS_FUND = "<b>Fair Value</b>: promedio Graham + Fwd P/E + Crecimiento &nbsp;·&nbsp; <b>vs FV</b>: % vs Fair Value &nbsp;·&nbsp; <b>Target 12M</b>: objetivo analistas &nbsp;·&nbsp; <b>Upside</b>: % vs Target"

render_seccion(
    "🔴 RSI EN SOBREVENTA — RSI < 35", "sec-os", "p_rsi",
    "<b>Criterio</b>: RSI &lt;35 — lista de vigilancia de sobreventa &nbsp;·&nbsp; " + GLOS_FUND
)
render_seccion(
    "🟣 GIRO KDJ + CRUCE MACD", "sec-cr", "p_giro",
    "<b>Criterio</b>: KDJ girando/cruzando + MACD gira/cruza + cierre sobre mínimo de ayer + volumen ≥85% &nbsp;·&nbsp; " + GLOS_FUND
)
render_seccion(
    "🟡 TOCANDO SOPORTE — EMA 20/50/200/325 o BOLLINGER", "sec-mas", "p_toque",
    "<b>Criterio</b>: toca EMA (20/50/200/325) o banda inferior Bollinger desde arriba + cierre sobre mínimo de ayer + volumen ≥85% &nbsp;·&nbsp; " + GLOS_FUND
)

st.markdown('<p class="footer">Rebote Screener · Técnico + Fundamental · Solo fines educativos · No es asesoría financiera</p>', unsafe_allow_html=True)
