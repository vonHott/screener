# ======================================================================
# SCREENER CRH V2 — RADAR DEL CRH V5 SOBRE LA GRAN LISTA
# Ejecuta automaticamente al cargar · Sin botones · Sin repasar 290 charts
# ----------------------------------------------------------------------
# QUE CAMBIO VS LA V FINAL (la de 4 gatillos sueltos):
#   * MOTOR = PORT FIEL DEL CRH V5. Los MISMOS 9 gatillos que corres en
#     Moomoo (S_PULL, S_IMPU, S_BOLL, S_SUELO, S_MACD, S_EARLY, S_CONT,
#     S_REBOTE_MA200, S_REC) con sus gates de banda (1.5/3.0) y contexto
#     (SOPORTE_SANO, PERMITE_MOM, ES_BAJISTA_CRITICO). Esto es lo que
#     mataba los cuchillos y laterales que la V Final pescaba.
#   * SEÑAL FRESCA: solo muestra el ticker el dia que la señal DISPARA
#     (B_SIGNAL = primera vela del raw), no cada dia que sigue activa.
#     Anti-duplicados (adios FICO marcado 2 dias seguidos).
#   * BLACKOUT DE EARNINGS: separa los que reportan en <=N dias habiles.
#     Esto solo te habria ahorrado GDDY -19.6% y ambos FICO -16/-18%.
#   * RSI = OSC SIMPLE (14-sum) igual que el CRH V5, no Wilder.
#   * VALOR sigue siendo solo 💎 visual, NO suma al score de swing.
# ======================================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
from concurrent.futures import ThreadPoolExecutor
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Screener CRH V2", page_icon="🎯", layout="wide",
                   initial_sidebar_state="collapsed")

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
.sec-cr{color:var(--purple);border-bottom-color:var(--purple)}
.sec-ea{color:var(--yellow);border-bottom-color:var(--yellow)}
.glosario{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 14px;margin-bottom:10px;font-size:11px;color:var(--muted);line-height:1.9}
.glosario b{color:#718096}
.tw{overflow-x:auto;border:1px solid var(--border);border-radius:10px;margin-bottom:10px;-webkit-overflow-scrolling:touch}
.tw table{border-collapse:collapse;width:100%;font-family:'DM Mono',monospace;font-size:11px;white-space:nowrap}
.tw th{background:#0a0e18;color:#718096;font-weight:500;text-transform:uppercase;font-size:9px;letter-spacing:.06em;padding:9px 12px;text-align:right;border-bottom:1px solid var(--border2);position:sticky;top:0}
.tw th:first-child,.tw th:nth-child(2){text-align:left}
.tw td{padding:8px 12px;text-align:right;border-bottom:1px solid var(--border);color:var(--text)}
.tw td:first-child{text-align:right;color:var(--muted);font-size:10px}
.tw td:nth-child(2){text-align:left;font-weight:600}
.tw tr{transition:background .08s}
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
# TICKERS COMPARTIDOS (GitHub Gist)
# ======================================================================
import urllib.request, json as _json, re as _re
GIST_ID = "00c849548b7f82e35530eb837df20a3a"

def finviz_url(sym):
    base = sym.replace("-USD","").replace("=F","").replace("=X","")
    return f"https://finviz.com/quote.ashx?t={base}&p=d"

def _gist_token():
    try: return st.secrets["GITHUB_TOKEN"]
    except Exception: return None

@st.cache_data(ttl=60, show_spinner=False)
def leer_tickers_compartidos():
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = _json.loads(r.read().decode())
        contenido = data["files"]["tickers.txt"]["content"]
        items = [t.strip().upper() for t in contenido.replace("\n", ",").split(",")]
        return [t for t in items if t]
    except Exception:
        return []

def escribir_tickers_compartidos(lista):
    token = _gist_token()
    if not token: return False, "No hay token configurado en Secrets."
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        payload = _json.dumps({"files": {"tickers.txt": {"content": ",".join(lista)}}}).encode()
        req = urllib.request.Request(url, data=payload, method="PATCH", headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return (r.status in (200, 201)), "ok"
    except Exception as e:
        return False, str(e)

def normalizar_ticker(t):
    t = t.strip().upper().replace("$", "").replace(" ", "")
    return t.replace(".B", "-B").replace(".A", "-A")

def ticker_valido(t):
    if not t or len(t) > 12: return False
    return bool(_re.match(r'^[A-Z0-9]{1,7}([\-\.=][A-Z0-9]{1,4})?$', t))

# ======================================================================
# FUNDAMENTALES (sin cambios: Finviz principal, yfinance respaldo)
# ======================================================================
def _num(s):
    if s is None: return None
    s = str(s).strip()
    if s in ("-", "", "—"): return None
    try:
        pct = s.endswith("%")
        s2 = s.replace("%", "").replace(",", "").replace("$", "")
        mult = 1.0
        if s2 and s2[-1] in "BMK":
            mult = {"B":1e9,"M":1e6,"K":1e3}[s2[-1]]; s2 = s2[:-1]
        v = float(s2) * mult
        return v/100.0 if pct else v
    except Exception:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def fetch_finviz(sym):
    if any(x in sym for x in ['-USD','-F','=X','=F','.DE','.SW','.HK']): return None
    try:
        from finvizfinance.quote import finvizfinance
        stock = finvizfinance(sym)
        f = stock.ticker_fundament()
        if not f or not isinstance(f, dict): return None
        growth = _num(f.get("EPS next 5Y")) or _num(f.get("EPS next Y"))
        return {"target_mean":_num(f.get("Target Price")),"n_analysts":None,
                "rec_mean":_num(f.get("Recom")),"pe_ttm":_num(f.get("P/E")),
                "pe_fwd":_num(f.get("Forward P/E")),"eps_ttm":_num(f.get("EPS (ttm)")),
                "fwd_eps":None,"book_value":_num(f.get("Book/sh")),"growth":growth,"_fuente":"finviz"}
    except Exception:
        return None

@st.cache_data(ttl=300, show_spinner=False)
def fetch_yf(sym):
    import time
    for intento in range(2):
        try:
            info = yf.Ticker(sym).info
            if info and len(info) >= 10 and (info.get("targetMeanPrice") or info.get("trailingPE") or info.get("trailingEps")):
                return {"target_mean":info.get("targetMeanPrice"),"n_analysts":info.get("numberOfAnalystOpinions"),
                        "rec_mean":info.get("recommendationMean"),"pe_ttm":info.get("trailingPE"),
                        "pe_fwd":info.get("forwardPE"),"eps_ttm":info.get("trailingEps"),
                        "fwd_eps":info.get("forwardEps"),"book_value":info.get("bookValue"),
                        "growth":info.get("earningsGrowth"),"_fuente":"yfinance"}
        except Exception:
            pass
        time.sleep(0.4 * (intento + 1))
    return None

@st.cache_data(ttl=300, show_spinner=False)
def fetch_fundamentales(sym):
    fv = fetch_finviz(sym)
    if fv is None: return fetch_yf(sym)
    if fv.get("target_mean") is None or fv.get("rec_mean") is None:
        yf_data = fetch_yf(sym)
        if yf_data:
            for k in ("target_mean","rec_mean","n_analysts"):
                if fv.get(k) is None: fv[k] = yf_data.get(k)
    return fv

def calc_upside(precio_actual, target_mean):
    if not target_mean or target_mean <= 0: return ("—", None, False)
    up = (target_mean - precio_actual) / precio_actual * 100
    if up >= 15: txt = f"🟢 +{up:.0f}%"
    elif up >= 0: txt = f"⚪ +{up:.0f}%"
    elif up >= -10: txt = f"🟡 {up:.0f}%"
    else: txt = f"🔴 {up:.0f}%"
    return (txt, up, precio_actual < target_mean)

def calc_fair_value(fund, pe_hist, precio_actual):
    import math as _math
    eps=fund.get("eps_ttm"); bv=fund.get("book_value"); feps=fund.get("fwd_eps")
    g=fund.get("growth"); pe_fwd_val=fund.get("pe_fwd")
    modelos = []
    if eps and bv and eps > 0 and bv > 0:
        modelos.append(_math.sqrt(22.5 * eps * bv))
    pe_ref = pe_hist if (pe_hist and pe_hist>0) else (pe_fwd_val if (pe_fwd_val and pe_fwd_val>0) else 18.0)
    pe_ok = max(8, min(pe_ref, 40))
    if feps and feps > 0: modelos.append(feps * pe_ok)
    if eps and eps > 0:
        gr = max(-0.05, min(g if g else 0.08, 0.25))
        modelos.append((eps * (1 + gr) ** 5 * pe_ok) / (1.10 ** 5))
    if (not eps or eps <= 0) and feps and feps > 0:
        gr = max(-0.05, min(g if g else 0.08, 0.25))
        modelos.append((feps * (1 + gr) ** 4 * pe_ok) / (1.10 ** 4))
    if not modelos: return ("—", "—", None)
    fv = sum(modelos) / len(modelos)
    up = (fv - precio_actual) / precio_actual * 100
    if up >= 15: txt = f"🟢 +{up:.0f}%"
    elif up >= 0: txt = f"⚪ +{up:.0f}%"
    elif up >= -15: txt = f"🟡 {up:.0f}%"
    else: txt = f"🔴 {up:.0f}%"
    return (f"${fv:.0f}", txt, up)

def consenso(rec_mean, n_analysts):
    if rec_mean is None or rec_mean <= 0: return "—"
    if rec_mean <= 1.5: tag = "🟢 Strong Buy"
    elif rec_mean <= 2.5: tag = "🟢 Buy"
    elif rec_mean <= 3.5: tag = "⚪ Hold"
    elif rec_mean <= 4.5: tag = "🔴 Sell"
    else: tag = "🔴 Strong Sell"
    return f"{tag} ({int(n_analysts)})" if (n_analysts and n_analysts > 0) else tag

# ======================================================================
# EARNINGS BLACKOUT (fix del diagnostico: GDDY/FICO eran pre-earnings)
# Se consulta SOLO para candidatos que pasan el filtro tecnico (~10-40),
# no para los 290. Cache 12h. Cripto/forex/futuros = exentos.
# ======================================================================
@st.cache_data(ttl=43200, show_spinner=False)
def dias_a_earnings(sym):
    """Devuelve (dias_al_proximo, dias_desde_ultimo, es_exento).
    None si no se pudo determinar (se muestra pero se marca '?')."""
    if any(x in sym for x in ['-USD','-F','=X','=F']):
        return (None, None, True)
    try:
        ed = yf.Ticker(sym).get_earnings_dates(limit=8)
        if ed is None or len(ed) == 0:
            return (None, None, False)
        idx = ed.index
        idx = idx.tz_localize(None) if idx.tz is not None else idx
        hoy = pd.Timestamp.now().normalize()
        fut = idx[idx >= hoy]; pas = idx[idx < hoy]
        d_prox = int((fut.min() - hoy).days) if len(fut) else None
        d_ult = int((hoy - pas.max()).days) if len(pas) else None
        return (d_prox, d_ult, False)
    except Exception:
        return (None, None, False)

def estado_earnings(d_prox, d_ult, exento, dias_black):
    """(bloquear, texto). bloquear=True -> va a la seccion de blackout."""
    if exento:
        return (False, "—")
    if d_prox is None and d_ult is None:
        return (False, "? s/d")
    if d_prox is not None and d_prox <= dias_black:
        return (True, f"⏰ {d_prox}d")
    if d_ult is not None and d_ult <= 2:
        return (False, f"🆕 -{d_ult}d")
    if d_prox is not None:
        return (False, f"✓ {d_prox}d")
    return (False, "? s/d")

# ======================================================================
# MARKET DATA + REGIMEN (sin cambios)
# ======================================================================
@st.cache_data(ttl=300, show_spinner=False)
def get_market_data():
    import math as _m
    indices = {"S&P 500":"^GSPC","Nasdaq":"^IXIC","Dow":"^DJI","Russell":"^RUT"}
    result = {}
    def _pct(h):
        try:
            cl = h['Close'].dropna()
            if len(cl) >= 2:
                prev = float(cl.iloc[-2]); curr = float(cl.iloc[-1])
                if prev > 0 and not _m.isnan(curr) and not _m.isnan(prev):
                    return curr, (curr-prev)/prev*100
        except Exception: pass
        return None
    try:
        syms = list(indices.values())
        batch = yf.download(syms, period="5d", interval="1d", group_by="ticker", progress=False, threads=True)
        for name, sym in indices.items():
            try:
                h = batch[sym] if sym in batch.columns.get_level_values(0) else None
                r = _pct(h) if h is not None else None
                if r: result[name] = {"price": r[0], "pct": r[1]}
            except Exception: pass
    except Exception: pass
    for name, sym in indices.items():
        if name in result: continue
        try:
            r = _pct(yf.Ticker(sym).history(period="5d", interval="1d"))
            if r: result[name] = {"price": r[0], "pct": r[1]}
        except Exception: pass
    for name in indices:
        if name not in result or result[name].get("price") in (None,0) or _m.isnan(result[name].get("price",0)):
            result.setdefault(name, {"price": None, "pct": None})
    vix = None
    try:
        cl = yf.Ticker("^VIX").history(period="5d", interval="1d")['Close'].dropna()
        if len(cl) >= 1: vix = float(cl.iloc[-1])
    except Exception: pass
    btc_pct = btc_price = None
    try:
        cl = yf.Ticker("BTC-USD").history(period="5d", interval="1d")['Close'].dropna()
        if len(cl) >= 2:
            btc_price = float(cl.iloc[-1]); btc_pct = (btc_price-float(cl.iloc[-2]))/float(cl.iloc[-2])*100
    except Exception: pass
    return result, vix, btc_pct, btc_price

@st.cache_data(ttl=300, show_spinner=False)
def regimen_alcista():
    try:
        spy = yf.Ticker("SPY").history(period="1y")['Close'].dropna()
        if len(spy) < 50: return True
        ema50 = spy.ewm(span=50, adjust=False).mean()
        return float(spy.iloc[-1]) > float(ema50.iloc[-1])
    except Exception:
        return True

# ======================================================================
# ANALIZAR TICKER — PORT FIEL DEL CRH V5 (los 9 gatillos + gates)
# Devuelve dict solo si B_SIGNAL disparo en las ultimas `lookback` velas.
# ======================================================================
def analizar_ticker(sym, df, lookback=3):
    if df is None or df.empty or len(df) < 220: return None
    df = df.dropna(subset=['Close','Volume']).copy()
    df = df[df['Volume'] > 0].copy()
    if len(df) < 220: return None
    C, H, L, V = df['Close'], df['High'], df['Low'], df['Volume']

    # --- BANDA (STD 60 suavizada 20; cortes CRH V5 = 1.5/3.0) ---
    ret = C.pct_change()*100
    beta = ret.rolling(60).std(ddof=0).rolling(20).mean()
    banda_pre = pd.Series(np.where(beta<1.5,1,np.where(beta<3.0,2,3)), index=df.index)

    # --- MEDIAS Y CONTEXTO MACRO ---
    ma20=C.ewm(span=20,adjust=False).mean(); ma50=C.ewm(span=50,adjust=False).mean(); ma200=C.ewm(span=200,adjust=False).mean()
    ma20_up=ma20>ma20.shift(1); ma50_sube=ma50>ma50.shift(3); ema200_baja=ma200<ma200.shift(1)
    es_bajista_critico=(C<ma200)&ema200_baja&(C<ma20)
    en_tendencia=(((C>ma50)&ma50_sube&(ma50>ma200)).rolling(5).sum()>=3)

    # --- ATR Wilder ---
    pc=C.shift(1); tr=pd.concat([H-L,(H-pc).abs(),(L-pc).abs()],axis=1).max(axis=1)
    atr=tr.ewm(alpha=1/14,adjust=False).mean()

    # --- ADX (con DI+/DI-) ---
    hd=H-H.shift(1); ld=L.shift(1)-L
    dmp=pd.Series(np.where((hd>0)&(hd>ld),hd,0.0),index=df.index).rolling(14).sum()
    dmm=pd.Series(np.where((ld>0)&(ld>hd),ld,0.0),index=df.index).rolling(14).sum()
    tr14=tr.rolling(14).sum().replace(0,np.nan)
    pdi=dmp*100/tr14; mdi=dmm*100/tr14
    adx=((pdi-mdi).abs()/(pdi+mdi).replace(0,np.nan)*100).rolling(9).mean()

    # --- KDJ ---
    lmin=L.rolling(9).min(); hmax=H.rolling(9).max()
    rsv=(C-lmin)/(hmax-lmin).replace(0,np.nan)*100
    kval=rsv.ewm(alpha=1/3,adjust=False).mean(); dval=kval.ewm(alpha=1/3,adjust=False).mean()
    jv=3*kval-2*dval; giro_j=jv>jv.shift(1)
    cross_kd=(kval>dval)&(kval.shift(1)<=dval.shift(1))

    # --- MACD ---
    dif=C.ewm(span=12,adjust=False).mean()-C.ewm(span=26,adjust=False).mean()
    dea=dif.ewm(span=9,adjust=False).mean(); histo=dif-dea
    giro_macd=(histo>histo.shift(1))&(histo.shift(1)<=histo.shift(2))
    macd_conv=(histo<0)&(histo>histo.shift(1))&(histo>histo.shift(2))
    tendencia_viva=((dif>0)|macd_conv)&ma20_up&(pdi>mdi)&(C>ma50)

    # --- RSI SIMPLE (OSC como CRH V5, NO Wilder) ---
    up=(C-pc).clip(lower=0).rolling(14).sum(); dn=(pc-C).clip(lower=0).rolling(14).sum()
    osc=up/(up+dn).replace(0,np.nan)*100

    # --- Bollinger ---
    bb_mid=C.rolling(20).mean(); bb_std=C.rolling(20).std(ddof=0); bb_dn=bb_mid-2*bb_std

    # --- Volumen (umbrales CRH V5) ---
    vma=V.rolling(20).mean()
    vol_ok=V>vma*1.02; vol_med=V>vma*1.2; vol_alt=V>vma*1.4; vol_soft=V>vma*0.88

    # --- Gates de contexto ---
    adx_cayendo=(adx<adx.shift(2))&(adx<adx.shift(4))
    en_lateral=adx_cayendo&(C<bb_mid)&(~tendencia_viva)
    adx_req=pd.Series(np.where(es_bajista_critico,28,np.where(banda_pre==3,22,18)),index=df.index)
    ma50_alcista=ma50>ma50.shift(5)
    venia_sobre_ma50=(C.shift(1)>ma50).rolling(3).sum()>=2
    ma200_plana_sube=ma200>=ma200.shift(3)
    soporte_sano=~(es_bajista_critico|((adx>30)&(mdi>pdi)))
    permite_mom=~en_lateral

    # --- LOS 9 GATILLOS DEL CRH V5 ---
    s_pull=(L<ma50*1.015)&(C>ma50*0.985)&giro_j&vol_ok&ma50_alcista&venia_sobre_ma50
    s_impu=(C>H.rolling(5).max().shift(1))&(adx>adx_req)&ma20_up&giro_j&vol_ok&permite_mom
    s_boll=(L.shift(1)<=bb_dn)&(C>bb_dn)&giro_j&giro_macd&vol_soft&soporte_sano
    s_suelo=(osc<35)&(jv<25)&(C>L.shift(1))&giro_macd&vol_soft&soporte_sano
    s_macd=(dif>dea)&(dif.shift(1)<=dea.shift(1))&(histo>histo.shift(1))&ma20_up&vol_ok&permite_mom
    s_early=(osc<40)&(jv<30)&cross_kd&ma20_up&vol_soft&soporte_sano
    s_cont=(C>H.rolling(10).max().shift(1))&(C>ma50)&ma50_sube&giro_j&permite_mom
    s_reb200=(L<=ma200*1.01)&(C>ma200)&(C>L.shift(1))&giro_j&ma20_up&ma200_plana_sube&vol_ok
    s_rec=(C>ma20)&(C.shift(1)<=ma20.shift(1))&ma50_sube&(ma50>ma200)&(C>ma50)&giro_j&vol_soft

    # --- Gating de banda: B3 no admite S_PULL ni S_EARLY ---
    trig_all=s_pull|s_impu|s_boll|s_suelo|s_macd|s_early|s_cont|s_reb200|s_rec
    trig_vol=s_impu|s_boll|s_suelo|s_macd|s_cont|s_reb200|s_rec
    b_raw=pd.Series(np.where(banda_pre==3,trig_vol,trig_all),index=df.index).astype(bool)
    b_signal=b_raw&(~b_raw.shift(1,fill_value=False))   # SEÑAL FRESCA (primera vela del raw)

    # --- ¿disparo en las ultimas `lookback` velas? ---
    recent=b_signal.iloc[-lookback:]
    if not recent.any(): return None
    barras_desde=int((len(b_signal)-1)-np.where(b_signal.values)[0][-1])
    i=len(df)-1-barras_desde   # indice de la vela de señal

    def _f(s):
        try: return bool(s.iloc[i])
        except: return False
    fired={'S_PULL':_f(s_pull),'S_IMPU':_f(s_impu),'S_BOLL':_f(s_boll),'S_SUELO':_f(s_suelo),
           'S_MACD':_f(s_macd),'S_EARLY':_f(s_early),'S_CONT':_f(s_cont),'S_REB200':_f(s_reb200),'S_REC':_f(s_rec)}
    banda_sig=int(banda_pre.iloc[i])
    if banda_sig==3:
        fired['S_PULL']=False; fired['S_EARLY']=False
    triggers=[k for k,v in fired.items() if v]
    if not triggers: return None

    precio=float(C.iloc[-1]); precio_sig=float(C.iloc[i])
    atr_v=float(atr.iloc[i]) if not pd.isna(atr.iloc[i]) else 0.0
    pdi_v=float(pdi.iloc[-1]) if not pd.isna(pdi.iloc[-1]) else 0.0
    mdi_v=float(mdi.iloc[-1]) if not pd.isna(mdi.iloc[-1]) else 0.0
    vol_med_v=bool(vol_med.iloc[i]); vol_alt_v=bool(vol_alt.iloc[i])

    # --- Tipo de setup ---
    rev={'S_SUELO','S_BOLL','S_EARLY','S_REB200'}; mom={'S_IMPU','S_CONT','S_MACD'}; pull={'S_PULL','S_REC'}
    ts=set(triggers)
    if ts&mom and not ts&rev: tipo='Momentum'
    elif ts&rev and not ts&mom: tipo='Reversión'
    elif ts&pull and not ts&mom and not ts&rev: tipo='Pullback'
    else: tipo='Mixto'

    # --- Convicción 0-5 (SOLO para ordenar; el filtro real son los gates) ---
    n=len(triggers)
    conv=(2 if n>=3 else (1 if n==2 else 0)) + (1 if pdi_v>mdi_v else 0) + (1 if vol_med_v else 0) + (1 if banda_sig<=2 else 0)
    conv=min(conv,5)

    banda_txt={1:"🟦 B1",2:"🟨 B2",3:"🟥 B3"}[banda_sig]
    abrev={'S_PULL':'PULL','S_IMPU':'IMPU','S_BOLL':'BOLL','S_SUELO':'SUELO','S_MACD':'MACD',
           'S_EARLY':'EARLY','S_CONT':'CONT','S_REB200':'REB200','S_REC':'REC'}
    trig_txt=" ".join(abrev[t] for t in triggers)

    return {
        "sym": sym, "precio": precio, "precio_str": f"${precio:.2f}", "precio_sig": precio_sig,
        "osc": float(osc.iloc[-1]) if not pd.isna(osc.iloc[-1]) else 50.0,
        "rsi_str": f"{osc.iloc[-1]:.1f}" if not pd.isna(osc.iloc[-1]) else "—",
        "j": float(jv.iloc[-1]) if not pd.isna(jv.iloc[-1]) else 50.0,
        "j_str": f"{jv.iloc[-1]:.1f}" if not pd.isna(jv.iloc[-1]) else "—",
        "adx": float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 0.0,
        "adx_str": f"{adx.iloc[-1]:.1f}" if not pd.isna(adx.iloc[-1]) else "—",
        "score": conv, "n_trig": n, "triggers": triggers, "trig_txt": trig_txt, "tipo": tipo,
        "banda": banda_sig, "banda_txt": banda_txt,
        "atr_abs": atr_v, "atr_str": f"${atr_v:.2f}" if atr_v>0 else "—",
        "barras_desde": barras_desde,
        "en_tendencia": bool(en_tendencia.iloc[i]),
        "pdi": pdi_v, "mdi": mdi_v, "ma200": float(ma200.iloc[-1]),
        "vol_alt": vol_alt_v, "vol_med": vol_med_v,
    }

# ======================================================================
# HEADER
# ======================================================================
st.markdown("""
<div class="header"><div>
  <h1>🎯 Screener <span>CRH V5</span> · radar de la gran lista</h1>
  <p>9 GATILLOS CRH V5 · GATES DE BANDA + CONTEXTO · SEÑAL FRESCA · BLACKOUT EARNINGS · FUNDAMENTAL</p>
</div></div>
""", unsafe_allow_html=True)

# ======================================================================
# MARKET DATA
# ======================================================================
indices, vix, btc_pct, btc_price = get_market_data()
st.markdown('<div class="idx-grid">', unsafe_allow_html=True)
for name, data in indices.items():
    p=data.get("price"); pct=data.get("pct")
    if p is None or pct is None:
        st.markdown(f'<div class="idx-card"><div class="idx-label">{name}</div><div class="idx-price" style="color:#4a5568">—</div><div style="color:#4a5568">s/d</div></div>', unsafe_allow_html=True)
        continue
    cls="up" if pct>=0 else "down"; sig="+" if pct>=0 else ""
    st.markdown(f'<div class="idx-card"><div class="idx-label">{name}</div><div class="idx-price">{p:,.0f}</div><div class="{cls}">{sig}{pct:.2f}%</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

sp_pct=(indices.get("S&P 500",{}).get("pct") or 0)
_vix_val = vix if vix is not None else 0
vcls="ok" if _vix_val<18 else ("warn" if _vix_val<25 else "bad")
_btc_pct_val = btc_pct if btc_pct is not None else 0
bcls="up" if _btc_pct_val>=0 else "down"; bsig="+" if _btc_pct_val>=0 else ""
bp=f"${btc_price:,.0f}" if (btc_price and btc_price>0) else "—"
_alcista_ui = regimen_alcista()

st.markdown(f"""
<div class="ctx-grid">
  <div class="ctx-card"><div class="ctx-label">VIX</div><div class="ctx-val">{(f"{_vix_val:.1f}" if vix is not None else "—")}</div><div class="ctx-sub {vcls}">{"✅ Tranquilo" if _vix_val<18 else ("⚠️ Moderado" if _vix_val<25 else "🔴 Alto")}</div></div>
  <div class="ctx-card"><div class="ctx-label">BTC</div><div class="ctx-val {bcls}">{bp}</div><div class="ctx-sub {bcls}">{(f"{bsig}{_btc_pct_val:.2f}%" if btc_pct is not None else "s/d")}</div></div>
  <div class="ctx-card"><div class="ctx-label">Régimen SPY</div><div class="ctx-val" style="font-size:12px;margin-top:4px;">&nbsp;</div><div class="ctx-sub {'ok' if _alcista_ui else 'bad'}" style="font-size:12px;">{("🟢 Alcista (>EMA50)" if _alcista_ui else "🔴 Bajista (<EMA50) · cuchillos −2")}</div></div>
</div>
""", unsafe_allow_html=True)

# ======================================================================
# TICKERS COMPARTIDOS
# ======================================================================
compartidos = leer_tickers_compartidos()
with st.expander(f"➕ Agregar tickers a la watchlist compartida ({len(compartidos)} agregados)", expanded=False):
    st.markdown('<div style="font-size:11px;color:#4a5568;margin-bottom:6px;">Uno o varios separados por coma (ej: <b>ALK, PYPL, V</b>). Se guardan para todos y no se repiten.</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([4,1])
    with col1:
        nuevos_input = st.text_input("Tickers", placeholder="ALK, PYPL, V", label_visibility="collapsed")
    with col2:
        agregar = st.button("Agregar", use_container_width=True)
    if agregar and nuevos_input.strip():
        base_set=set(TICKERS); comp_set=set(compartidos)
        pedidos=[normalizar_ticker(t) for t in nuevos_input.replace("\n",",").split(",")]
        pedidos=[t for t in pedidos if t]
        nuevos_unicos, ya_existen, invalidos = [], [], []
        for t in pedidos:
            if not ticker_valido(t): invalidos.append(t)
            elif t in base_set or t in comp_set or t in nuevos_unicos: ya_existen.append(t)
            else: nuevos_unicos.append(t)
        if nuevos_unicos:
            ok, msg = escribir_tickers_compartidos(compartidos + nuevos_unicos)
            if ok:
                aviso=f"✅ Agregados: {', '.join(nuevos_unicos)}"
                if ya_existen: aviso += f" · Ya existían: {', '.join(ya_existen)}"
                if invalidos: aviso += f" · ⚠️ Inválidos: {', '.join(invalidos)}"
                st.success(aviso); st.info("Entran en el próximo barrido. Usa 🔄 abajo para escanearlos ahora.")
                leer_tickers_compartidos.clear()
            else: st.error(f"No se pudo guardar: {msg}")
        else:
            msg_w=""
            if ya_existen: msg_w+=f"Ya estaban: {', '.join(ya_existen)}. "
            if invalidos: msg_w+=f"⚠️ Inválidos: {', '.join(invalidos)} (usa el símbolo, ej AAPL)."
            st.warning(msg_w or "Nada que agregar.")
    if compartidos:
        st.markdown(f'<div style="font-size:10px;color:#4a5568;margin-top:8px;">Compartidos: {", ".join(compartidos)}</div>', unsafe_allow_html=True)
    st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
    if st.button("🔄 Re-escanear ahora", use_container_width=True):
        st.cache_data.clear(); st.rerun()

_vistos=set(); WATCHLIST=[]
for t in list(TICKERS)+compartidos:
    if t not in _vistos: WATCHLIST.append(t); _vistos.add(t)

# ======================================================================
# HISTORIAL
# ======================================================================
def leer_historial():
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = _json.loads(r.read().decode())
        if "historial.json" in data["files"]:
            return _json.loads(data["files"]["historial.json"]["content"])
    except Exception: pass
    return []
_hist = leer_historial()

# ======================================================================
# BARRIDO
# ======================================================================
@st.cache_data(ttl=300, show_spinner=False)
def descargar_batch(tickers_tuple):
    return yf.download(list(tickers_tuple), period="2y", group_by="ticker",
                       progress=False, auto_adjust=True, threads=True)

@st.cache_data(ttl=300, show_spinner=False)
def precios_actuales(watchlist_tuple):
    df_batch = descargar_batch(watchlist_tuple); precios = {}
    for sym in watchlist_tuple:
        try:
            if isinstance(df_batch.columns, pd.MultiIndex):
                if sym in df_batch.columns.get_level_values(0):
                    cl = df_batch[sym]["Close"].dropna()
                    if len(cl) > 0: precios[sym] = float(cl.iloc[-1])
            else:
                cl = df_batch["Close"].dropna()
                if len(cl) > 0: precios[sym] = float(cl.iloc[-1])
        except Exception: pass
    return precios

def fetch_fund(item):
    """Fundamentales + earnings para un candidato (corre en paralelo)."""
    sym = item["sym_original"]
    skip = any(x in sym for x in ['-USD','-F','=X','=F','.DE','.SW','.HK'])
    item["target"]=item["consenso"]=item["pe_ttm"]=item["pe_fwd"]="—"
    item["upside"]="—"; item["fv"]="—"; item["fv_up"]="—"; item["valor_pts"]=0
    # earnings (para TODOS los candidatos, tambien los skip de fundamentales salvo cripto/fx/fut)
    d_prox, d_ult, exento = dias_a_earnings(sym)
    item["earn_prox"]=d_prox; item["earn_ult"]=d_ult; item["earn_exento"]=exento
    if skip: return item
    fund = fetch_fundamentales(sym)
    if not fund: return item
    tm = fund.get("target_mean")
    item["target"] = f"${tm:.0f}" if tm else "—"
    up_txt, target_up_raw, _ = calc_upside(item["precio"], tm); item["upside"] = up_txt
    item["consenso"] = consenso(fund.get("rec_mean"), fund.get("n_analysts"))
    pe=fund.get("pe_ttm"); item["pe_ttm"]=f"{pe:.1f}" if pe and pe>0 else "—"
    pef=fund.get("pe_fwd"); item["pe_fwd"]=f"{pef:.1f}" if pef and pef>0 else "—"
    fv_txt, fv_up_txt, fv_up_raw = calc_fair_value(fund, fund.get("pe_ttm"), item["precio"])
    item["fv"]=fv_txt; item["fv_up"]=fv_up_txt
    fv_ok=(fv_up_raw is not None and fv_up_raw>=15); target_ok=(target_up_raw is not None and target_up_raw>=15)
    item["valor_pts"]=2 if (fv_ok and target_ok) else (1 if fv_ok else 0)
    return item

@st.cache_data(ttl=300, show_spinner=False)
def barrido_completo(watchlist_tuple, lookback):
    df_batch = descargar_batch(watchlist_tuple)
    resultados = []
    for sym in watchlist_tuple:
        try:
            if isinstance(df_batch.columns, pd.MultiIndex):
                df_sym = df_batch[sym].copy() if sym in df_batch.columns.get_level_values(0) else None
            else:
                df_sym = df_batch.copy()
            datos = analizar_ticker(sym, df_sym, lookback=lookback)
        except Exception:
            datos = None
        if datos is not None:
            datos["sym_original"] = sym
            resultados.append(datos)
    with ThreadPoolExecutor(max_workers=4) as ex:
        todos = list(ex.map(fetch_fund, resultados))
    for x in todos:
        x.setdefault("valor_pts", 0)
    # Filtro de regimen: SPY < EMA50 -> castigar cuchillos (reversion sin DI+ bajo MA200)
    if not regimen_alcista():
        for x in todos:
            if x.get("tipo")=="Reversión" and x["pdi"] <= x["mdi"] and x["precio"] < x.get("ma200", x["precio"]):
                x["score"] = max(0, x["score"] - 2)
    return todos

# lookback de señal: cuantos dias hacia atras aceptar la señal fresca (1=solo hoy)
LOOKBACK = 3

with st.spinner(f"Escaneando {len(WATCHLIST)} tickers con los gatillos del CRH V5..."):
    todos = barrido_completo(tuple(WATCHLIST), LOOKBACK)
_precios_hoy = precios_actuales(tuple(WATCHLIST))

# ======================================================================
# CONTROL DE BLACKOUT (post-filtro en vivo, no re-escanea)
# ======================================================================
dias_black = st.slider(
    "⏰ Blackout de earnings — sacar de COMPRAS los que reportan en ≤N días hábiles",
    min_value=0, max_value=5, value=3, step=1,
    help="0 = desactivado. Tu diagnostico: GDDY y ambos FICO eran pre-earnings. El default 3 los saca."
)

# aplicar estado de earnings a cada candidato
en_blackout, limpios = [], []
for x in todos:
    bloquear, txt = estado_earnings(x.get("earn_prox"), x.get("earn_ult"), x.get("earn_exento", False), dias_black)
    x["earn_txt"] = txt
    (en_blackout if bloquear else limpios).append(x)

# ======================================================================
# HISTORIAL (expander) — reutiliza infraestructura existente
# ======================================================================
def _precio_num_h(s):
    try: return float(str(s).replace("$","").replace(",","").strip())
    except: return None

from datetime import datetime as _dt, timezone as _tz, timedelta as _td
_ahora_ny = _dt.now(_tz(_td(hours=-5)))
_sello = _ahora_ny.strftime("%Y-%m-%d %H:%M")

_label = f"📸 Historial TOP PICKS - últimos {len(_hist)} días (cierre NY)" if _hist else "📸 Historial TOP PICKS - se llena tras el cierre de NY"
with st.expander(_label, expanded=False):
    st.markdown('<div style="font-size:11px;color:#4a5568;margin-bottom:8px;">Foto automática de las TOP al cierre de NY. Memoria de 15 días.</div>', unsafe_allow_html=True)
    if not _hist:
        st.markdown('<div style="color:#718096;font-size:12px;padding:8px 0;">Aún no hay fotos guardadas.</div>', unsafe_allow_html=True)
    else:
        for foto in reversed(_hist):
            fecha=foto.get("fecha","?"); tops=foto.get("tops",[])
            if not tops:
                st.markdown(f'<div style="color:#718096;font-size:12px;margin:6px 0;"><b>{fecha}</b> - sin TOP PICKS</div>', unsafe_allow_html=True); continue
            filas=""
            for t in tops:
                sym=t["sym"]; precio_top=t.get("precio","-"); precio_hoy=_precios_hoy.get(sym)
                if precio_hoy is None:
                    celda='<td style="color:#4a5568">—</td>'
                else:
                    p0=_precio_num_h(precio_top); ph=precio_hoy
                    if p0 and ph and p0>0:
                        chg=(ph-p0)/p0*100; col="#00e5a0" if chg>=0 else "#ff4d6d"; sg="+" if chg>=0 else ""
                        celda='<td style="font-weight:700;color:'+col+'">$'+f"{ph:.2f}"+' <span style="font-size:9px;font-weight:400">('+sg+f"{chg:.1f}"+'%)</span></td>'
                    else:
                        celda='<td style="font-weight:700">$'+f"{ph:.2f}"+'</td>'
                filas+='<tr><td style="text-align:left"><a class="tk" href="'+finviz_url(sym)+'" target="_blank">'+sym+'</a></td><td style="text-align:center;color:#00e5a0;font-weight:700">'+str(t["score"])+'</td><td style="font-size:10px">'+t.get("gatillos","")+'</td><td>'+precio_top+'</td>'+celda+'<td>'+t.get("fv","-")+'</td><td>'+t.get("upside","-")+'</td><td>'+t.get("rsi","-")+'</td></tr>'
            titulo='<div style="font-family:Syne,sans-serif;font-weight:700;color:#00d4ff;font-size:13px;margin-bottom:4px;">'+fecha+' - '+str(len(tops))+' picks</div>'
            tabla='<div class="tw"><table><thead><tr><th style="text-align:left">Ticker</th><th style="text-align:center">Conv</th><th>Gatillos</th><th>Precio</th><th style="color:#00d4ff">Precio hoy</th><th>FV</th><th>Upside</th><th>RSI</th></tr></thead><tbody>'+filas+'</tbody></table></div>'
            st.markdown('<div style="margin:10px 0;">'+titulo+tabla+'</div>', unsafe_allow_html=True)

# ======================================================================
# CALCULADORA DE GESTION (sin cambios de logica; lee de `todos`)
# ======================================================================
with st.expander("🧮 Calculadora de gestión (SL / TP / tamaño de posición)", expanded=False):
    st.markdown("""<div style='font-size:11px;color:#a0aec0;line-height:1.6;background:#0d1424;border:1px solid #1e3a5f;border-radius:8px;padding:10px 12px;margin-bottom:10px;'>
<b style='color:#00d4ff'>Banda de volatilidad</b> = cuánto se mueve la acción; define el margen del Stop. Mismos cortes que el CRH V5 (STD 60 → 1.5/3.0).<br>
🟦 <b>B1</b>: SL 1.3× ATR · TP1 2.0× · TP2 3.5× &nbsp; 🟨 <b>B2</b>: SL 1.5× · TP1 2.2× · TP2 4.0× &nbsp; 🟥 <b>B3</b>: SL 1.8-2.0× · TP1 2.8× · TP2 5.0×<br>
<span style='color:#718096'>El deslizador va de 0.5 (ajustado) a 3.5 (amplio); el recomendado queda prefijado en la banda del activo.</span>
</div>""", unsafe_allow_html=True)
    modo = st.radio("Modo", ["Desde candidato del barrido", "Manual (cualquier acción)"], horizontal=True, label_visibility="collapsed")
    _mapa = {x["sym_original"]: x for x in todos}; _syms = sorted(_mapa.keys())
    sym_label=""; precio_actual=0.0; atr=0.0; banda_reco=2; _slider_key="nivel_riesgo_manual"
    if modo == "Desde candidato del barrido":
        if not _syms:
            st.info("Sin candidatos hoy. Usa el modo Manual.")
        else:
            cc1, cc2 = st.columns([3,3])
            with cc1: sym_sel = st.selectbox("Ticker (candidato)", _syms)
            x=_mapa[sym_sel]; sym_label=sym_sel; precio_actual=x["precio"]; atr=x.get("atr_abs",0) or 0
            banda_reco=x.get("banda",2); _slider_key=f"nivel_riesgo_{sym_sel}"
            with cc2:
                st.markdown("<div style='font-size:11px;color:#718096;padding-top:30px;'>Autocompletado: "+x.get("banda_txt","?")+" · ATR $"+f"{atr:.2f}"+" · actual $"+f"{precio_actual:.2f}"+"</div>", unsafe_allow_html=True)
    else:
        m1,m2,m3 = st.columns([2,2,2])
        with m1: sym_label = st.text_input("Ticker", value="", placeholder="ej: AAPL")
        with m2: precio_actual = st.number_input("Precio actual ($)", min_value=0.0, value=100.0, step=0.01, format="%.2f")
        with m3: atr = st.number_input("ATR ($)", min_value=0.0, value=2.0, step=0.01, format="%.2f")
        banda_reco=2; _slider_key="nivel_riesgo_manual"
    _reco_txt={1:"🟦 B1",2:"🟨 B2",3:"🟥 B3"}.get(banda_reco,"🟨 B2")
    st.markdown("<div style='font-size:11px;color:#a0aec0;margin:4px 0 2px;'>Recomendado para este activo: <b style='color:#00d4ff'>"+_reco_txt+"</b> (nivel "+f"{float(banda_reco):.1f}"+"). Mueve el deslizador para ajustar.</div>", unsafe_allow_html=True)
    nivel = st.slider("Nivel de riesgo SL/TP", min_value=0.5, max_value=3.5, value=float(banda_reco), step=0.1, key=_slider_key, label_visibility="collapsed")
    _niv_x=[0.5,1.0,2.0,3.0,3.5]
    sl_mult=float(np.interp(nivel,_niv_x,[1.0,1.3,1.5,2.0,2.5]))
    tp1_mult=float(np.interp(nivel,_niv_x,[1.7,2.0,2.2,2.8,3.3]))
    tp2_mult=float(np.interp(nivel,_niv_x,[3.0,3.5,4.0,5.0,6.0]))
    if nivel<1.0: zona="⬇️ Ajustado"
    elif nivel<1.5: zona="🟦 B1"
    elif nivel<2.5: zona="🟨 B2"
    elif nivel<=3.0: zona="🟥 B3"
    else: zona="⬆️ Amplio"
    st.markdown("<div style='font-size:12px;color:#a0aec0;margin:2px 0 6px;'>Posición: <b>"+zona+"</b> · SL <b>"+f"{sl_mult:.2f}"+"×</b> · TP1 <b>"+f"{tp1_mult:.2f}"+"×</b> · TP2 <b>"+f"{tp2_mult:.2f}"+"×</b> ATR</div>", unsafe_allow_html=True)
    e1,e2,e3 = st.columns([2,2,2])
    with e1: usar_actual = st.checkbox("Usar precio actual como entrada", value=True)
    with e2:
        if usar_actual:
            entrada=precio_actual; st.markdown("<div style='font-size:12px;color:#a0aec0;padding-top:8px;'>Entrada: <b>$"+f"{entrada:.2f}"+"</b></div>", unsafe_allow_html=True)
        else:
            entrada=st.number_input("Precio de entrada ($)", min_value=0.0, value=float(round(precio_actual,2)) if precio_actual>0 else 0.0, step=0.01, format="%.2f")
    with e3: monto = st.number_input("Monto (USD)", min_value=0.0, value=100.0, step=50.0, format="%.0f")
    if entrada>0 and atr>0:
        sl=entrada-atr*sl_mult; tp1=entrada+atr*tp1_mult; tp2=entrada+atr*tp2_mult
        riesgo_usd=(entrada-sl); rr1=(tp1-entrada)/riesgo_usd if riesgo_usd>0 else 0; rr2=(tp2-entrada)/riesgo_usd if riesgo_usd>0 else 0
        acciones=(monto/entrada) if entrada>0 else 0; riesgo_total=acciones*riesgo_usd; riesgo_pct=(riesgo_total/monto*100) if monto>0 else 0
        st.markdown("<div style='font-family:Syne,sans-serif;font-weight:700;color:#00d4ff;font-size:14px;margin:6px 0;'>"+(sym_label or "Acción")+"  ·  "+zona+"</div>", unsafe_allow_html=True)
        res_sl=acciones*(sl-entrada); res_tp1=acciones*(tp1-entrada); res_tp2=acciones*(tp2-entrada)
        def _fmt(neto):
            final=monto+neto; signo="+" if neto>=0 else "-"
            return "$"+f"{final:.2f}"+" <span style='font-size:9px;color:#718096'>("+signo+"$"+f"{abs(neto):.2f}"+")</span>"
        filas=[("Stop Loss","$"+f"{sl:.2f}","-"+f"{(entrada-sl)/entrada*100:.1f}"+"%",_fmt(res_sl),f"{sl_mult:.2f}x ATR"),
               ("Take Profit 1","$"+f"{tp1:.2f}","+"+f"{(tp1-entrada)/entrada*100:.1f}"+"%",_fmt(res_tp1),f"{tp1_mult:.2f}x · R:R "+f"{rr1:.1f}"),
               ("Take Profit 2","$"+f"{tp2:.2f}","+"+f"{(tp2-entrada)/entrada*100:.1f}"+"%",_fmt(res_tp2),f"{tp2_mult:.2f}x · R:R "+f"{rr2:.1f}")]
        html='<div class="tw"><table><thead><tr><th style="text-align:left">Nivel</th><th>Precio</th><th>%</th><th>Resultado</th><th>Base</th></tr></thead><tbody>'
        for n,p,pct,res,base in filas:
            col="#00e5a0" if "Profit" in n else "#ff4d6d"
            html+='<tr><td style="text-align:left;color:'+col+';font-weight:600">'+n+'</td><td>'+p+'</td><td style="color:'+col+'">'+pct+'</td><td style="color:'+col+';font-weight:600">'+res+'</td><td style="font-size:10px;color:#718096">'+base+'</td></tr>'
        html+="</tbody></table></div>"; st.markdown(html, unsafe_allow_html=True)
        st.markdown("<div style='font-size:12px;color:#a0aec0;margin-top:8px;'>💰 <b>"+f"{acciones:.2f}"+" acciones</b> con $"+f"{monto:.0f}"+" a $"+f"{entrada:.2f}"+" · Riesgo si toca SL: <b style='color:#ff4d6d'>$"+f"{abs(riesgo_total):.2f}"+"</b> ("+f"{riesgo_pct:.1f}"+"%)</div>", unsafe_allow_html=True)
        mitad=acciones/2; g1=mitad*(tp1-entrada); g2=mitad*(tp2-entrada)
        st.markdown("<div style='background:#0d1424;border:1px solid #1e3a5f;border-radius:8px;padding:10px 12px;margin-top:10px;font-size:12px;color:#a0aec0;line-height:1.7;'>"
            +"<b style='color:#00d4ff'>📊 Plan de salida 50/50</b><br>"
            +"<b>1.</b> En <b style='color:#00e5a0'>TP1 ($"+f"{tp1:.2f}"+")</b>: cierra 50% → +$"+f"{g1:.2f}"+" y sube stop a breakeven ($"+f"{entrada:.2f}"+")<br>"
            +"<b>2.</b> El 50% restante corre con riesgo cero<br>"
            +"<b>3.</b> En <b style='color:#00e5a0'>TP2 ($"+f"{tp2:.2f}"+")</b>: cierra el resto → +$"+f"{g2:.2f}"+" extra (total +$"+f"{g1+g2:.2f}"+")"
            +"</div>", unsafe_allow_html=True)
    else:
        st.info("Completa precio de entrada y ATR (>0) para calcular.")

# ======================================================================
# RESUMEN
# ======================================================================
n_mom=sum(1 for x in limpios if x["tipo"]=="Momentum")
n_rev=sum(1 for x in limpios if x["tipo"]=="Reversión")
n_pull=sum(1 for x in limpios if x["tipo"]=="Pullback")
n_mix=sum(1 for x in limpios if x["tipo"]=="Mixto")
n_valor=sum(1 for x in limpios if x.get("valor_pts",0)>0)
n_hoy=sum(1 for x in limpios if x["barras_desde"]==0)
_reg_txt = "🟢 régimen alcista" if _alcista_ui else "🔴 régimen bajista (cuchillos −2)"
st.markdown(f'<div style="text-align:center;color:var(--muted);font-size:12px;padding:8px 0 4px;letter-spacing:.05em;">✅ {len(WATCHLIST)} tickers · {len(limpios)} señales CRH V5 ({n_hoy} hoy) · 🟢 {n_mom} momentum · 🔵 {n_rev} reversión · 🟣 {n_pull} pullback · ⚪ {n_mix} mixto · 💎 {n_valor} valor · ⏰ {len(en_blackout)} en earnings · {_reg_txt}</div>', unsafe_allow_html=True)
st.markdown(f'<div style="text-align:center;color:#4a5568;font-size:10px;padding:0 0 14px;letter-spacing:.04em;">🕑 escaneo {_sello} hora NY · señal fresca (≤{LOOKBACK}d) · gatillos idénticos al CRH V5 de Moomoo</div>', unsafe_allow_html=True)

# ======================================================================
# TABLA HTML (ordenable) — columnas adaptadas al CRH V5
# ======================================================================
import re as _re2
_TABLA_N=[0]
def _color(col, val):
    s=str(val)
    if col=="RSI":
        try:
            r=float(s)
            if r<33: return "color:#ff4d6d;font-weight:600"
            if r>65: return "color:#00e5a0;font-weight:600"
        except: pass
        return "color:#4a5568"
    if col=="J":
        try:
            r=float(s)
            if r<20: return "color:#ff4d6d;font-weight:600"
            if r>80: return "color:#ffd166;font-weight:600"
        except: pass
        return "color:#4a5568"
    if col in ("Upside","vs FV"):
        if "🟢" in s: return "color:#00e5a0;font-weight:600"
        if "🔴" in s: return "color:#ff4d6d;font-weight:600"
        if "🟡" in s: return "color:#ffd166;font-weight:600"
        return "color:#4a5568"
    if col=="Conv":
        try:
            n=int(float(s))
            if n>=5: return "color:#00e5a0;font-weight:700;text-align:center"
            if n==4: return "color:#00d4ff;font-weight:700;text-align:center"
            if n==3: return "color:#00d4ff;font-weight:600;text-align:center"
            if n==2: return "color:#b48cff;font-weight:600;text-align:center"
        except: pass
        return "color:#4a5568;text-align:center"
    if col=="Tipo":
        if "Momentum" in s: return "color:#00e5a0;font-weight:600"
        if "Reversión" in s: return "color:#00d4ff;font-weight:600"
        if "Pullback" in s: return "color:#b48cff;font-weight:600"
        return "color:#718096"
    if col=="Earn":
        if "⏰" in s: return "color:#ff4d6d;font-weight:600"
        if "🆕" in s: return "color:#ffd166;font-weight:600"
        if "?" in s: return "color:#b48cff"
        return "color:#4a5568"
    if col=="Cuándo":
        return "color:#00e5a0;font-weight:600" if s=="hoy" else "color:#718096"
    if col=="ATR": return "color:#a0aec0"
    return ""

def _sortval(col, raw, idx):
    s=str(raw)
    if col=="#": return idx
    if col=="Ticker":
        m=_re2.search(r'>([^<]+)</a>', s); return m.group(1) if m else s
    if col=="Cuándo":
        return {"hoy":0,"ayer":1}.get(s, 9)
    if col=="Tipo":
        return {"Momentum":0,"Mixto":1,"Pullback":2,"Reversión":3}.get(s.strip(),9)
    if col=="Earn":
        m=_re2.search(r'-?\d+', s); return float(m.group()) if m else 999
    if col=="ATR":
        try: return float(s.replace("$","")) 
        except: return -1
    m=_re2.search(r'-?\d+\.?\d*', s.replace(",",""))
    return float(m.group()) if m else -999999

def tabla_html(lista):
    _TABLA_N[0]+=1; tid=f"tw{_TABLA_N[0]}"
    cols=["#","Ticker","Conv","Tipo","Gatillos","Banda","Cuándo","Earn","Precio","ATR",
          "Fair Value","vs FV","Target 12M","Upside","RSI","J","ADX"]
    head="".join(f'<th>{c}<span class="ar"></span></th>' for c in cols)
    filas=[]
    for i,x in enumerate(lista,1):
        cuando="hoy" if x["barras_desde"]==0 else ("ayer" if x["barras_desde"]==1 else f"-{x['barras_desde']}d")
        vp=x.get("valor_pts",0); val_badge=" 💎💎" if vp==2 else (" 💎" if vp==1 else "")
        celdas={"#":str(i),"Ticker":f'<a class="tk" href="{finviz_url(x["sym"])}" target="_blank">{x["sym"]}</a>',
                "Conv":str(x.get("score","")),"Tipo":x.get("tipo","—"),
                "Gatillos":x.get("trig_txt","")+val_badge,"Banda":x.get("banda_txt","—"),
                "Cuándo":cuando,"Earn":x.get("earn_txt","—"),"Precio":x["precio_str"],"ATR":x.get("atr_str","—"),
                "Fair Value":x.get("fv","—"),"vs FV":x.get("fv_up","—"),"Target 12M":x.get("target","—"),
                "Upside":x.get("upside","—"),"RSI":x["rsi_str"],"J":x["j_str"],"ADX":x["adx_str"]}
        tds=[]
        for c in cols:
            sv=_sortval(c,celdas[c],i)
            if c in ("#","Ticker"): tds.append(f'<td data-s="{sv}">{celdas[c]}</td>')
            else: tds.append(f'<td data-s="{sv}" style="{_color(c,celdas[c])}">{celdas[c]}</td>')
        filas.append("<tr>"+"".join(tds)+"</tr>")
    return f'<div class="tw"><table id="{tid}"><thead><tr>'+head+'</tr></thead><tbody>'+"".join(filas)+'</tbody></table></div>'

# ======================================================================
# COMPRAS CRH V5 — bucketed por convicción
# ======================================================================
def _cambios_vs_ayer():
    foto_prev=None
    for foto in reversed(_hist):
        if foto.get("fecha") != _ahora_ny.strftime("%Y-%m-%d"):
            foto_prev=foto; break
    if not foto_prev: return None, None, None
    prev={t["sym"]: t.get("score",0) for t in foto_prev.get("tops",[])}
    hoy_t={x["sym"]: x["score"] for x in limpios if x["score"]>=4}
    nuevos=[s for s in hoy_t if s not in prev]
    subieron=[s for s in hoy_t if s in prev and hoy_t[s]>prev[s]]
    return foto_prev.get("fecha"), nuevos, subieron

_fp,_nv,_sb=_cambios_vs_ayer()
if _fp and (_nv or _sb):
    partes=[]
    if _nv: partes.append('<span style="color:#00e5a0;font-weight:600">🆕 Nuevos:</span> '+", ".join(_nv))
    if _sb: partes.append('<span style="color:#00d4ff;font-weight:600">⬆ Subieron:</span> '+", ".join(_sb))
    st.markdown(f'<div style="background:#0d1424;border:1px solid #1e3a5f;border-radius:10px;padding:10px 14px;margin:8px 0 14px;font-size:12px;color:#a0aec0;">Cambios vs {_fp}: '+" &nbsp;·&nbsp; ".join(partes)+'</div>', unsafe_allow_html=True)

st.markdown('<div class="sec sec-os">🎯 COMPRAS CRH V5 — SEÑAL FRESCA POR CONVICCIÓN</div>', unsafe_allow_html=True)
st.markdown("""<div class="glosario">
<b>Motor = CRH V5</b>: los mismos 9 gatillos de tu indicador de Moomoo, con gates de banda (1.5/3.0) y contexto (SOPORTE_SANO, PERMITE_MOM, bajista crítico). Solo aparece el <b>día que la señal dispara</b> (fresca, ≤{lb}d). &nbsp;·&nbsp;
<b>Gatillos</b>: PULL (pullback MA50) · IMPU (ruptura+ADX) · BOLL (banda inf.) · SUELO (OSC&lt;35+piso) · MACD (cruce) · EARLY (KDJ temprano) · CONT (continuación) · REB200 (rebote MA200) · REC (recupera MA20) &nbsp;·&nbsp;
<b>Tipo</b>: 🟢Momentum · 🔵Reversión · 🟣Pullback (define cómo gestionar) &nbsp;·&nbsp;
<b>Conv (0-5)</b>: confluencia (2+ gatillos) + DI+ manda + volumen ≥1.2× + banda limpia. <b>Es solo para ordenar</b>; el filtro de calidad son los gates. &nbsp;·&nbsp;
<b>ATR</b> $ (14d Wilder) para SL/TP · <b>💎VALOR</b> solo visual, NO suma · <b>Earn</b>: ⏰ reporta pronto (fuera) · 🆕 reportó hace poco · ✓ despejado
</div>""".replace("{lb}", str(LOOKBACK)), unsafe_allow_html=True)

def bucket(titulo, lista, color):
    if not lista: return
    st.markdown(f'<div style="font-family:Syne,sans-serif;font-weight:700;font-size:12px;color:{color};margin:14px 0 4px;letter-spacing:.05em;">{titulo} ({len(lista)})</div>', unsafe_allow_html=True)
    ordenada=sorted(lista, key=lambda x:(x["barras_desde"], -x["score"], -x["n_trig"]))
    st.markdown(tabla_html(ordenada), unsafe_allow_html=True)

c5=[x for x in limpios if x["score"]>=5]
c4=[x for x in limpios if x["score"]==4]
c3=[x for x in limpios if x["score"]==3]
c2=[x for x in limpios if x["score"]<=2]
bucket("🏆 CONVICCIÓN 5 — MÁXIMA (confluencia + DI+ + volumen + banda limpia)", c5, "#00e5a0")
bucket("🥇 CONVICCIÓN 4 — MUY FUERTE", c4, "#00d4ff")
bucket("🥈 CONVICCIÓN 3 — FUERTE", c3, "#00d4ff")
bucket("🥉 CONVICCIÓN ≤2 — VIGILANCIA", c2, "#b48cff")
if not limpios:
    st.info("Ningún ticker disparó una señal CRH V5 fresca en los últimos días. Esto es normal y esperado: el screener es de alta precisión, no de volumen. Mejor 0 buenas que 60 malas.")

# ======================================================================
# EN VENTANA DE EARNINGS (blackout) — mirar, no entrar aún
# ======================================================================
if en_blackout:
    st.markdown('<div class="sec sec-ea">⏰ EN VENTANA DE EARNINGS — NO ENTRAR (BLACKOUT)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="glosario">Estos <b>dispararon una señal CRH V5 válida</b> pero reportan resultados en ≤{dias_black} días hábiles. Aquí es donde el screener viejo pisaba las minas (GDDY −19.6%, FICO −16/−18%). Espera al reporte; si sobrevive y vuelve a disparar, entra entonces.</div>', unsafe_allow_html=True)
    st.markdown(tabla_html(sorted(en_blackout, key=lambda x:(x.get("earn_prox") or 99, -x["score"]))), unsafe_allow_html=True)

# ======================================================================
# JS DE ORDENAMIENTO
# ======================================================================
import streamlit.components.v1 as components
components.html("""
<script>
function ordenar(tabla, col, th){
    const tbody=tabla.querySelector('tbody'); const filas=Array.from(tbody.querySelectorAll('tr'));
    const asc=th.getAttribute('data-asc')!=='true';
    tabla.querySelectorAll('th').forEach(h=>{h.removeAttribute('data-asc'); const a=h.querySelector('.ar'); if(a)a.textContent='';});
    th.setAttribute('data-asc',asc); const ar=th.querySelector('.ar'); if(ar) ar.textContent=asc?' \u25B2':' \u25BC';
    filas.sort((ra,rb)=>{
        let a=ra.children[col].getAttribute('data-s'); let b=rb.children[col].getAttribute('data-s');
        const na=parseFloat(a), nb=parseFloat(b);
        if(!isNaN(na)&&!isNaN(nb)){return asc?na-nb:nb-na;}
        a=(a||'').toString(); b=(b||'').toString(); return asc?a.localeCompare(b):b.localeCompare(a);
    });
    filas.forEach(f=>tbody.appendChild(f));
}
function activar(){
    const doc=window.parent.document; const tablas=doc.querySelectorAll('.tw table');
    tablas.forEach(tabla=>{
        if(tabla.getAttribute('data-sortable')) return;
        tabla.setAttribute('data-sortable','1');
        tabla.querySelectorAll('th').forEach((th,idx)=>{th.style.cursor='pointer'; th.addEventListener('click',()=>ordenar(tabla,idx,th));});
    });
}
let intentos=0; const timer=setInterval(()=>{activar(); intentos++; if(intentos>20) clearInterval(timer);},400);
</script>
""", height=0)

st.markdown('<p class="footer">Screener CRH V5 · radar de la gran lista · señal = gatillos idénticos al indicador de Moomoo · solo educativo · no es asesoría</p>', unsafe_allow_html=True)
