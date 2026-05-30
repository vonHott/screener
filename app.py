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
# FUNDAMENTALES — fair value, target 12M, P/E, P/B, P/S, consensus
# ======================================================================
@st.cache_data(ttl=300, show_spinner=False)
def fetch_fundamentales(sym):
    """Datos fundamentales del ticker desde yfinance.info"""
    try:
        info = yf.Ticker(sym).info
        if not info or len(info) < 10:
            return None
        return {
            "target_mean":   info.get("targetMeanPrice"),
            "target_high":   info.get("targetHighPrice"),
            "target_low":    info.get("targetLowPrice"),
            "n_analysts":    info.get("numberOfAnalystOpinions"),
            "rec_mean":      info.get("recommendationMean"),
            "pe_ttm":        info.get("trailingPE"),
            "pe_fwd":        info.get("forwardPE"),
            "eps_ttm":       info.get("trailingEps"),
            "book_value":    info.get("bookValue"),
        }
    except:
        return None

    try:
        precios_5y = df_precio['Close'].tail(1260)
        precio_actual = float(precios_5y.iloc[-1])
        pe_hist = pe_actual * (precios_5y / precio_actual)
        pct = (pe_hist < pe_actual).sum() / len(pe_hist) * 100
        return round(pct, 0)
    except:
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


