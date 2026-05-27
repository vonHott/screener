# ======================================================================
# SG6 SCREENER MÓVIL — VERSION LIMPIA
# Entradas frescas de HOY · CRH v3 gatillos · 3 bandas BC/HYB/VOL
# Sin ADD · Sin IS_LONG simulado · Ejecutar al cierre de mercado
# ======================================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import io
warnings.filterwarnings('ignore')

try:
    import pandas_ta as ta
    USE_PANDAS_TA = True
except ImportError:
    USE_PANDAS_TA = False

st.set_page_config(
    page_title="SG6 · Santo Grial",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@600;700;800&display=swap');
:root {
    --bg:#080c14; --surface:#0d1220; --border:#1a2235; --border2:#243048;
    --text:#e2e8f0; --muted:#4a5568; --accent:#00d4ff;
    --green:#00e5a0; --red:#ff4d6d; --orange:#ff8c42; --yellow:#ffd166;
}
html,body,[class*="css"]{font-family:'DM Mono',monospace;background:var(--bg)!important;color:var(--text)}
[data-testid="stSidebar"]{display:none!important}
[data-testid="collapsedControl"]{display:none!important}
#MainMenu,footer,header{display:none!important}
.block-container{padding:1rem 1.2rem 2rem!important;max-width:1400px!important}

.sg6-header{background:linear-gradient(135deg,var(--surface) 0%,#0f1928 100%);border:1px solid var(--border2);border-radius:12px;padding:20px 28px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between}
.sg6-header h1{font-family:'Syne',sans-serif;font-size:clamp(16px,3vw,22px);font-weight:800;color:var(--text);margin:0 0 2px 0}
.sg6-header h1 span{color:var(--accent)}
.sg6-header p{color:var(--muted);font-size:10px;margin:0;letter-spacing:.08em}
.sg6-badge{background:linear-gradient(135deg,#00d4ff22,#00d4ff11);border:1px solid #00d4ff44;color:var(--accent);font-size:10px;padding:4px 10px;border-radius:20px;white-space:nowrap}

.idx-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px}
@media(max-width:700px){.idx-grid{grid-template-columns:1fr 1fr}}
.idx-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 16px}
.idx-label{color:var(--muted);font-size:9px;letter-spacing:.12em;text-transform:uppercase;margin-bottom:4px}
.idx-price{color:var(--text);font-size:clamp(16px,2.5vw,20px);font-weight:500;margin-bottom:2px}
.up{color:var(--green);font-size:12px;font-weight:500}
.down{color:var(--red);font-size:12px;font-weight:500}

.ctx-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:16px}
@media(max-width:700px){.ctx-grid{grid-template-columns:1fr 1fr}}
.ctx-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 16px}
.ctx-label{color:var(--muted);font-size:9px;letter-spacing:.12em;text-transform:uppercase;margin-bottom:4px}
.ctx-val{color:var(--text);font-size:18px;font-weight:500;margin-bottom:2px}
.ctx-sub{font-size:11px;font-weight:500}
.ok{color:var(--green)}.warn{color:var(--yellow)}.bad{color:var(--red)}

.config-panel{background:var(--surface);border:1px solid var(--border2);border-radius:10px;padding:16px;margin-bottom:16px}
.config-title{font-family:'Syne',sans-serif;font-size:11px;font-weight:700;color:var(--muted);letter-spacing:.15em;text-transform:uppercase;margin-bottom:12px}

[data-testid="stButton"]>button{background:var(--surface)!important;border:1px solid var(--border2)!important;border-radius:10px!important;color:var(--text)!important;font-family:'DM Mono',monospace!important;font-size:12px!important;font-weight:500!important;transition:border-color .15s,background .15s!important;padding:10px 16px!important}
[data-testid="stButton"]>button:hover{border-color:var(--accent)!important;background:#0d1928!important;color:var(--accent)!important}
[data-testid="stButton"]>button[kind="primary"]{background:linear-gradient(135deg,#003d5c,#001e3c)!important;border-color:var(--accent)!important;color:var(--accent)!important;font-weight:700!important;font-size:13px!important}

[data-testid="stDataFrame"]{border:1px solid var(--border)!important;border-radius:10px!important;overflow:hidden!important;font-family:'DM Mono',monospace!important;font-size:11px!important}

.sec-header{display:flex;align-items:center;gap:10px;margin:16px 0 12px 0;padding-bottom:8px;border-bottom:1px solid var(--border2)}
.sec-header h4{font-family:'Syne',sans-serif;font-size:15px;font-weight:700;color:var(--text);margin:0}
.sec-line{flex:1;height:1px;background:linear-gradient(to right,#00d4ff44,transparent)}

.glosario{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 14px;margin-bottom:12px;font-size:11px;color:var(--muted);line-height:1.9}
.glosario b{color:#718096}
.footer{color:var(--border2);font-size:10px;text-align:center;padding:20px 0 8px;letter-spacing:.05em}
[data-testid="stSlider"] label,[data-testid="stSelectbox"] label{font-size:11px!important;color:var(--muted)!important}
</style>
""", unsafe_allow_html=True)

# ======================================================================
# WATCHLIST
# ======================================================================
TICKERS = [
    "CHWY","ALT","PLTR","RBRK","MORN","CBRS","ISRG","MDT","DG","EPAM",
    "BRK-B","NCLH","CLS","GILD","FSLR","RTX","PSX","NBIS","ZTS","FICO",
    "BAC","GS","NOW","RMBS","MRVL","COF","BHP","ETH-USD","SOL-USD","BTI",
    "SAP","FDX","TME","INTU","SONY","COHR","GDDY","PM","TSM","CRDO","NNE",
    "NRG","BLK","ENPH","LMT","DPZ","IONQ","VRT","VRTX","MSFT","AAPL",
    "MMM","HD","GOOGL","EBAY","SOFI","MPWR","LULU","CPRT","ETN","TJX",
    "ADP","NEE","DHR","T","VZ","QQQ","MU","TXN","OKTA","ZS","AFRM","GME",
    "BABA","RIOT","ARM","XLP","XLK","XLI","XLV","XLE","IWM","SPY","UBER",
    "PYPL","INTC","LRCX","AMAT","REGN","SHOP","HOOD","NET","CRWD","DDOG",
    "SNOW","MDB","MARA","COIN","AVGO","CSCO","ACN","LIN","TMO","LLY","ABBV",
    "ABNB","MRNA","AMT","ASTS","PANW","APH","SMCI","DELL","ANET","STX",
    "WDC","RCL","BKNG","TMUS","DE","CRM","ADBE","TGT","COST","CVX","XOM",
    "GE","ABT","AMZN","BTC-USD","SOUN","IBM","SMH","URA","CEG","NVO","MRK",
    "SPOT","EQIX","BA","FCX","AEM","MSTR","PEP","KO","WMT","PFE","DIS",
    "JNJ","MCD","JPM","MA","CAT","SBUX","PG","UNH","NVDA","NFLX","MELI",
    "NKE","META","ORCL","ASML","TSLA","AMD","QQQM","VOO","ACHR","LINK-USD","AVAX-USD",
    "CL=F","NG=F","SI=F","HG=F","GC=F","NQ=F",
    "EURUSD=X","USDCHF=X","GBPUSD=X","USDJPY=X","USDCOP=X","USDCLP=X","USDBRL=X","DX-Y.NYB",
    "ZIM","DLTR","BBY","WBD","UNG","GT","WYNN","MGM","SNAP","CVNA","ROKU",
    "HUM","ELV","UHS","ILMN","SWK","FNV","SBSW","GOLD","SQM","ALB","GSK","AZN",
    "BAYN.DE","ADS.DE","ROG.SW","FRE.DE","9988.HK",
]

# ======================================================================
# FUNCIONES
# ======================================================================
def calcular_rsi(close, periodo=14):
    if USE_PANDAS_TA:
        try: return ta.rsi(close, length=periodo)
        except: pass
    c = close.copy().reset_index(drop=True)
    n = len(c); delta = c.diff()
    gain = delta.clip(lower=0).fillna(0)
    loss = (-delta).clip(lower=0).fillna(0)
    ag = np.zeros(n); al = np.zeros(n)
    if n > periodo:
        ag[periodo] = gain.iloc[1:periodo+1].mean()
        al[periodo] = loss.iloc[1:periodo+1].mean()
        for i in range(periodo+1, n):
            ag[i] = (ag[i-1]*(periodo-1)+gain.iloc[i])/periodo
            al[i] = (al[i-1]*(periodo-1)+loss.iloc[i])/periodo
    rs = ag/np.where(al==0,1e-8,al)
    rsi = 100-(100/(1+rs)); rsi[:periodo] = np.nan
    return pd.Series(rsi, index=close.index)

@st.cache_data(ttl=300, show_spinner=False)
def get_market_data():
    indices = {"S&P 500":"^GSPC","Nasdaq 100":"^NDX","Dow Jones":"^DJI","Russell 2000":"^RUT"}
    result = {}
    for name, sym in indices.items():
        try:
            h = yf.Ticker(sym).history(period="5d", interval="1d")
            if len(h)>=2:
                prev=float(h['Close'].iloc[-2]); curr=float(h['Close'].iloc[-1])
                result[name] = {"price":curr,"pct":(curr-prev)/prev*100}
        except: result[name] = {"price":0,"pct":0}
    vix = 0
    try:
        h = yf.Ticker("^VIX").history(period="5d",interval="1d")
        if not h.empty: vix = float(h['Close'].iloc[-1])
    except: pass
    btc_pct = 0; btc_price = 0
    try:
        h = yf.Ticker("BTC-USD").history(period="5d",interval="1d")
        if len(h)>=2:
            btc_price = float(h['Close'].iloc[-1])
            btc_pct   = (btc_price - float(h['Close'].iloc[-2])) / float(h['Close'].iloc[-2]) * 100
    except: pass
    return result, vix, btc_pct, btc_price

def analizar_ticker(sym, periodo):
    try:
        df = yf.download(sym, period=periodo, progress=False, auto_adjust=True)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    except: return None
    df = df.dropna(subset=['Close','Volume'])
    df = df[df['Volume']>0].copy()
    if len(df) < 250: return None

    # ── Bandas 3 niveles CRH v3 ──
    df['BETA'] = df['Close'].pct_change().mul(100).rolling(60).std(ddof=0).rolling(20).mean()
    df['BANDA'] = np.where(df['BETA']<1.0,"BC", np.where(df['BETA']<1.8,"HYB","VOL"))

    # ── Medias ──
    df['MA20']  = df['Close'].ewm(span=20, adjust=False).mean()
    df['MA50']  = df['Close'].ewm(span=50, adjust=False).mean()
    df['MA200'] = df['Close'].ewm(span=200,adjust=False).mean()
    df['MA20_UP']   = df['MA20'] > df['MA20'].shift(1)
    df['MA50_SUBE'] = df['MA50'] > df['MA50'].shift(3)

    # ── ATR ──
    hl  = df['High']-df['Low']
    hpc = (df['High']-df['Close'].shift(1)).abs()
    lpc = (df['Low'] -df['Close'].shift(1)).abs()
    df['ATR'] = pd.concat([hl,hpc,lpc],axis=1).max(axis=1).rolling(14).mean()

    # ── ADX ──
    hd = df['High']-df['High'].shift(1)
    ld = df['Low'].shift(1)-df['Low']
    dmp = np.where((hd>0)&(hd>ld), hd, 0)
    dmm = np.where((ld>0)&(ld>hd), ld, 0)
    t14 = pd.Series(pd.concat([hl,hpc,lpc],axis=1).max(axis=1)).rolling(14).sum().replace(0,1e-8)
    pdi = pd.Series(dmp, index=df.index).rolling(14).sum()*100/t14
    mdi = pd.Series(dmm, index=df.index).rolling(14).sum()*100/t14
    df['ADX'] = (abs(pdi-mdi)/(pdi+mdi).replace(0,1e-8)*100).rolling(9).mean()
    df['PDI'] = pdi; df['MDI'] = mdi
    df['ADX_REQ'] = np.where(df['Close']<df['MA200'], 28, 20)

    # ── KDJ ──
    lm = df['Low'].rolling(9).min()
    hm = df['High'].rolling(9).max()
    rsv = (df['Close']-lm)/(hm-lm).replace(0,1e-8)*100
    df['K'] = rsv.ewm(alpha=1/3, adjust=False).mean()
    df['D'] = df['K'].ewm(alpha=1/3, adjust=False).mean()
    df['J'] = 3*df['K']-2*df['D']
    df['GIRO_J']  = df['J'] > df['J'].shift(1)
    df['CROSS_KD']= (df['K']>df['D'])&(df['K'].shift(1)<=df['D'].shift(1))

    # ── MACD ──
    dif = df['Close'].ewm(span=12,adjust=False).mean()-df['Close'].ewm(span=26,adjust=False).mean()
    dea = dif.ewm(span=9,adjust=False).mean()
    hist= dif-dea
    df['DIF']  = dif; df['DEA'] = dea; df['HIST'] = hist
    df['GIRO_MACD']    = (hist>hist.shift(1))&(hist.shift(1)<=hist.shift(2))
    df['MACD_GIRO_NEG']= (hist<0)&(hist<hist.shift(1))&(hist.shift(1)<hist.shift(2))

    # ── RSI ──
    df['RSI'] = calcular_rsi(df['Close'], 14)

    # ── Bollinger ──
    df['BB_MID'] = df['Close'].rolling(20).mean()
    df['BB_STD'] = df['Close'].rolling(20).std(ddof=0)
    df['BB_DN']  = df['BB_MID'] - 2*df['BB_STD']

    # ── Volumen ──
    df['VOL_MA'] = df['Volume'].rolling(20).mean()

    # ── Filtros MA (CRH v3) ──
    df['MA50_ALC']  = df['MA50'] > df['MA50'].shift(5)
    df['VENIA_MA50']= df['Close'].shift(1).gt(df['MA50']).rolling(3).sum() >= 2
    df['MA200_PLANA']= df['MA200'] >= df['MA200'].shift(3)

    # ── Gatillos CRH v3 — identicos al script Moomoo ──
    # ── GATILLOS DE REBOTE DESDE ABAJO (screener de entrada nueva) ──
    # Solo gatillos que implican inicio desde sobreventa o soporte:
    # S_BOLL  : rebote desde banda Bollinger inferior
    # S_SUELO : RSI<35 + J<25 — sobreventa extrema
    # S_EARLY : RSI<40 + cruce KD — anticipado en zona baja
    # S_R200  : rebote desde MA200 con soporte real
    # S_BSOFT : rebote suave desde BB inferior sin MACD negativo
    # S_PULL  : pullback a MA50 en tendencia alcista
    # Excluidos: S_IMPU, S_CONT, S_MACD — son continuacion, no inicio

    cx_macd = (dif>dea)&(dif.shift(1)<=dea.shift(1))

    df['S_PULL']  = (df['Low']<df['MA50']*1.015)&(df['Close']>df['MA50']*0.985)&df['GIRO_J']&(df['Volume']>df['VOL_MA']*1.02)&df['MA50_ALC']&df['VENIA_MA50']
    df['S_BOLL']  = (df['Low'].shift(1)<=df['BB_DN'])&(df['Close']>df['BB_DN'])&df['GIRO_J']&df['GIRO_MACD']&(df['Volume']>df['VOL_MA']*0.88)
    df['S_SUELO'] = (df['RSI']<35)&(df['J']<25)&(df['Close']>df['Low'].shift(1))&df['GIRO_MACD']&(df['Volume']>df['VOL_MA']*0.88)
    df['S_EARLY'] = (df['RSI']<40)&(df['J']<30)&df['CROSS_KD']&df['MA20_UP']&(df['Volume']>df['VOL_MA']*0.88)
    df['S_R200']  = (df['Low']<=df['MA200']*1.01)&(df['Close']>df['MA200'])&(df['Close']>df['Low'].shift(1))&df['GIRO_J']&df['MA20_UP']&df['MA200_PLANA']&(df['Volume']>df['VOL_MA']*1.02)
    df['S_BSOFT'] = (df['Low'].shift(1)<=df['BB_DN'])&(df['Close']>df['BB_DN'])&(df['Close']>df['Low'].shift(1))&df['GIRO_J']&(df['Volume']>df['VOL_MA']*0.88)&~df['MACD_GIRO_NEG']

    # ── VMC CIPHER B — WaveTrend Oscillator (LazyBear / VuManChu, MPL 2.0) ──
    # Parametros originales del indicador
    vmc_n1 = 10   # channel length
    vmc_n2 = 21   # average length
    ob1    = 60   # overbought 1
    os1    = -60  # oversold 1
    ob2    = 53
    os2    = -53

    # HLC3
    hlc3 = (df['High'] + df['Low'] + df['Close']) / 3

    # EMA del HLC3
    esa  = hlc3.ewm(span=vmc_n1, adjust=False).mean()

    # Diferencia absoluta suavizada
    de   = (hlc3 - esa).abs().ewm(span=vmc_n1, adjust=False).mean()

    # Commodity Channel Index adaptado
    ci   = (hlc3 - esa) / (0.015 * de.replace(0, 1e-8))

    # WaveTrend 1 y 2
    wt1  = ci.ewm(span=vmc_n2, adjust=False).mean()
    wt2  = wt1.rolling(4).mean()
    df['VMC_WT1'] = wt1
    df['VMC_WT2'] = wt2

    # Money Flow Index RSI modificado (componente MFI del VMC)
    mfi_period = 60
    mfi_mult   = 150
    mfi_raw    = ((df['Close'] - df['Open']) / (df['High'] - df['Low']).replace(0, 1e-8)) * mfi_mult
    df['VMC_MFI'] = mfi_raw.rolling(mfi_period).mean()

    # SEÑAL VMC — Circulo verde (buy dot):
    # WT2 cruza hacia arriba WT1 desde zona de sobreventa
    wt_cross_up = (wt2 > wt1) & (wt2.shift(1) <= wt1.shift(1))
    wt_oversold  = wt2.shift(1) < os2  # venia de sobreventa
    mfi_positive = df['VMC_MFI'] > 0   # money flow positivo
    df['VMC_BUY'] = wt_cross_up & wt_oversold & mfi_positive

    # Divergencia alcista VMC:
    # Precio hace minimo mas bajo pero WT2 hace minimo mas alto
    price_lower_low = df['Close'] < df['Close'].rolling(5).min().shift(1)
    wt2_higher_low  = wt2 > wt2.rolling(5).min().shift(1)
    df['VMC_DIV']   = price_lower_low & wt2_higher_low & (wt2 < os2)

    # B_RAW: cualquier gatillo de rebote, sin distincion de banda
    # (los rebotes aplican igual para BC, HYB y VOL)
    df['B_RAW'] = df['S_PULL']|df['S_BOLL']|df['S_SUELO']|df['S_EARLY']|df['S_R200']|df['S_BSOFT']|df['VMC_BUY']|df['VMC_DIV']

    # B_SIGNAL: primera barra de la racha — identico a Moomoo
    df['B_SIGNAL'] = df['B_RAW'] & ~df['B_RAW'].shift(1).fillna(False)

    # Solo entradas de HOY
    if not df['B_SIGNAL'].iloc[-1]:
        return None

    # Cuantos dias lleva B_RAW activo (1 = entrada limpia y fresca)
    dias_raw = 0
    for k in range(len(df)-1, max(len(df)-30,-1), -1):
        if df['B_RAW'].iloc[k]:
            dias_raw += 1
        else:
            break

    # Datos de salida
    precio   = float(df['Close'].iloc[-1])
    banda    = str(df['BANDA'].iloc[-1])
    atr      = float(df['ATR'].iloc[-1])
    rsi_v    = float(df['RSI'].iloc[-1]) if not pd.isna(df['RSI'].iloc[-1]) else 0
    adx_v    = float(df['ADX'].iloc[-1]) if not pd.isna(df['ADX'].iloc[-1]) else 0

    tp_mult  = 1.6 if banda=="BC" else (2.0 if banda=="HYB" else 2.5)
    sl_mult  = 1.3 if banda=="BC" else (1.5 if banda=="HYB" else 1.8)
    tp1      = precio + atr * tp_mult
    sl       = max(precio - atr*sl_mult, precio*0.97)

    # Gatillos disparados hoy
    gmap = {"PULL":"S_PULL","BOLL":"S_BOLL","SUELO":"S_SUELO",
            "EARLY":"S_EARLY","R200":"S_R200","BSOFT":"S_BSOFT",
            "VMC_BUY":"VMC_BUY","VMC_DIV":"VMC_DIV"}
    gatillos = [n for n,c in gmap.items() if bool(df[c].iloc[-1])]

    # Radar OJO/BTD
    df['OJO'] = (df['RSI']<35)&(df['J']<28)&(df['Close']<=df['BB_DN']*1.01)
    df['CJ']  = (df['J']>10)&(df['J'].shift(1).fillna(100)<=12)
    df['BTD'] = df['OJO'].shift(1).fillna(False)&df['CJ']&df['GIRO_MACD']

    return {
        "Ticker": sym,
        "Banda":  banda,
        "Precio": f"${precio:.2f}",
        "precio_raw": precio,
        "RSI":    f"{rsi_v:.1f}",
        "rsi_raw": rsi_v,
        "ADX":    f"{adx_v:.1f}",
        "TP1":    f"${tp1:.2f}",
        "SL":     f"${sl:.2f}",
        "Días B_RAW": dias_raw,
        "Gatillos": ",".join(gatillos) if gatillos else "—",
        "OJO": bool(df['OJO'].iloc[-2:].any()),
        "BTD": bool(df['BTD'].iloc[-2:].any()),
    }

# ======================================================================
# SESSION STATE
# ======================================================================
for k,v in [("listo",False),("compras",[]),("rsi",[]),("radar",[]),("seccion",None),("ru",33)]:
    if k not in st.session_state: st.session_state[k] = v

# ======================================================================
# HELPERS
# ======================================================================
def cb(v):
    if v=="BC":  return "background-color:#002d1a;color:#00e5a0;font-weight:600"
    if v=="HYB": return "background-color:#001e3c;color:#00d4ff;font-weight:600"
    if v=="VOL": return "background-color:#2d1200;color:#ff8c42;font-weight:600"
    return ""
def cr(v):
    try:
        r=float(str(v))
        if r<33: return "color:#ff4d6d;font-weight:600"
        if r>65: return "color:#00e5a0;font-weight:600"
    except: pass
    return "color:#4a5568"

G1 = """<div class="glosario"><b>Banda</b> — BC baja vol · HYB media vol · VOL alta vol &nbsp;·&nbsp; <b>Precio</b> — cierre de hoy (vela de entrada) &nbsp;·&nbsp; <b>RSI</b> — rojo &lt;33 · verde &gt;65 &nbsp;·&nbsp; <b>TP1</b> — objetivo ATR×mult desde entrada &nbsp;·&nbsp; <b>SL</b> — stop loss ATR×mult con tope 3% &nbsp;·&nbsp; <b>Gatillos</b> — razones que dispararon la señal hoy</div>"""
G2 = """<div class="glosario"><b>RSI</b> — Wilder por debajo del umbral configurado &nbsp;·&nbsp; <b>ADX</b> — fuerza de tendencia</div>"""
G3 = """<div class="glosario"><b>OJO 🟡</b> — RSI &lt;35 + J &lt;28 + precio cerca BB inferior &nbsp;·&nbsp; <b>BTD 🟢</b> — ayer OJO + hoy J cruza + MACD gira</div>"""

# ======================================================================
# HEADER
# ======================================================================
st.markdown("""
<div class="sg6-header">
  <div>
    <h1>📊 SG6 · <span>Santo Grial</span></h1>
    <p>CRH V3 · BC/HYB/VOL · 9 GATILLOS · RSI WILDER · EJECUTAR AL CIERRE</p>
  </div>
  <div class="sg6-badge">v3.0 CLEAN</div>
</div>
""", unsafe_allow_html=True)

# ======================================================================
# LANDING
# ======================================================================
if not st.session_state.listo:
    with st.spinner("Cargando mercado..."):
        indices, vix, btc_pct, btc_price = get_market_data()

    # Índices
    st.markdown('<div class="idx-grid">', unsafe_allow_html=True)
    for name, data in indices.items():
        p=data["price"]; pct=data["pct"]
        cls="up" if pct>=0 else "down"
        sig="+" if pct>=0 else ""
        st.markdown(f'<div class="idx-card"><div class="idx-label">{name}</div><div class="idx-price">{p:,.0f}</div><div class="{cls}">{sig}{pct:.2f}%</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # VIX + BTC + Contexto
    sp_pct = indices.get("S&P 500",{}).get("pct",0)
    if vix<18 and sp_pct>0:   ctx_cls,ctx_txt = "ok","✅ Condiciones favorables"
    elif vix>25 or sp_pct<-1: ctx_cls,ctx_txt = "bad","⚠️ Mercado defensivo"
    else:                      ctx_cls,ctx_txt = "warn","⚪ Contexto mixto"
    vcls = "ok" if vix<18 else ("warn" if vix<25 else "bad")
    bcls = "up" if btc_pct>=0 else "down"
    bsig = "+" if btc_pct>=0 else ""
    bp   = f"${btc_price:,.0f}" if btc_price>0 else "—"

    st.markdown(f"""
    <div class="ctx-grid">
      <div class="ctx-card">
        <div class="ctx-label">VIX — Volatilidad</div>
        <div class="ctx-val">{vix:.1f}</div>
        <div class="ctx-sub {vcls}">{"✅ Tranquilo" if vix<18 else ("⚠️ Moderado" if vix<25 else "🔴 Alto")}</div>
      </div>
      <div class="ctx-card">
        <div class="ctx-label">BTC — Termómetro</div>
        <div class="ctx-val {bcls}">{bp}</div>
        <div class="ctx-sub {bcls}">{bsig}{btc_pct:.2f}% &nbsp; {"🟢 Riesgo ON" if btc_pct>=0 else "🔴 Riesgo OFF"}</div>
      </div>
      <div class="ctx-card">
        <div class="ctx-label">Contexto</div>
        <div class="ctx-val" style="font-size:13px;margin-top:6px;">&nbsp;</div>
        <div class="ctx-sub {ctx_cls}" style="font-size:13px;">{ctx_txt}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Config
    st.markdown('<div class="config-panel"><div class="config-title">⚙️ Configuración</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1: periodo    = st.selectbox("Período histórico", ["2y","1y","6mo"], index=0)
    with c2: rsi_umbral = st.slider("RSI sobreventa", 25, 45, 33)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("▶  EJECUTAR ESCÁNER", use_container_width=True, type="primary"):
        st.session_state.listo    = False
        st.session_state.compras  = []
        st.session_state.rsi      = []
        st.session_state.radar    = []
        st.session_state.seccion  = None
        st.session_state.ru       = rsi_umbral

        lista_c, lista_r, lista_rd = [], [], []
        prog = st.progress(0, text="Iniciando...")

        for idx, ticker in enumerate(TICKERS):
            prog.progress(int((idx+1)/len(TICKERS)*100), text=f"{ticker}  ({idx+1}/{len(TICKERS)})")
            datos = analizar_ticker(ticker, periodo)

            # Compras: solo las que tienen B_SIGNAL hoy (analizar_ticker ya filtra)
            if datos:
                lista_c.append({
                    "Ticker":   datos["Ticker"],
                    "Banda":    datos["Banda"],
                    "Precio":   datos["Precio"],
                    "Días":     datos["Días B_RAW"],
                    "RSI":      datos["RSI"],
                    "ADX":      datos["ADX"],
                    "TP1":      datos["TP1"],
                    "SL":       datos["SL"],
                    "Gatillos": datos["Gatillos"],
                })

            # RSI — necesita descargar aunque no haya señal hoy
            # Solo añadir si el ticker ya fue descargado con señal
            # Para RSI y Radar usamos los datos de compras + descarga separada
            if datos and datos["rsi_raw"] < rsi_umbral:
                lista_r.append({
                    "Ticker": datos["Ticker"],
                    "Banda":  datos["Banda"],
                    "Precio": datos["Precio"],
                    "RSI":    datos["RSI"],
                    "ADX":    datos["ADX"],
                })
            if datos and datos["BTD"]:
                lista_rd.append({"Ticker":datos["Ticker"],"Señal":"🟢 BTD","Banda":datos["Banda"],"Precio":datos["Precio"],"RSI":datos["RSI"]})
            elif datos and datos["OJO"]:
                lista_rd.append({"Ticker":datos["Ticker"],"Señal":"🟡 OJO","Banda":datos["Banda"],"Precio":datos["Precio"],"RSI":datos["RSI"]})

        prog.empty()
        st.session_state.compras = lista_c
        st.session_state.rsi     = lista_r
        st.session_state.radar   = lista_rd
        st.session_state.listo   = True
        st.rerun()

    st.markdown('<p class="footer">SG6 · CRH v3 · Solo fines educativos · No es asesoría financiera</p>', unsafe_allow_html=True)
    st.stop()

# ======================================================================
# RESULTADOS
# ======================================================================
lc=st.session_state.compras; lr=st.session_state.rsi; lrd=st.session_state.radar; ru=st.session_state.ru

st.success(f"✅ Escáner completado — {len(TICKERS)} tickers · {len(lc)} señales hoy")

c1,c2,c3,c4 = st.columns([1,1,1,1])
with c1:
    if st.button(f"🚀 Entradas hoy\n\n{len(lc)}", use_container_width=True):
        st.session_state.seccion = None if st.session_state.seccion=="c" else "c"
with c2:
    if st.button(f"📉 RSI < {ru}\n\n{len(lr)}", use_container_width=True):
        st.session_state.seccion = None if st.session_state.seccion=="r" else "r"
with c3:
    if st.button(f"🎯 OJO / BTD\n\n{len(lrd)}", use_container_width=True):
        st.session_state.seccion = None if st.session_state.seccion=="rd" else "rd"
with c4:
    if st.button("← Nuevo escáner", use_container_width=True):
        st.session_state.listo=False; st.session_state.seccion=None; st.rerun()

st.markdown("---")

sec = st.session_state.seccion
if sec=="c":
    st.markdown('<div class="sec-header"><h4>🚀 Entradas frescas — señal disparada hoy</h4><div class="sec-line"></div></div>', unsafe_allow_html=True)
    st.markdown(G1, unsafe_allow_html=True)
    if lc:
        df1 = pd.DataFrame(lc).reset_index(drop=True); df1.index = range(1,len(df1)+1)
        st.dataframe(df1.style.map(cb,subset=["Banda"]).map(cr,subset=["RSI"]), use_container_width=True)
        st.download_button("⬇️ CSV", df1.to_csv(index=False).encode(), "entradas_sg6.csv", "text/csv")
    else:
        st.info("Sin señales nuevas hoy. Ejecuta al cierre del mercado.")
elif sec=="r":
    st.markdown('<div class="sec-header"><h4>📉 Sobreventa RSI</h4><div class="sec-line"></div></div>', unsafe_allow_html=True)
    st.markdown(G2, unsafe_allow_html=True)
    if lr:
        df2 = pd.DataFrame(lr).sort_values("RSI").reset_index(drop=True); df2.index = range(1,len(df2)+1)
        st.dataframe(df2.style.map(cb,subset=["Banda"]).map(cr,subset=["RSI"]), use_container_width=True)
    else:
        st.info("Ningún activo en sobreventa extrema.")
elif sec=="rd":
    st.markdown('<div class="sec-header"><h4>🎯 Radar OJO / BTD</h4><div class="sec-line"></div></div>', unsafe_allow_html=True)
    st.markdown(G3, unsafe_allow_html=True)
    if lrd:
        df3 = pd.DataFrame(lrd).reset_index(drop=True); df3.index = range(1,len(df3)+1)
        st.dataframe(df3.style.map(cb,subset=["Banda"]).map(cr,subset=["RSI"]), use_container_width=True)
    else:
        st.info("Sin alertas de suelo.")
else:
    st.markdown('<p style="color:#1a2235;font-size:13px;text-align:center;padding:32px 0;letter-spacing:.05em;">SELECCIONA UN CONTADOR PARA VER LOS RESULTADOS</p>', unsafe_allow_html=True)

st.markdown('<p class="footer">SG6 · CRH v3 · RSI Wilder · Solo fines educativos · No es asesoría financiera</p>', unsafe_allow_html=True)
