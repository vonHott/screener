# ======================================================================
# SG6 SCREENER — APP UNIFICADA MOBILE + DESKTOP V2
# Detecta viewport y adapta layout automaticamente
# Santo Grial · Sistema KW-DNA
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
    --bg:       #080c14;
    --surface:  #0d1220;
    --border:   #1a2235;
    --border2:  #243048;
    --text:     #e2e8f0;
    --muted:    #4a5568;
    --accent:   #00d4ff;
    --green:    #00e5a0;
    --red:      #ff4d6d;
    --orange:   #ff8c42;
    --yellow:   #ffd166;
    --bc-bg:    #002d1a;
    --bc-fg:    #00e5a0;
    --hyb-bg:   #001e3c;
    --hyb-fg:   #00d4ff;
    --vol-bg:   #2d1200;
    --vol-fg:   #ff8c42;
}

html, body, [class*="css"] {
    font-family: 'DM Mono', monospace;
    background: var(--bg) !important;
    color: var(--text);
}

/* Ocultar chrome de Streamlit */
[data-testid="stSidebar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
#MainMenu, footer, header        { display: none !important; }
.block-container { padding: 1rem 1.2rem 2rem !important; max-width: 1400px !important; }

/* ── HEADER ── */
.sg6-header {
    background: linear-gradient(135deg, var(--surface) 0%, #0f1928 100%);
    border: 1px solid var(--border2);
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
}
.sg6-header-left h1 {
    font-family: 'Syne', sans-serif;
    font-size: clamp(16px, 3vw, 22px);
    font-weight: 800;
    color: var(--text);
    margin: 0 0 2px 0;
    letter-spacing: -0.5px;
}
.sg6-header-left h1 span { color: var(--accent); }
.sg6-header-left p { color: var(--muted); font-size: 10px; margin: 0; letter-spacing: .08em; }
.sg6-badge {
    background: linear-gradient(135deg, var(--accent)22, var(--accent)11);
    border: 1px solid var(--accent)44;
    color: var(--accent);
    font-size: 10px;
    font-weight: 500;
    padding: 4px 10px;
    border-radius: 20px;
    white-space: nowrap;
}

/* ── INDEX CARDS ── */
.idx-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 12px; }
@media (max-width: 700px) { .idx-grid { grid-template-columns: 1fr 1fr; } }
.idx-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 16px;
    transition: border-color .2s;
}
.idx-card:hover { border-color: var(--border2); }
.idx-label { color: var(--muted); font-size: 9px; letter-spacing: .12em; text-transform: uppercase; margin-bottom: 4px; }
.idx-price { color: var(--text); font-size: clamp(16px, 2.5vw, 20px); font-weight: 500; margin-bottom: 2px; }
.up   { color: var(--green); font-size: 12px; font-weight: 500; }
.down { color: var(--red);   font-size: 12px; font-weight: 500; }

/* ── CONTEXT CARDS ── */
.ctx-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 16px; }
@media (max-width: 700px) { .ctx-grid { grid-template-columns: 1fr 1fr; } }
.ctx-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 16px;
}
.ctx-label { color: var(--muted); font-size: 9px; letter-spacing: .12em; text-transform: uppercase; margin-bottom: 4px; }
.ctx-val   { color: var(--text); font-size: 18px; font-weight: 500; margin-bottom: 2px; }
.ctx-sub   { font-size: 11px; font-weight: 500; }
.ok   { color: var(--green); }
.warn { color: var(--yellow); }
.bad  { color: var(--red); }

/* ── NEWS + HOT ── */
.panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 12px;
}
.panel-title { font-family: 'Syne', sans-serif; font-size: 12px; font-weight: 700; color: var(--muted); letter-spacing: .12em; text-transform: uppercase; margin-bottom: 10px; }
.news-row { border-bottom: 1px solid var(--border); padding: 8px 0; font-size: 12px; }
.news-row a { color: var(--accent); text-decoration: none; line-height: 1.4; }
.news-src  { color: var(--muted); font-size: 10px; margin-top: 2px; }
.hot-row   { display: flex; justify-content: space-between; align-items: center; padding: 7px 0; border-bottom: 1px solid var(--border); font-size: 12px; }
.hot-ticker { color: var(--text); font-weight: 500; min-width: 55px; }
.hot-price  { color: var(--muted); }
.hot-vol    { color: var(--muted); font-size: 10px; }

