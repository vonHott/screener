# ======================================================================
# SG6 SCREENER MÓVIL — V1
# Versión optimizada para celular
# Sin sidebar · Todo vertical · Landing + Resultados
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
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }

/* Ocultar sidebar completamente */
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }

/* Header compacto */
.mob-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 16px;
    text-align: center;
}
.mob-header h1 { color: #f1f5f9; font-size: 18px; font-weight: 700; margin: 0 0 2px 0; }
.mob-header p  { color: #64748b; font-size: 10px; margin: 0; letter-spacing: 0.5px; }

/* Cards de índices */
.idx-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; }
.idx-card { background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 10px 14px; }
.idx-name  { color: #475569; font-size: 9px; letter-spacing: .08em; margin-bottom: 2px; }
.idx-price { color: #f1f5f9; font-size: 17px; font-weight: 700; }
.idx-up    { color: #34d399; font-size: 12px; font-weight: 600; }
.idx-down  { color: #f87171; font-size: 12px; font-weight: 600; }

/* VIX / BTC */
.ctx-card { background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; }
.ctx-label { color: #475569; font-size: 9px; letter-spacing: .08em; }
.ctx-val   { color: #f1f5f9; font-size: 15px; font-weight: 700; }
.vix-ok   { color: #34d399; font-size: 12px; font-weight: 600; }
.vix-warn { color: #fbbf24; font-size: 12px; font-weight: 600; }
.vix-bad  { color: #f87171; font-size: 12px; font-weight: 600; }

/* Noticias */
.news-item { border-bottom: 1px solid #1e293b; padding: 8px 0; font-size: 12px; }
.news-item a { color: #38bdf8; text-decoration: none; }
.news-src  { color: #475569; font-size: 10px; margin-left: 6px; }

/* Hot list */
.hot-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #1e293b; font-size: 12px; }

/* Configuracion landing */
.config-card { background: #0f172a; border: 1px solid #1e293b; border-radius: 10px; padding: 16px; margin-bottom: 12px; }
.config-card h3 { color: #94a3b8; font-size: 12px; letter-spacing: .08em; margin: 0 0 10px 0; }

/* Botones resultado */
[data-testid="stButton"] button {
    background: #0f172a !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
    color: #f1f5f9 !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    width: 100% !important;
    padding: 12px !important;
}
[data-testid="stButton"] button:hover { border-color: #38bdf8 !important; }

/* Tabla compacta */
[data-testid="stDataFrame"] { border: 1px solid #1e293b; border-radius: 6px; font-size: 11px; }

.footer-cap { color: #334155; font-size: 10px; text-align: center; padding: 12px 0; }
.seccion-header { border-left: 3px solid #38bdf8; padding-left: 10px; margin: 12px 0; }
.seccion-header h4 { color: #f1f5f9; font-size: 14px; font-weight: 600; margin: 0; }
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
    indices = {"S&P 500":"^GSPC","Nasdaq":"^NDX","Dow":"^DJI","Russell":"^RUT"}
    result = {}
    for name, sym in indices.items():
        try:
            h = yf.Ticker(sym).history(period="2d")
            if len(h)>=2:
                prev = float(h['Close'].iloc[-2]); curr = float(h['Close'].iloc[-1])
                result[name] = {"price":curr,"pct":(curr-prev)/prev*100}
        except Exception:
            result[name] = {"price":0,"pct":0}
    vix_val = 0
    try:
        h = yf.Ticker("^VIX").history(period="1d")
        if not h.empty: vix_val = float(h['Close'].iloc[-1])
    except Exception: pass
    btc_pct = 0
    try:
        h = yf.Ticker("BTC-USD").history(period="2d")
        if len(h)>=2: btc_pct = (float(h['Close'].iloc[-1])-float(h['Close'].iloc[-2]))/float(h['Close'].iloc[-2])*100
    except Exception: pass
    noticias = []
    try:
        for sym in ["SPY","QQQ"]:
            try:
                tk = yf.Ticker(sym)
                news = tk.get_news() if hasattr(tk,'get_news') else tk.news
                for n in (news or []):
                    title  = n.get("title","")
                    link   = n.get("link","") or n.get("url","#")
                    source = n.get("source","") or n.get("publisher","")
                    if title and not any(x["title"]==title for x in noticias):
                        noticias.append({"title":title,"link":link,"source":source})
                if len(noticias)>=5: break
            except Exception: continue
    except Exception: pass
    hot = []
    try:
        sc = yf.screen("most_active", size=8)
        for q in (sc.get("quotes",[]) if sc else []):
            sym=q.get("symbol",""); pct=q.get("regularMarketChangePercent",0) or 0
            vol=q.get("regularMarketVolume",0) or 0; avol=q.get("averageDailyVolume3Month",1) or 1
            price=q.get("regularMarketPrice",0) or 0
            if sym: hot.append({"T":sym,"P":f"${price:.2f}","Δ":f"{pct:+.1f}%","V×":f"×{vol/avol:.1f}","_p":pct})
    except Exception:
        for sym in ["NVDA","TSLA","AAPL","AMZN","META","AMD","MSFT","SPY"]:
            try:
                h = yf.Ticker(sym).history(period="2d")
                if len(h)>=2:
                    p=float(h['Close'].iloc[-1]); pc=(p-float(h['Close'].iloc[-2]))/float(h['Close'].iloc[-2])*100
                    hot.append({"T":sym,"P":f"${p:.2f}","Δ":f"{pc:+.1f}%","V×":"—","_p":pc})
            except Exception: pass
    return result, vix_val, btc_pct, noticias, hot

def analizar_ticker(ticker_name, periodo):
    try:
        df = yf.download(ticker_name, period=periodo, progress=False, auto_adjust=True)
        if df.empty: return None,"Sin datos"
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    except Exception as e: return None, str(e)[:40]
    df = df.dropna(subset=['Close','Volume']); df = df[df['Volume']>0].copy()
    if len(df)<250: return None,f"Pocas velas"
    df['RET_V']=df['Close'].pct_change()*100
    df['BETA_RAW']=df['RET_V'].rolling(60).std(ddof=0)
    df['BETA_S']=df['BETA_RAW'].rolling(20).mean()
    df['BANDA']=np.where(df['BETA_S']<1.4,"BC","VOL")
    df['MA20']=df['Close'].ewm(span=20,adjust=False).mean()
    df['MA50']=df['Close'].ewm(span=50,adjust=False).mean()
    df['MA200']=df['Close'].ewm(span=200,adjust=False).mean()
    df['MA20_UP']=df['MA20']>df['MA20'].shift(1)
    df['FILTRO_BASE']=df['Close']>=df['MA200']
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
    # Filtros MA
    df['MA50_ALCISTA']=df['MA50']>df['MA50'].shift(5)
    df['VENIA_MA50']=df['Close'].shift(1).gt(df['MA50']).rolling(3).sum()>=2
    df['MA200_PLANA']=df['MA200']>=df['MA200'].shift(3)
    df['MA50_SUBE']=df['MA50']>df['MA50'].shift(3)
    # Gatillos
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
    is_bc=df['BANDA']=="BC"; is_vol=df['BANDA']=="VOL"
    sbc=df['S_PULL']|df['S_IMPU']|df['S_BOLL']|df['S_SUELO']|df['S_MACD_CROSS']|df['S_EARLY']|df['S_CONT']|df['S_R200']|df['S_BSOFT']
    svol=df['S_IMPU']|df['S_BOLL']|df['S_SUELO']|df['S_MACD_CROSS']|df['S_CONT']|df['S_R200']|df['S_BSOFT']
    df['B_RAW']=(is_bc&sbc)|(is_vol&svol)
    b_raw_arr=df['B_RAW'].values
    dias_activa=0
    for k in range(len(b_raw_arr)-1,max(len(b_raw_arr)-6,-1),-1):
        if b_raw_arr[k]: dias_activa+=1
        else: break
    e_price,atr_entry=None,None
    if dias_activa>0:
        idx_e=len(df)-dias_activa
        if idx_e>=0:
            e_price=float(df['Close'].iloc[idx_e])
            atr_entry=float(df['ATR_V'].iloc[idx_e])
    precio=float(df['Close'].iloc[-1]); banda=df['BANDA'].iloc[-1]
    tp_mult=1.6 if banda=="BC" else 2.2
    if e_price and atr_entry:
        tp1=e_price+atr_entry*tp_mult; sl=e_price*0.97
        pf=(tp1-precio)/precio*100
        tp1_s=f"${tp1:.2f}"; sl_s=f"${sl:.2f}"; ep_s=f"${e_price:.2f}"
        ft_s=f"✅{abs(pf):.1f}%sup" if pf<0 else f"{pf:+.1f}%"
    else:
        tp1_s=sl_s=ep_s=ft_s="—"; pf=0
    gmap={"PULL":"S_PULL","IMPU":"S_IMPU","BOLL":"S_BOLL","SUELO":"S_SUELO","MACD":"S_MACD_CROSS","EARLY":"S_EARLY","CONT":"S_CONT","R200":"S_R200","BSOFT":"S_BSOFT"}
    gatillos=[]
    if dias_activa>0:
        for nombre,col in gmap.items():
            if df[col].iloc[-1]: gatillos.append(nombre)
    def safe(col): v=df[col].iloc[-1]; return float(v) if not pd.isna(v) else 0.0
    rsi_v=safe('OSC'); adx_v=safe('ADX_V'); jv_v=safe('J_V')
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
for k,v in [("listo",False),("compras",[]),("rsi",[]),("radar",[]),("seccion",None),("ru",33)]:
    if k not in st.session_state: st.session_state[k]=v

# ======================================================================
# HEADER
# ======================================================================
st.markdown("""
<div class="mob-header">
    <h1>📊 SG6 · Santo Grial</h1>
    <p>KW-DNA · BC/VOL · 9 GATILLOS · ADD · RSI WILDER</p>
</div>
""", unsafe_allow_html=True)

# ======================================================================
# LANDING — pantalla inicial con datos de mercado + configuracion
# ======================================================================
if not st.session_state.listo:
    with st.spinner("Cargando mercado..."):
        indices, vix_val, btc_pct, noticias, hot = get_market_data()

    # Índices 2x2
    st.markdown('<div class="idx-grid">', unsafe_allow_html=True)
    for name, data in indices.items():
        p=data["price"]; pct=data["pct"]
        sig="+" if pct>=0 else ""
        cls="idx-up" if pct>=0 else "idx-down"
        st.markdown(f'<div class="idx-card"><div class="idx-name">{name}</div><div class="idx-price">{p:,.0f}</div><div class="{cls}">{sig}{pct:.2f}%</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # VIX + BTC en 2 columnas
    c1,c2 = st.columns(2)
    with c1:
        vcls = "vix-ok" if vix_val<18 else ("vix-warn" if vix_val<25 else "vix-bad")
        vtxt = "✅ Tranquilo" if vix_val<18 else ("⚠️ Moderado" if vix_val<25 else "🔴 Alto")
        st.markdown(f'<div class="ctx-card"><div class="ctx-label">VIX</div><div class="ctx-val">{vix_val:.1f}</div><div class="{vcls}">{vtxt}</div></div>', unsafe_allow_html=True)
    with c2:
        bcls="idx-up" if btc_pct>=0 else "idx-down"
        bsig="+" if btc_pct>=0 else ""
        btxt="🟢 Riesgo ON" if btc_pct>=0 else "🔴 Riesgo OFF"
        st.markdown(f'<div class="ctx-card"><div class="ctx-label">BTC</div><div class="ctx-val">{bsig}{btc_pct:.2f}%</div><div class="{bcls}">{btxt}</div></div>', unsafe_allow_html=True)

    # Noticias + Hot compactos
    with st.expander("📰 Noticias", expanded=False):
        if noticias:
            for n in noticias[:5]:
                st.markdown(f'<div class="news-item"><a href="{n["link"]}" target="_blank">{n["title"]}</a><span class="news-src">{n["source"]}</span></div>', unsafe_allow_html=True)
        else:
            st.caption("Sin noticias disponibles.")

    with st.expander("🔥 Más activas", expanded=False):
        if hot:
            for h in sorted(hot, key=lambda x:abs(x.get("_p",0)), reverse=True)[:8]:
                col_v="#34d399" if h.get("_p",0)>=0 else "#f87171"
                st.markdown(f'<div class="hot-row"><span style="color:#f1f5f9;font-weight:600">{h["T"]}</span><span style="color:#94a3b8">{h["P"]}</span><span style="color:{col_v};font-weight:600">{h["Δ"]}</span><span style="color:#475569">{h["V×"]}</span></div>', unsafe_allow_html=True)
        else:
            st.caption("Sin datos disponibles.")

    st.markdown("---")

    # Configuracion compacta
    st.markdown('<div class="config-card"><h3>⚙️ CONFIGURACIÓN</h3>', unsafe_allow_html=True)
    periodo    = st.selectbox("Período", ["2y","1y","6mo"], index=0, label_visibility="collapsed")
    rsi_umbral = st.slider("RSI sobreventa", 25, 45, 33)
    dias_max   = st.slider("Señal activa máx. días", 1, 5, 3)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("▶ EJECUTAR ESCÁNER", use_container_width=True, type="primary"):
        st.session_state.listo=False
        st.session_state.compras=[]
        st.session_state.rsi=[]
        st.session_state.radar=[]
        st.session_state.seccion=None
        st.session_state.ru=rsi_umbral
        lista_c,lista_r,lista_rd=[],[],[]
        prog=st.progress(0,text="Escaneando...")
        for idx,ticker in enumerate(TICKERS_DEFAULT):
            prog.progress(int((idx+1)/len(TICKERS_DEFAULT)*100), text=f"{ticker} ({idx+1}/{len(TICKERS_DEFAULT)})")
            datos,_=analizar_ticker(ticker,periodo)
            if datos is None: continue
            es_c=0<datos["Días"]<=dias_max
            if es_c:
                ant="Día 1" if datos["Días"]==1 else f"{datos['Días']}d"
                lista_c.append({"Ticker":datos["Ticker"],"Banda":datos["Banda"],"Días":ant,
                    "Gatillos":datos["Gatillos"],"P.Ent":datos["P.Ent"],"Precio":datos["Precio"],
                    "RSI":datos["RSI"],"ADX":datos["ADX"],"TP1":datos["TP1"],"%TP":datos["%TP"],"SL":datos["SL"]})
            if datos["rsi_raw"]<rsi_umbral:
                lista_r.append({"Ticker":datos["Ticker"],"Banda":datos["Banda"],"Precio":datos["Precio"],"RSI":datos["RSI"],"ADX":datos["ADX"]})
            if datos["Radar_BTD"]:
                lista_rd.append({"Ticker":datos["Ticker"],"Señal":"🟢BTD","Banda":datos["Banda"],"Precio":datos["Precio"],"RSI":datos["RSI"]})
            elif datos["Radar_OJO"]:
                lista_rd.append({"Ticker":datos["Ticker"],"Señal":"🟡OJO","Banda":datos["Banda"],"Precio":datos["Precio"],"RSI":datos["RSI"]})
        prog.empty()
        st.session_state.compras=lista_c
        st.session_state.rsi=lista_r
        st.session_state.radar=lista_rd
        st.session_state.listo=True
        st.rerun()

    st.markdown('<p class="footer-cap">SG6 · KW-DNA · Solo fines educativos · No es asesoría financiera</p>', unsafe_allow_html=True)
    st.stop()

# ======================================================================
# RESULTADOS
# ======================================================================
lc=st.session_state.compras; lr=st.session_state.rsi; lrd=st.session_state.radar
ru=st.session_state.ru

st.success(f"✅ Escáner completado — {len(TICKERS_DEFAULT)} tickers")

# Botones contadores
c1,c2,c3=st.columns(3)
with c1:
    if st.button(f"🚀\n{len(lc)}\nCompras",use_container_width=True):
        st.session_state.seccion=None if st.session_state.seccion=="c" else "c"
with c2:
    if st.button(f"📉\n{len(lr)}\nRSI<{ru}",use_container_width=True):
        st.session_state.seccion=None if st.session_state.seccion=="r" else "r"
with c3:
    if st.button(f"🎯\n{len(lrd)}\nRadar",use_container_width=True):
        st.session_state.seccion=None if st.session_state.seccion=="rd" else "rd"

# Volver
if st.button("← Volver al inicio", use_container_width=False):
    st.session_state.listo=False
    st.session_state.seccion=None
    st.rerun()

st.markdown("---")

def cb(v):
    if v=="BC":  return "background-color:#064e3b;color:#34d399;font-weight:600"
    if v=="VOL": return "background-color:#451a03;color:#fb923c;font-weight:600"
    return ""
def cr(v):
    try:
        r=float(str(v))
        if r<33: return "color:#f87171;font-weight:600"
        if r>65: return "color:#34d399;font-weight:600"
    except: pass
    return "color:#94a3b8"

sec=st.session_state.seccion
if sec=="c":
    st.markdown('<div class="seccion-header"><h4>🚀 Compras frescas</h4></div>',unsafe_allow_html=True)
    if lc:
        df1=pd.DataFrame(lc).reset_index(drop=True)
        df1.index=range(1,len(df1)+1)
        st.dataframe(df1.style.map(cb,subset=["Banda"]).map(cr,subset=["RSI"]),use_container_width=True)
        st.download_button("⬇️ CSV",df1.to_csv(index=False).encode(),"compras.csv","text/csv")
    else:
        st.info("Sin señales activas hoy.")
elif sec=="r":
    st.markdown('<div class="seccion-header"><h4>📉 Sobreventa RSI</h4></div>',unsafe_allow_html=True)
    if lr:
        df2=pd.DataFrame(lr).sort_values("RSI").reset_index(drop=True)
        df2.index=range(1,len(df2)+1)
        st.dataframe(df2.style.map(cb,subset=["Banda"]).map(cr,subset=["RSI"]),use_container_width=True)
    else:
        st.info("Ningún activo en sobreventa.")
elif sec=="rd":
    st.markdown('<div class="seccion-header"><h4>🎯 Radar OJO/BTD</h4></div>',unsafe_allow_html=True)
    if lrd:
        df3=pd.DataFrame(lrd).reset_index(drop=True)
        df3.index=range(1,len(df3)+1)
        st.dataframe(df3.style.map(cb,subset=["Banda"]).map(cr,subset=["RSI"]),use_container_width=True)
    else:
        st.info("Sin alertas de suelo.")
else:
    st.markdown('<p style="color:#334155;font-size:12px;text-align:center;padding:16px 0;">Toca un contador para ver los resultados</p>',unsafe_allow_html=True)

st.markdown('<p class="footer-cap">SG6 · KW-DNA · Solo fines educativos</p>',unsafe_allow_html=True)