def calc_graham(eps_ttm, book_value, precio_actual):
    """Graham Number = sqrt(22.5 × EPS × BVPS). Devuelve (texto_fv, upside_txt, upside_raw).
    Solo válido con EPS y Book Value positivos."""
    if not eps_ttm or not book_value or eps_ttm <= 0 or book_value <= 0:
        return ("—", "—", None)
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

    # ── 1. SOBREVENTA FRESCA ──
    sobreventa = (
        rsi_v < 35 and
        bool(df['GIRO_J'].iloc[-1]) and
        precio > float(df['Low'].iloc[-2]) and
        bool(df['VOL_OK'].iloc[-1])
    )

    # ── 2. TOCANDO SOPORTE MA50 / MA200 / MA325 ──
    ma50_v  = float(df['MA50'].iloc[-1])
    ma200_v = float(df['MA200'].iloc[-1])
    ma325_v = float(df['MA325'].iloc[-1])
    low_v   = float(df['Low'].iloc[-1])
    toca_ma = (
        (low_v <= ma50_v * 1.015 and precio > ma50_v * 0.985) or
        (low_v <= ma200_v * 1.015 and precio > ma200_v * 0.985) or
        (low_v <= ma325_v * 1.015 and precio > ma325_v * 0.985)
    )
    soporte = (
        toca_ma and
        bool(df['GIRO_J'].iloc[-1]) and
        bool(df['VOL_OK'].iloc[-1])
    )

    # ── 3. REBOTE BOLLINGER ──
    bb_dn_y = float(df['BB_DN'].iloc[-2])
    low_y   = float(df['Low'].iloc[-2])
    bb_dn   = float(df['BB_DN'].iloc[-1])
    rebote_bb = (
        low_y <= bb_dn_y and
        precio > bb_dn and
        bool(df['GIRO_J'].iloc[-1]) and
        bool(df['VOL_OK'].iloc[-1])
    )

    # ── 4. CRUCE KDJ + MACD ──
    cruce = (
        bool(df['CROSS_KD'].iloc[-1] or df['CROSS_KD'].iloc[-2]) and
        bool(df['GIRO_MACD'].iloc[-1] or df['CROSS_MACD'].iloc[-1] or df['CROSS_MACD'].iloc[-2]) and
        rsi_v < 50 and
        bool(df['VOL_OK'].iloc[-1])
    )

    if not (sobreventa or soporte or rebote_bb or cruce):
        return None

    # Score técnico base (1-4)
    score = sum([sobreventa, soporte, rebote_bb, cruce])

    return {
        "sym": sym,
        "precio": precio,
        "precio_str": f"${precio:.2f}",
        "rsi": rsi_v, "rsi_str": f"{rsi_v:.1f}",
        "j": j_v, "j_str": f"{j_v:.1f}",
        "adx": adx_v, "adx_str": f"{adx_v:.1f}",
        "score": score,
        "sobreventa": sobreventa,
        "soporte":    soporte,
        "rebote_bb":  rebote_bb,
        "cruce":      cruce,
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
# ESCANEO AUTOMATICO — batch download + threading
# ======================================================================
prog = st.progress(0, text=f"Descargando {len(TICKERS)} tickers en batch...")

@st.cache_data(ttl=300, show_spinner=False)
def descargar_batch(tickers_tuple):
    return yf.download(
        list(tickers_tuple), period="2y", group_by="ticker",
        progress=False, auto_adjust=True, threads=True,
    )

df_batch = descargar_batch(tuple(TICKERS))
prog.progress(40, text="Calculando indicadores...")

# Fase 2: indicadores
resultados = []
for idx, sym in enumerate(TICKERS):
    if idx % 30 == 0:
        prog.progress(40 + int(idx/len(TICKERS)*30), text=f"Indicadores · {idx}/{len(TICKERS)}")
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
    item["graham"]="—"
    item["graham_up"]="—"
    item["bonus_fv"]=False
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

    # Graham Number (fair value defensivo)
    g_fv, g_txt, graham_up_raw = calc_graham(fund.get("eps_ttm"), fund.get("book_value"), item["precio"])
    item["graham"] = g_fv
    item["graham_up"] = g_txt

    # ── BONUS +1: Graham Y Target ambos >= +15% (doble confirmacion de ganga) ──
    if (graham_up_raw is not None and graham_up_raw >= 15 and
        target_up_raw is not None and target_up_raw >= 15):
        item["score"] = item["score"] + 1
        item["bonus_fv"] = True

    return item

with ThreadPoolExecutor(max_workers=12) as executor:
    todos = list(executor.map(fetch_fund, resultados))

prog.progress(100, text="¡Listo!")
prog.empty()

# Resumen
n_sob = sum(1 for x in todos if x["sobreventa"])
n_sop = sum(1 for x in todos if x["soporte"])
n_bb  = sum(1 for x in todos if x["rebote_bb"])
n_cr  = sum(1 for x in todos if x["cruce"])
n_top = sum(1 for x in todos if x["score"] >= 2)

st.markdown(f'<div style="text-align:center;color:var(--muted);font-size:12px;padding:8px 0 16px;letter-spacing:.05em;">✅ {len(TICKERS)} tickers · {len(todos)} candidatos · <span style="color:#00e5a0;font-weight:700">{n_top} TOP-PICKS</span> · 🟢 {n_sob} sobreventa · 🟡 {n_sop} soporte · 🔵 {n_bb} bollinger · 🟣 {n_cr} cruce</div>', unsafe_allow_html=True)

# ======================================================================
# TOP PICKS — score >= 2 (incluye bonus fundamental)
# ======================================================================
top_picks = sorted([x for x in todos if x["score"] >= 2], key=lambda x: (-x["score"], x["rsi"]))

if top_picks:
    st.markdown('<div class="sec sec-os">⭐ TOP PICKS — MEJOR SCORE (TÉCNICO + FUNDAMENTAL)</div>', unsafe_allow_html=True)
    st.markdown("""<div class="glosario">
    <b>Score</b> — gatillos técnicos + bonus valor (verde 4+, azul 3, morado 2) &nbsp;·&nbsp;
    <b>Gatillos</b> — 🟢SOB sobreventa · 🟡SOP soporte EMA50/200/325 · 🔵BB bollinger · 🟣CR cruce KDJ+MACD &nbsp;·&nbsp;
    <b>💎VALOR</b> — bonus +1: Graham FV Y Target 12M ambos ≥+15% (barata por ambas valoraciones) &nbsp;·&nbsp;
    <b>Graham FV</b> — fair value de Graham √(22.5×EPS×BookValue), valor máximo defensivo &nbsp;·&nbsp;
    <b>vs Graham</b> — % entre precio y Graham FV (🟢 barato bajo Graham) &nbsp;·&nbsp;
    <b>Target 12M</b> — precio objetivo a 12 meses (consenso analistas) &nbsp;·&nbsp;
    <b>Upside</b> — % entre precio y Target 12M: 🟢 ≥+15% · ⚪ 0/+15% · 🟡 -10/0% · 🔴 &lt;-10% &nbsp;·&nbsp;
    <b>P/E fwd</b> — P/E proyectado próximos 12M &nbsp;·&nbsp;
    <b>Consenso</b> — rating analistas (n)
    </div>""", unsafe_allow_html=True)
    rows = []
    for x in top_picks:
        gs = []
        if x["sobreventa"]: gs.append("🟢SOB")
        if x["soporte"]:    gs.append("🟡SOP")
        if x["rebote_bb"]:  gs.append("🔵BB")
        if x["cruce"]:      gs.append("🟣CR")
        if x.get("bonus_fv"): gs.append("💎VALOR")
        rows.append({
            "Ticker": x["sym"], "Score": x["score"], "Gatillos": " ".join(gs),
            "Precio": x["precio_str"],
            "Graham FV": x.get("graham","—"), "vs Graham": x.get("graham_up","—"),
            "Target 12M": x.get("target","—"), "Upside": x.get("upside","—"),
            "RSI": x["rsi_str"], "J(KDJ)": x["j_str"], "ADX": x["adx_str"],
            "P/E": x.get("pe_ttm","—"), "P/E fwd": x.get("pe_fwd","—"),
            "Consenso": x.get("consenso","—"),
        })
    df_top = pd.DataFrame(rows).reset_index(drop=True); df_top.index = range(1,len(df_top)+1)
    st.dataframe(df_top.style.map(csc,subset=["Score"]).map(cr,subset=["RSI"]).map(cj,subset=["J(KDJ)"]).map(cs,subset=["Upside","vs Graham","Consenso"]), use_container_width=True)

# ======================================================================
# 4 LISTAS INDIVIDUALES
# ======================================================================
def render_seccion(titulo, css, key, glosario):
    items = sorted([x for x in todos if x[key]], key=lambda x: x["rsi"])
    st.markdown(f'<div class="sec {css}">{titulo}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="glosario">{glosario}</div>', unsafe_allow_html=True)
    if not items:
        st.info("Sin candidatos en esta categoría hoy.")
        return
    rows = [{
        "Ticker": x["sym"], "Precio": x["precio_str"],
        "Graham FV": x.get("graham","—"), "vs Graham": x.get("graham_up","—"),
        "Target 12M": x.get("target","—"), "Upside": x.get("upside","—"),
        "RSI": x["rsi_str"], "J(KDJ)": x["j_str"], "ADX": x["adx_str"],
        "P/E": x.get("pe_ttm","—"), "P/E fwd": x.get("pe_fwd","—"),
        "Consenso": x.get("consenso","—"),
    } for x in items]
    df_ = pd.DataFrame(rows).reset_index(drop=True); df_.index = range(1,len(df_)+1)
    st.dataframe(df_.style.map(cr,subset=["RSI"]).map(cj,subset=["J(KDJ)"]).map(cs,subset=["Upside","vs Graham","Consenso"]), use_container_width=True)

GLOS_FUND = "<b>Graham FV</b>: √(22.5×EPS×BookValue) fair value defensivo &nbsp;·&nbsp; <b>vs Graham</b>: % vs Graham &nbsp;·&nbsp; <b>Target 12M</b>: objetivo analistas &nbsp;·&nbsp; <b>Upside</b>: % vs Target"

render_seccion(
    "🟢 SOBREVENTA FRESCA — RSI < 35", "sec-os", "sobreventa",
    "<b>Criterio</b>: RSI &lt;35 + KDJ girando + cierre sobre mínimo de ayer + volumen &nbsp;·&nbsp; " + GLOS_FUND
)
render_seccion(
    "🟡 TOCANDO SOPORTE EMA 50 / 200 / 325", "sec-mas", "soporte",
    "<b>Criterio</b>: precio toca EMA50, EMA200 o EMA325 + KDJ girando + volumen &nbsp;·&nbsp; " + GLOS_FUND
)
render_seccion(
    "🔵 REBOTE BOLLINGER INFERIOR", "sec-bb", "rebote_bb",
    "<b>Criterio</b>: tocó BB inferior ayer y cerró sobre ella + KDJ girando + volumen &nbsp;·&nbsp; " + GLOS_FUND
)
render_seccion(
    "🟣 CRUCE KDJ + MACD EN ZONA BAJA", "sec-cr", "cruce",
    "<b>Criterio</b>: K cruza D + MACD gira/cruza + RSI &lt;50 + volumen &nbsp;·&nbsp; " + GLOS_FUND
)

st.markdown('<p class="footer">Rebote Screener · Técnico + Fundamental · Solo fines educativos · No es asesoría financiera</p>', unsafe_allow_html=True)