/* ── CONFIG ── */
.config-panel {
    background: var(--surface);
    border: 1px solid var(--border2);
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 16px;
}
.config-title { font-family: 'Syne', sans-serif; font-size: 11px; font-weight: 700; color: var(--muted); letter-spacing: .15em; text-transform: uppercase; margin-bottom: 12px; }

/* ── BOTONES ── */
[data-testid="stButton"] > button {
    background: var(--surface) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    transition: border-color .15s, background .15s !important;
    padding: 10px 16px !important;
}
[data-testid="stButton"] > button:hover {
    border-color: var(--accent) !important;
    background: #0d1928 !important;
    color: var(--accent) !important;
}
[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #003d5c, #001e3c) !important;
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    font-weight: 700 !important;
    font-size: 13px !important;
}

/* ── RESULTADO BOTONES CONTADORES ── */
.counter-btn { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.counter-num { font-family: 'Syne', sans-serif; font-size: 28px; font-weight: 800; color: var(--text); }
.counter-lbl { font-size: 10px; color: var(--muted); letter-spacing: .1em; text-transform: uppercase; }

/* ── TABLA ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 11px !important;
}

/* ── SECCION HEADER ── */
.sec-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 16px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border2);
}
.sec-header h4 { font-family: 'Syne', sans-serif; font-size: 15px; font-weight: 700; color: var(--text); margin: 0; }
.sec-line { flex: 1; height: 1px; background: linear-gradient(to right, var(--accent)44, transparent); }

/* ── GLOSARIO ── */
.glosario { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; font-size: 11px; color: var(--muted); line-height: 1.9; }
.glosario b { color: #718096; }

/* ── FOOTER ── */
.footer { color: var(--border2); font-size: 10px; text-align: center; padding: 20px 0 8px; letter-spacing: .05em; }

/* ── STREAMLIT OVERRIDES ── */
[data-testid="stSlider"] label, [data-testid="stSelectbox"] label { font-size: 11px !important; color: var(--muted) !important; }
[data-testid="stMetric"] { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 10px 14px; }
</style>
""", unsafe_allow_html=True)

# ======================================================================
# WATCHLIST
# ======================================================================
TICKERS_DEFAULT = [
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
def calcular_rsi(close_series, periodo=14):
    if USE_PANDAS_TA:
        try: return ta.rsi(close_series, length=periodo)
        except Exception: pass
    close = close_series.copy().reset_index(drop=True)
    n = len(close)
    delta = close.diff()
    gain = delta.clip(lower=0).fillna(0)
    loss = (-delta).clip(lower=0).fillna(0)
    avg_gain = np.zeros(n); avg_loss = np.zeros(n)
    if n > periodo:
        avg_gain[periodo] = gain.iloc[1:periodo+1].mean()
        avg_loss[periodo] = loss.iloc[1:periodo+1].mean()
        for i in range(periodo+1, n):
            avg_gain[i] = (avg_gain[i-1]*(periodo-1)+gain.iloc[i])/periodo
            avg_loss[i] = (avg_loss[i-1]*(periodo-1)+loss.iloc[i])/periodo
    rs = avg_gain/np.where(avg_loss==0,1e-8,avg_loss)
    rsi = 100-(100/(1+rs)); rsi[:periodo] = np.nan
    return pd.Series(rsi, index=close_series.index)

@st.cache_data(ttl=600, show_spinner=False)
def get_market_data():
    indices = {"S&P 500":"^GSPC","Nasdaq 100":"^NDX","Dow Jones":"^DJI","Russell 2000":"^RUT"}
    result = {}
    for name, sym in indices.items():
        try:
            h = yf.Ticker(sym).history(period="2d")
            if len(h)>=2:
                prev=float(h['Close'].iloc[-2]); curr=float(h['Close'].iloc[-1])
                result[name] = {"price":curr,"pct":(curr-prev)/prev*100}
        except Exception:
            result[name] = {"price":0,"pct":0}
    vix_val=0
    try:
        h=yf.Ticker("^VIX").history(period="1d")
        if not h.empty: vix_val=float(h['Close'].iloc[-1])
    except Exception: pass
    btc_pct=0
    try:
        h=yf.Ticker("BTC-USD").history(period="2d")
        if len(h)>=2: btc_pct=(float(h['Close'].iloc[-1])-float(h['Close'].iloc[-2]))/float(h['Close'].iloc[-2])*100
    except Exception: pass
    noticias=[]
    try:
        for sym in ["SPY","QQQ"]:
            try:
                tk=yf.Ticker(sym)
                news=tk.get_news() if hasattr(tk,'get_news') else tk.news
                for n in (news or []):
                    t=n.get("title",""); l=n.get("link","") or n.get("url","#"); s=n.get("source","") or n.get("publisher","")
                    if t and not any(x["title"]==t for x in noticias):
                        noticias.append({"title":t,"link":l,"source":s})
                if len(noticias)>=6: break
            except Exception: continue
    except Exception: pass
    hot=[]
    try:
        sc=yf.screen("most_active",size=10)
        for q in (sc.get("quotes",[]) if sc else []):
            sym=q.get("symbol",""); pct=q.get("regularMarketChangePercent",0) or 0
            vol=q.get("regularMarketVolume",0) or 0; avol=q.get("averageDailyVolume3Month",1) or 1
            price=q.get("regularMarketPrice",0) or 0
            if sym: hot.append({"T":sym,"P":f"${price:.2f}","Δ":f"{pct:+.2f}%","V×":f"×{vol/avol:.1f}","_p":pct})
    except Exception:
        for sym in ["NVDA","TSLA","AAPL","AMZN","META","AMD","MSFT","SPY","QQQ","COIN"]:
            try:
                h=yf.Ticker(sym).history(period="2d")
                if len(h)>=2:
                    p=float(h['Close'].iloc[-1]); pc=(p-float(h['Close'].iloc[-2]))/float(h['Close'].iloc[-2])*100
                    pv=float(h['Volume'].iloc[-1]); pa=float(h['Volume'].mean())
                    hot.append({"T":sym,"P":f"${p:.2f}","Δ":f"{pc:+.2f}%","V×":f"×{pv/pa:.1f}","_p":pc})
            except Exception: pass
    return result, vix_val, btc_pct, noticias, hot

def analizar_ticker(ticker_name, periodo):
    try:
        df=yf.download(ticker_name,period=periodo,progress=False,auto_adjust=True)
        if df.empty: return None,"Sin datos"
        if isinstance(df.columns,pd.MultiIndex): df.columns=df.columns.get_level_values(0)
    except Exception as e: return None,str(e)[:40]
    df=df.dropna(subset=['Close','Volume']); df=df[df['Volume']>0].copy()
    if len(df)<250: return None,"Pocas velas"
    df['RET_V']=df['Close'].pct_change()*100
    df['BETA_RAW']=df['RET_V'].rolling(60).std(ddof=0)
    df['BETA_S']=df['BETA_RAW'].rolling(20).mean()
    df['BANDA_PRE']=np.where(df['BETA_S']<1.0,"BC",np.where(df['BETA_S']<1.8,"HYB","VOL"))
    df['BANDA']=df['BANDA_PRE']
    df['MA20']=df['Close'].ewm(span=20,adjust=False).mean()
    df['MA50']=df['Close'].ewm(span=50,adjust=False).mean()
    df['MA200']=df['Close'].ewm(span=200,adjust=False).mean()
    df['MA20_UP']=df['MA20']>df['MA20'].shift(1)
    df['H_L']=df['High']-df['Low']
    df['H_PC']=(df['High']-df['Close'].shift(1)).abs()
    df['L_PC']=(df['Low']-df['Close'].shift(1)).abs()
    df['TR_V']=df[['H_L','H_PC','L_PC']].max(axis=1)
    df['ATR_V']=df['TR_V'].rolling(14).mean()
    df['HD']=df['High']-df['High'].shift(1); df['LD']=df['Low'].shift(1)-df['Low']
    df['DMP_RAW']=np.where((df['HD']>0)&(df['HD']>df['LD']),df['HD'],0)
    df['DMM_RAW']=np.where((df['LD']>0)&(df['LD']>df['HD']),df['LD'],0)
    t14=df['TR_V'].rolling(14).sum().replace(0,1e-8)
    df['PDI']=df['DMP_RAW'].rolling(14).sum()*100/t14
    df['MDI']=df['DMM_RAW'].rolling(14).sum()*100/t14
    s14=(df['PDI']+df['MDI']).replace(0,1e-8)
    df['ADX_V']=(abs(df['PDI']-df['MDI'])/s14*100).rolling(9).mean()
    df['ADX_REQ']=np.where(df['Close']<df['MA200'],28,20)
    lm=df['Low'].rolling(9).min(); hm=df['High'].rolling(9).max()
    dk=(hm-lm).replace(0,1e-8)
    df['RSV']=(df['Close']-lm)/dk*100
    df['KVAL']=df['RSV'].ewm(alpha=1/3,adjust=False).mean()
    df['DVAL']=df['KVAL'].ewm(alpha=1/3,adjust=False).mean()
    df['J_V']=3*df['KVAL']-2*df['DVAL']
    df['GIRO_J']=df['J_V']>df['J_V'].shift(1)
    df['CROSS_KD']=(df['KVAL']>df['DVAL'])&(df['KVAL'].shift(1)<=df['DVAL'].shift(1))
    df['DIF']=df['Close'].ewm(span=12,adjust=False).mean()-df['Close'].ewm(span=26,adjust=False).mean()
    df['DEA']=df['DIF'].ewm(span=9,adjust=False).mean()
    df['HISTO']=df['DIF']-df['DEA']
    df['GIRO_MACD']=(df['HISTO']>df['HISTO'].shift(1))&(df['HISTO'].shift(1)<=df['HISTO'].shift(2))
    df['MACD_GIRO_NEG']=(df['HISTO']<0)&(df['HISTO']<df['HISTO'].shift(1))&(df['HISTO'].shift(1)<df['HISTO'].shift(2))
    df['OSC']=calcular_rsi(df['Close'],14)
    df['BB_MID']=df['Close'].rolling(20).mean()
    df['BB_STD']=df['Close'].rolling(20).std(ddof=0)
    df['BB_DN']=df['BB_MID']-2*df['BB_STD']
    df['VOL_MA']=df['Volume'].rolling(20).mean()
    df['MA50_ALCISTA']=df['MA50']>df['MA50'].shift(5)
    df['VENIA_MA50']=df['Close'].shift(1).gt(df['MA50']).rolling(3).sum()>=2
    df['MA200_PLANA']=df['MA200']>=df['MA200'].shift(3)
    df['MA50_SUBE']=df['MA50']>df['MA50'].shift(3)
    # Gatillos CRH v3
    df['S_PULL']=(df['Low']<df['MA50']*1.015)&(df['Close']>df['MA50']*0.985)&df['GIRO_J']&(df['Volume']>df['VOL_MA']*1.02)&df['MA50_ALCISTA']&df['VENIA_MA50']
    df['S_IMPU']=(df['Close']>df['High'].shift(1).rolling(5).max())&(df['ADX_V']>df['ADX_REQ'])&df['MA20_UP']&df['GIRO_J']&(df['Volume']>df['VOL_MA']*1.02)
    df['S_BOLL']=(df['Low'].shift(1)<=df['BB_DN'])&(df['Close']>df['BB_DN'])&df['GIRO_J']&df['GIRO_MACD']&(df['Volume']>df['VOL_MA']*0.88)
    df['S_SUELO']=(df['OSC']<35)&(df['J_V']<25)&(df['Close']>df['Low'].shift(1))&df['GIRO_MACD']&(df['Volume']>df['VOL_MA']*0.88)
    df['CX_MACD']=(df['DIF']>df['DEA'])&(df['DIF'].shift(1)<=df['DEA'].shift(1))
    df['S_MACD_CROSS']=df['CX_MACD']&(df['HISTO']>df['HISTO'].shift(1))&df['MA20_UP']&(df['Volume']>df['VOL_MA']*1.02)
    df['S_EARLY']=(df['OSC']<40)&(df['J_V']<30)&df['CROSS_KD']&df['MA20_UP']&(df['Volume']>df['VOL_MA']*0.88)
    df['S_CONT']=(df['Close']>df['High'].shift(1).rolling(10).max())&(df['Close']>df['MA50'])&df['MA50_SUBE']&df['GIRO_J']
    df['S_R200']=(df['Low']<=df['MA200']*1.01)&(df['Close']>df['MA200'])&(df['Close']>df['Low'].shift(1))&df['GIRO_J']&df['MA20_UP']&df['MA200_PLANA']&(df['Volume']>df['VOL_MA']*1.02)
    df['S_BSOFT']=(df['Low'].shift(1)<=df['BB_DN'])&(df['Close']>df['BB_DN'])&(df['Close']>df['Low'].shift(1))&df['GIRO_J']&(df['Volume']>df['VOL_MA']*0.88)&~df['MACD_GIRO_NEG']
    is_bc=df['BANDA']=="BC"; is_hyb=df['BANDA']=="HYB"; is_vol=df['BANDA']=="VOL"
    sbc =df['S_PULL']|df['S_IMPU']|df['S_BOLL']|df['S_SUELO']|df['S_MACD_CROSS']|df['S_EARLY']|df['S_CONT']|df['S_R200']|df['S_BSOFT']
    shyb=df['S_PULL']|df['S_IMPU']|df['S_BOLL']|df['S_SUELO']|df['S_MACD_CROSS']|df['S_EARLY']|df['S_CONT']|df['S_R200']|df['S_BSOFT']
    svol=df['S_IMPU']|df['S_BOLL']|df['S_SUELO']|df['S_MACD_CROSS']|df['S_CONT']|df['S_R200']|df['S_BSOFT']
    df['B_RAW']=(is_bc&sbc)|(is_hyb&shyb)|(is_vol&svol)
    df['B_SIGNAL'] = df['B_RAW'] & ~df['B_RAW'].shift(1).fillna(False)

    # Solo detectar señal de HOY (ultima barra del dia)
    # App se ejecuta al cierre — solo importa si hoy hay señal nueva
    es_compra_hoy = bool(df['B_SIGNAL'].iloc[-1])
    dias_activa   = 1 if es_compra_hoy else 0
    e_price, atr_entry = None, None
    if es_compra_hoy:
        e_price   = float(df['Close'].iloc[-1])
        atr_entry = float(df['ATR_V'].iloc[-1])
    precio=float(df['Close'].iloc[-1]); banda=df['BANDA'].iloc[-1]
    tp_mult=1.6 if banda=="BC" else (2.0 if banda=="HYB" else 2.5)
    if e_price and atr_entry:
        tp1=e_price+atr_entry*tp_mult; sl=e_price*0.97
        pf=(tp1-precio)/precio*100
        tp1_s=f"${tp1:.2f}"; sl_s=f"${sl:.2f}"; ep_s=f"${e_price:.2f}"
        ft_s=f"✅ +{abs(pf):.1f}%sup" if pf<0 else f"{pf:+.1f}%"
    else:
        tp1_s=sl_s=ep_s=ft_s="—"; pf=0
    gmap={"PULL":"S_PULL","IMPU":"S_IMPU","BOLL":"S_BOLL","SUELO":"S_SUELO",
          "MACD":"S_MACD_CROSS","EARLY":"S_EARLY","CONT":"S_CONT","R200":"S_R200","BSOFT":"S_BSOFT"}
    gatillos=[]
    if dias_activa>0:
        for nombre,col in gmap.items():
            if df[col].iloc[-1]: gatillos.append(nombre)
    def safe(col): v=df[col].iloc[-1]; return float(v) if not pd.isna(v) else 0.0
    rsi_v=safe('OSC'); adx_v=safe('ADX_V')
    df['OJO']=((df['OSC']<35)&(df['J_V']<28)&(df['Close']<=df['BB_DN']*1.01)).fillna(False)
    df['CRUCE_J']=((df['J_V']>10)&(df['J_V'].shift(1).fillna(100)<=12)).fillna(False)
    df['BTD']=(df['OJO'].shift(1).fillna(False)&df['CRUCE_J']&df['GIRO_MACD'].fillna(False)).fillna(False)
    return {
        "Ticker":ticker_name,"Banda":banda,
        "Precio":f"${precio:.2f}","precio_raw":precio,
        "P.Ent":ep_s,"RSI":f"{rsi_v:.1f}","rsi_raw":rsi_v,
        "ADX":f"{adx_v:.1f}","TP1":tp1_s,"SL":sl_s,"%TP":ft_s,
        "Días":dias_activa,"Gatillos":",".join(gatillos) if gatillos else "—",
        "Radar_OJO":bool(df['OJO'].iloc[-2:].any()),
        "Radar_BTD":bool(df['BTD'].iloc[-2:].any()),
    }, None

# ======================================================================
# SESSION STATE
# ======================================================================
for k,v in [("listo",False),("compras",[]),("rsi",[]),("radar",[]),("seccion",None),("ru",33),("periodo","2y")]:
    if k not in st.session_state: st.session_state[k]=v

# ======================================================================
# HELPERS ESTILO
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
def cf(v):
    s=str(v)
    if "sup" in s: return "color:#00e5a0;font-weight:600"
    try:
        r=float(s.replace('%','').replace('+',''))
        if r<=2: return "color:#00e5a0;font-weight:600"
        if r<=5: return "color:#ffd166;font-weight:600"
    except: pass
    return "color:#4a5568"

G1="""<div class="glosario"><b>Banda</b> — BC baja vol · HYB media vol · VOL alta vol &nbsp;·&nbsp; <b>P.Ent</b> — precio vela gatillo &nbsp;·&nbsp; <b>RSI</b> — rojo &lt;33 · verde &gt;65 &nbsp;·&nbsp; <b>TP1</b> — objetivo desde P.Entrada &nbsp;·&nbsp; <b>%TP</b> — distancia al objetivo · ✅ = superado &nbsp;·&nbsp; <b>SL</b> — stop loss 3% bajo P.Entrada</div>"""
G2="""<div class="glosario"><b>RSI</b> — Wilder: rojo &lt;33 sobreventa extrema &nbsp;·&nbsp; <b>ADX</b> — fuerza de tendencia</div>"""
G3="""<div class="glosario"><b>OJO 🟡</b> — alerta: RSI &lt;35 + J(V) &lt;28 + precio cerca BB inferior &nbsp;·&nbsp; <b>BTD 🟢</b> — Buy The Dip confirmado: ayer OJO + hoy J cruza + MACD gira</div>"""

# ======================================================================
# HEADER
# ======================================================================
st.markdown("""
<div class="sg6-header">
    <div class="sg6-header-left">
        <h1>📊 SG6 · <span>Santo Grial</span></h1>
        <p>SISTEMA KW-DNA · BC/HYB/VOL · 9 GATILLOS · ADD · RSI WILDER</p>
    </div>
    <div class="sg6-badge">v2.0 UNIFIED</div>
</div>
""", unsafe_allow_html=True)

# ======================================================================
# PANTALLA INICIAL
# ======================================================================
if not st.session_state.listo:
    with st.spinner("Cargando datos de mercado..."):
        indices, vix_val, btc_pct, noticias, hot = get_market_data()

    # Índices — grid responsivo 4 col desktop / 2 col mobile
    st.markdown('<div class="idx-grid">', unsafe_allow_html=True)
    for name, data in indices.items():
        p=data["price"]; pct=data["pct"]
        sig="+"; cls="up"
        if pct<0: sig=""; cls="down"
        st.markdown(f'<div class="idx-card"><div class="idx-label">{name}</div><div class="idx-price">{p:,.0f}</div><div class="{cls}">{sig}{pct:.2f}%</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # VIX + BTC + Contexto
    sp_pct = indices.get("S&P 500",{}).get("pct",0)
    if vix_val<18 and sp_pct>0:    ctx_cls,ctx_txt="ok","✅ Condiciones favorables"
    elif vix_val>25 or sp_pct<-1:  ctx_cls,ctx_txt="bad","⚠️ Mercado defensivo"
    else:                           ctx_cls,ctx_txt="warn","⚪ Contexto mixto"
    vcls = "ok" if vix_val<18 else ("warn" if vix_val<25 else "bad")
    bcls = "up" if btc_pct>=0 else "down"
    bsig = "+" if btc_pct>=0 else ""

    st.markdown(f"""
    <div class="ctx-grid">
        <div class="ctx-card">
            <div class="ctx-label">VIX — Volatilidad</div>
            <div class="ctx-val">{vix_val:.1f}</div>
            <div class="ctx-sub {vcls}">{"✅ Tranquilo" if vix_val<18 else ("⚠️ Moderado" if vix_val<25 else "🔴 Alto")}</div>
        </div>
        <div class="ctx-card">
            <div class="ctx-label">BTC — Termómetro</div>
            <div class="ctx-val {bcls}">{bsig}{btc_pct:.2f}%</div>
            <div class="ctx-sub {bcls}">{"🟢 Riesgo ON" if btc_pct>=0 else "🔴 Riesgo OFF"}</div>
        </div>
        <div class="ctx-card">
            <div class="ctx-label">Contexto de mercado</div>
            <div class="ctx-val" style="font-size:13px;margin-top:4px;">&nbsp;</div>
            <div class="ctx-sub {ctx_cls}" style="font-size:13px;">{ctx_txt}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Noticias + Hot en 2 columnas desktop / 1 columna mobile
    col_n, col_h = st.columns([3,2])
    with col_n:
        st.markdown('<div class="panel"><div class="panel-title">📰 Noticias del mercado</div>', unsafe_allow_html=True)
        if noticias:
            for n in noticias[:6]:
                st.markdown(f'<div class="news-row"><a href="{n["link"]}" target="_blank">{n["title"]}</a><div class="news-src">{n["source"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#4a5568;font-size:12px;">Sin noticias disponibles.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col_h:
        st.markdown('<div class="panel"><div class="panel-title">🔥 Más activas hoy</div>', unsafe_allow_html=True)
        if hot:
            for h in sorted(hot, key=lambda x:abs(x.get("_p",0)), reverse=True)[:8]:
                col_v="#00e5a0" if h.get("_p",0)>=0 else "#ff4d6d"
                st.markdown(f'<div class="hot-row"><span class="hot-ticker">{h["T"]}</span><span class="hot-price">{h["P"]}</span><span style="color:{col_v};font-weight:600">{h["Δ"]}</span><span class="hot-vol">{h["V×"]}</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:#4a5568;font-size:12px;">Sin datos disponibles.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Configuración
    st.markdown('<div class="config-panel"><div class="config-title">⚙️ Configuración del escáner</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        periodo = st.selectbox("Período histórico", ["2y","1y","6mo"], index=0)
    with col2:
        rsi_umbral = st.slider("RSI sobreventa", 25, 45, 33)
    with col3:
        dias_max = st.slider("Señal activa máx. días", 1, 5, 3)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("▶  EJECUTAR ESCÁNER", use_container_width=True, type="primary"):
        st.session_state.listo=False
        st.session_state.compras=[]; st.session_state.rsi=[]; st.session_state.radar=[]
        st.session_state.seccion=None; st.session_state.ru=rsi_umbral
        st.session_state.periodo=periodo; st.session_state.dias_max=dias_max
        lista_c,lista_r,lista_rd=[],[],[]
        prog=st.progress(0,text="Iniciando escáner...")
        for idx,ticker in enumerate(TICKERS_DEFAULT):
            prog.progress(int((idx+1)/len(TICKERS_DEFAULT)*100), text=f"Analizando {ticker}  ({idx+1}/{len(TICKERS_DEFAULT)})")
            datos,_=analizar_ticker(ticker,periodo)
            if datos is None: continue
            if datos["Días"]==1:
                ant="Día 1" if datos["Días"]==1 else f"Activa {datos['Días']}d"
                lista_c.append({"Ticker":datos["Ticker"],"Banda":datos["Banda"],                    "Gatillos":datos["Gatillos"],"P.Ent":datos["P.Ent"],"Precio":datos["Precio"],
                    "RSI":datos["RSI"],"ADX":datos["ADX"],"TP1":datos["TP1"],"%TP":datos["%TP"],"SL":datos["SL"]})
            if datos["rsi_raw"]<rsi_umbral:
                lista_r.append({"Ticker":datos["Ticker"],"Banda":datos["Banda"],"Precio":datos["Precio"],"RSI":datos["RSI"],"ADX":datos["ADX"]})
            if datos["Radar_BTD"]:
                lista_rd.append({"Ticker":datos["Ticker"],"Señal":"🟢 BTD","Banda":datos["Banda"],"Precio":datos["Precio"],"RSI":datos["RSI"]})
            elif datos["Radar_OJO"]:
                lista_rd.append({"Ticker":datos["Ticker"],"Señal":"🟡 OJO","Banda":datos["Banda"],"Precio":datos["Precio"],"RSI":datos["RSI"]})
        prog.empty()
        st.session_state.compras=lista_c; st.session_state.rsi=lista_r; st.session_state.radar=lista_rd
        st.session_state.listo=True
        st.rerun()

    st.markdown('<p class="footer">SG6 Screener · Sistema KW-DNA · RSI Wilder · Solo con fines educativos · No es asesoría financiera</p>', unsafe_allow_html=True)
    st.stop()

# ======================================================================
# PANTALLA RESULTADOS
# ======================================================================
lc=st.session_state.compras; lr=st.session_state.rsi; lrd=st.session_state.radar; ru=st.session_state.ru

st.success(f"✅ Escáner completado — {len(TICKERS_DEFAULT)} tickers procesados")

# Botones-contadores
c1,c2,c3,c4=st.columns([1,1,1,1])
with c1:
    if st.button(f"🚀 Compras + ADD\n\n{len(lc)}", use_container_width=True):
        st.session_state.seccion=None if st.session_state.seccion=="c" else "c"
with c2:
    if st.button(f"📉 RSI < {ru}\n\n{len(lr)}", use_container_width=True):
        st.session_state.seccion=None if st.session_state.seccion=="r" else "r"
with c3:
    if st.button(f"🎯 Radar OJO/BTD\n\n{len(lrd)}", use_container_width=True):
        st.session_state.seccion=None if st.session_state.seccion=="rd" else "rd"
with c4:
    if st.button("← Nuevo escáner", use_container_width=True):
        st.session_state.listo=False; st.session_state.seccion=None; st.rerun()

st.markdown("---")

sec=st.session_state.seccion
if sec=="c":
    st.markdown('<div class="sec-header"><h4>🚀 Señales activas — compras frescas</h4><div class="sec-line"></div></div>', unsafe_allow_html=True)
    st.markdown(G1, unsafe_allow_html=True)
    if lc:
        df1=pd.DataFrame(lc).reset_index(drop=True); df1.index=range(1,len(df1)+1)
        st.dataframe(df1.style.map(cb,subset=["Banda"]).map(cr,subset=["RSI"]).map(cf,subset=["%TP"]), use_container_width=True)
        c1,c2,_=st.columns([1,1,4])
        with c1: st.download_button("⬇️ CSV", df1.to_csv(index=False).encode(), "compras_sg6.csv","text/csv",key="dl_c")
    else: st.info("Sin señales activas hoy.")
elif sec=="r":
    st.markdown('<div class="sec-header"><h4>📉 Activos en sobreventa</h4><div class="sec-line"></div></div>', unsafe_allow_html=True)
    st.markdown(G2, unsafe_allow_html=True)
    if lr:
        df2=pd.DataFrame(lr).sort_values("RSI").reset_index(drop=True); df2.index=range(1,len(df2)+1)
        st.dataframe(df2.style.map(cb,subset=["Banda"]).map(cr,subset=["RSI"]), use_container_width=True)
        st.download_button("⬇️ CSV", df2.to_csv(index=False).encode(),"sobreventa_sg6.csv","text/csv",key="dl_r")
    else: st.info("Ningún activo en sobreventa extrema.")
elif sec=="rd":
    st.markdown('<div class="sec-header"><h4>🎯 Radar OJO / BTD</h4><div class="sec-line"></div></div>', unsafe_allow_html=True)
    st.markdown(G3, unsafe_allow_html=True)
    if lrd:
        df3=pd.DataFrame(lrd).reset_index(drop=True); df3.index=range(1,len(df3)+1)
        st.dataframe(df3.style.map(cb,subset=["Banda"]).map(cr,subset=["RSI"]), use_container_width=True)
        st.download_button("⬇️ CSV", df3.to_csv(index=False).encode(),"radar_sg6.csv","text/csv",key="dl_rd")
    else: st.info("Sin alertas tempranas de suelo.")
else:
    st.markdown('<p style="color:#1a2235;font-size:13px;text-align:center;padding:32px 0;letter-spacing:.05em;">SELECCIONA UN CONTADOR PARA VER LOS RESULTADOS</p>', unsafe_allow_html=True)

st.markdown('<p class="footer">SG6 Screener · Sistema KW-DNA · RSI Wilder · Solo con fines educativos · No es asesoría financiera</p>', unsafe_allow_html=True)
