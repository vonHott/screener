# ======================================================================
# SG6 SCREENER — APP STREAMLIT V19
# Santo Grial 6 · Para Inversores
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
    page_title="SG6 Screener · Santo Grial",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', sans-serif; }
.main-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 20px 28px;
    margin-bottom: 20px;
}
.main-header h1 { color: #f1f5f9; font-size: 22px; font-weight: 600; letter-spacing: -0.3px; margin: 0 0 4px 0; }
.main-header p  { color: #64748b; font-size: 12px; margin: 0; letter-spacing: 0.5px; }

/* Botones de sección */
div[data-testid="column"] button {
    width: 100% !important;
    height: 90px !important;
    background: #0f172a !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
    color: #f1f5f9 !important;
    font-size: 28px !important;
    font-weight: 700 !important;
    cursor: pointer !important;
    transition: border-color 0.2s, background 0.2s !important;
    text-align: left !important;
    padding: 14px 20px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
}
div[data-testid="column"] button:hover {
    border-color: #38bdf8 !important;
    background: #0c1a2e !important;
}
div[data-testid="column"] button p {
    font-size: 12px !important;
    color: #64748b !important;
    font-weight: 400 !important;
    margin: 0 !important;
}

[data-testid="stDataFrame"] { border: 1px solid #1e293b; border-radius: 6px; overflow: hidden; }
[data-testid="stSidebar"] { background: #0f172a; border-right: 1px solid #1e293b; }
.glosario { background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 12px 16px; margin-bottom: 12px; font-size: 12px; color: #64748b; line-height: 1.8; }
.glosario b { color: #94a3b8; }
.footer-cap { color: #334155; font-size: 11px; text-align: center; padding-top: 16px; }
.seccion-header { border-left: 3px solid #38bdf8; padding-left: 12px; margin-bottom: 16px; }
.seccion-header h4 { color: #f1f5f9; margin: 0; font-size: 16px; font-weight: 600; }
.seccion-header p  { color: #64748b; margin: 0; font-size: 12px; }
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
    "NKE","META","ORCL","ASML","TSLA","AMD","QQQM","VOO","ACHR","LINK-USD","AVAX-USD"
]

# ======================================================================
# RSI
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
    avg_gain = np.zeros(n)
    avg_loss = np.zeros(n)
    if n > periodo:
        avg_gain[periodo] = gain.iloc[1:periodo+1].mean()
        avg_loss[periodo] = loss.iloc[1:periodo+1].mean()
        for i in range(periodo+1, n):
            avg_gain[i] = (avg_gain[i-1]*(periodo-1) + gain.iloc[i]) / periodo
            avg_loss[i] = (avg_loss[i-1]*(periodo-1) + loss.iloc[i]) / periodo
    rs = avg_gain / np.where(avg_loss==0, 1e-8, avg_loss)
    rsi = 100 - (100 / (1 + rs))
    rsi[:periodo] = np.nan
    return pd.Series(rsi, index=close_series.index)

# ======================================================================
# GEX
# ======================================================================
@st.cache_data(ttl=14400, show_spinner=False)
def calcular_gex(ticker_name, precio_actual):
    try:
        tk = yf.Ticker(ticker_name)
        exps = tk.options
        if not exps: return None
        puts_all, calls_all = [], []
        for exp in exps[:5]:
            try:
                chain = tk.option_chain(exp)
                puts_all.append(chain.puts[['strike','openInterest']].copy())
                calls_all.append(chain.calls[['strike','openInterest']].copy())
            except Exception: continue
        if not puts_all or not calls_all: return None
        puts_df  = pd.concat(puts_all).groupby('strike')['openInterest'].sum().reset_index()
        calls_df = pd.concat(calls_all).groupby('strike')['openInterest'].sum().reset_index()
        rlo, rhi = precio_actual*0.70, precio_actual*1.30
        puts_df  = puts_df[(puts_df['strike']>=rlo)&(puts_df['strike']<=rhi)]
        calls_df = calls_df[(calls_df['strike']>=rlo)&(calls_df['strike']<=rhi)]
        if puts_df.empty or calls_df.empty: return None
        pw = float(puts_df.loc[puts_df['openInterest'].idxmax(),'strike'])
        cw = float(calls_df.loc[calls_df['openInterest'].idxmax(),'strike'])
        if precio_actual > cw: e,c = "🔴","Techo gamma"
        elif precio_actual < pw: e,c = "🟡","Piso gamma"
        else:
            d1,d2 = precio_actual-pw, cw-precio_actual
            e,c = ("🟠","Cerca techo") if d2<d1*0.4 else ("🟢","Zona favorable")
        return {"Put Wall":f"${pw:.2f}","Call Wall":f"${cw:.2f}","GEX":f"{e} {c}"}
    except Exception: return None

# ======================================================================
# ANALISIS
# ======================================================================
@st.cache_data(ttl=14400, show_spinner=False)
def analizar_ticker(ticker_name, periodo):
    try:
        df = yf.download(ticker_name, period=periodo, progress=False, auto_adjust=True)
        if df.empty: return None, "Sin datos en yfinance"
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    except Exception as e: return None, str(e)[:60]

    df = df.dropna(subset=['Close','Volume'])
    df = df[df['Volume']>0].copy()
    if len(df)<250: return None, f"Pocas velas: {len(df)}"

    ultima_fecha = df.index[-1].strftime('%Y-%m-%d')
    df['RET_V']    = df['Close'].pct_change()*100
    df['BETA_RAW'] = df['RET_V'].rolling(60).std(ddof=0)
    df['BETA_S']   = df['BETA_RAW'].rolling(20).mean()
    df['BANDA']    = np.where(df['BETA_S']<1.4,"BC","VOL")
    df['MA20']  = df['Close'].ewm(span=20, adjust=False).mean()
    df['MA50']  = df['Close'].ewm(span=50, adjust=False).mean()
    df['MA200'] = df['Close'].ewm(span=200,adjust=False).mean()
    df['F_BAJISTA']   = df['Close']<df['MA200']
    df['F_ALCISTA']   = df['Close']>df['MA200']
    df['MA20_UP']     = df['MA20']>df['MA20'].shift(1)
    df['FILTRO_BASE'] = df['Close']>=df['MA200']
    df['H_L']  = df['High']-df['Low']
    df['H_PC'] = (df['High']-df['Close'].shift(1)).abs()
    df['L_PC'] = (df['Low'] -df['Close'].shift(1)).abs()
    df['TR_V'] = df[['H_L','H_PC','L_PC']].max(axis=1)
    df['ATR_V'] = df['TR_V'].rolling(14).mean()
    df['HD'] = df['High']-df['High'].shift(1)
    df['LD'] = df['Low'].shift(1)-df['Low']
    df['DMP_RAW'] = np.where((df['HD']>0)&(df['HD']>df['LD']),df['HD'],0)
    df['DMM_RAW'] = np.where((df['LD']>0)&(df['LD']>df['HD']),df['LD'],0)
    tr14 = df['TR_V'].rolling(14).sum().replace(0,1e-8)
    df['PDI'] = df['DMP_RAW'].rolling(14).sum()*100/tr14
    df['MDI'] = df['DMM_RAW'].rolling(14).sum()*100/tr14
    s14 = (df['PDI']+df['MDI']).replace(0,1e-8)
    df['ADX_V']   = (abs(df['PDI']-df['MDI'])/s14*100).rolling(9).mean()
    df['ADX_REQ'] = np.where(df['F_BAJISTA'],28,20)
    tr6 = df['TR_V'].rolling(6).sum().replace(0,1e-8)
    df['PDI_A'] = df['DMP_RAW'].rolling(6).sum()*100/tr6
    df['MDI_A'] = df['DMM_RAW'].rolling(6).sum()*100/tr6
    s6 = (df['PDI_A']+df['MDI_A']).replace(0,1e-8)
    df['ADX_A'] = (abs(df['PDI_A']-df['MDI_A'])/s6*100).rolling(6).mean()
    df['ADX_A_ACCEL'] = (df['ADX_A']>df['ADX_A'].shift(1))&(df['ADX_A'].shift(1)>df['ADX_A'].shift(2))
    lm = df['Low'].rolling(9).min(); hm = df['High'].rolling(9).max()
    dk = (hm-lm).replace(0,1e-8)
    df['RSV']  = (df['Close']-lm)/dk*100
    df['KVAL'] = df['RSV'].ewm(alpha=1/3,adjust=False).mean()
    df['DVAL'] = df['KVAL'].ewm(alpha=1/3,adjust=False).mean()
    df['J_V']  = 3*df['KVAL']-2*df['DVAL']
    df['GIRO_J']   = df['J_V']>df['J_V'].shift(1)
    df['CROSS_KD'] = (df['KVAL']>df['DVAL'])&(df['KVAL'].shift(1)<=df['DVAL'].shift(1))
    df['DIF']   = df['Close'].ewm(span=12,adjust=False).mean()-df['Close'].ewm(span=26,adjust=False).mean()
    df['DEA']   = df['DIF'].ewm(span=9,adjust=False).mean()
    df['HISTO'] = df['DIF']-df['DEA']
    df['GIRO_MACD']      = (df['HISTO']>df['HISTO'].shift(1))&(df['HISTO'].shift(1)<=df['HISTO'].shift(2))
    df['MACD_GIRO_NEG']  = (df['HISTO']<0)&(df['HISTO']<df['HISTO'].shift(1))&(df['HISTO'].shift(1)<df['HISTO'].shift(2))
    df['MACD_CONV_ALCI'] = (df['HISTO']<0)&(df['HISTO']>df['HISTO'].shift(1))&(df['HISTO']>df['HISTO'].shift(2))
    df['OSC'] = calcular_rsi(df['Close'],14)
    df['BB_MID'] = df['Close'].rolling(20).mean()
    df['BB_STD'] = df['Close'].rolling(20).std(ddof=0)
    df['BB_DN']  = df['BB_MID']-2*df['BB_STD']
    df['VOL_MA'] = df['Volume'].rolling(20).mean()

    df['S_PULL']       = (df['Low']<df['MA50']*1.015)&(df['Close']>df['MA50']*0.985)&df['GIRO_J']&(df['Volume']>df['VOL_MA']*1.05)&df['FILTRO_BASE']
    df['S_IMPU']       = (df['Close']>df['High'].shift(1).rolling(5).max())&(df['ADX_V']>df['ADX_REQ'])&df['MA20_UP']&df['GIRO_J']&(df['Volume']>df['VOL_MA']*1.05)
    df['S_BOLL']       = (df['Low'].shift(1)<=df['BB_DN'])&(df['Close']>df['BB_DN'])&df['GIRO_J']&df['GIRO_MACD']&(df['Volume']>df['VOL_MA']*1.05)&df['FILTRO_BASE']
    df['S_SUELO']      = (df['OSC']<32)&(df['J_V']<22)&(df['Low'].shift(1)<=df['BB_DN'])&(df['Close']>df['BB_DN'])&(df['Close']>df['Low'].shift(1))&df['GIRO_MACD']&(df['Volume']>df['VOL_MA']*0.9)
    df['CX_MACD']      = (df['DIF']>df['DEA'])&(df['DIF'].shift(1)<=df['DEA'].shift(1))
    df['S_MACD_CROSS'] = df['CX_MACD']&(df['DIF']<0)&(df['HISTO']>df['HISTO'].shift(1))&(df['Close']>df['MA20'])&df['MA20_UP']&(df['Volume']>df['VOL_MA']*1.05)&df['FILTRO_BASE']
    df['S_EARLY']      = (df['OSC']<38)&(df['J_V']<30)&df['CROSS_KD']&(df['Close']>df['Close'].shift(1))&df['MA20_UP']&(df['Volume']>df['VOL_MA']*0.9)&df['FILTRO_BASE']
    df['S_R50']        = (df['Low']<=df['MA50']*1.008)&(df['Close']>df['MA50'])&(df['Close']>df['BB_DN'])&(df['Close']<df['BB_MID'])&df['GIRO_J']&df['MA20_UP']&df['F_ALCISTA']&(df['Volume']>df['VOL_MA']*0.95)
    df['S_R200']       = (df['Low']<=df['MA200']*1.01)&(df['Close']>df['MA200'])&(df['Close']>df['Low'].shift(1))&df['GIRO_J']&df['MA20_UP']&(df['Volume']>df['VOL_MA']*0.95)
    df['S_BSOFT']      = (df['Low'].shift(1)<=df['BB_DN'])&(df['Close']>df['BB_DN'])&(df['Close']>df['Low'].shift(1))&df['GIRO_J']&(df['Volume']>df['VOL_MA']*0.9)&df['FILTRO_BASE']&~df['MACD_GIRO_NEG']

    is_bc  = df['BANDA']=="BC"; is_vol = df['BANDA']=="VOL"
    sbc  = df['S_PULL']|df['S_IMPU']|df['S_BOLL']|df['S_SUELO']|df['S_MACD_CROSS']|df['S_EARLY']|df['S_R50']|df['S_R200']|df['S_BSOFT']
    svol = df['S_IMPU']|df['S_BOLL']|df['S_SUELO']|df['S_MACD_CROSS']|df['S_EARLY']|df['S_R200']|df['S_BSOFT']
    df['B_RAW'] = (is_bc&sbc)|(is_vol&svol)

    b_raw_arr = df['B_RAW'].values
    dias_activa = 0
    for k in range(len(b_raw_arr)-1, max(len(b_raw_arr)-6,-1), -1):
        if b_raw_arr[k]: dias_activa += 1
        else: break

    # Precio de entrada = cierre del primer dia de la racha activa
    e_price, atr_entry = None, None
    if dias_activa > 0:
        idx_e = len(df) - dias_activa
        if idx_e >= 0:
            e_price   = float(df['Close'].iloc[idx_e])
            atr_entry = float(df['ATR_V'].iloc[idx_e])

    precio  = float(df['Close'].iloc[-1])
    banda   = df['BANDA'].iloc[-1]
    tp_mult = 1.6 if banda=="BC" else 2.2

    if e_price and atr_entry:
        tp1 = e_price + atr_entry*tp_mult
        sl  = e_price*0.97
        pf  = (tp1-precio)/precio*100
        pd_ = (precio-sl)/precio*100
        tp1_s = f"${tp1:.2f}"
        sl_s  = f"${sl:.2f}"
        ep_s  = f"${e_price:.2f}"
        ft_s  = f"✅ +{abs(pf):.1f}% sup." if pf<0 else f"{pf:+.1f}%"
        ds_s  = f"{pd_:.1f}%"
    else:
        tp1_s=sl_s=ep_s=ft_s=ds_s="—"; pf=0; pd_=99

    i = len(df)-1
    add_bc  = (dias_activa>0 and banda=="BC"  and df['PDI_A'].iloc[i]>df['MDI_A'].iloc[i] and df['ADX_A'].iloc[i]>28 and bool(df['ADX_A_ACCEL'].iloc[i]) and bool(df['CROSS_KD'].iloc[i]) and df['KVAL'].iloc[i]<75 and df['Close'].iloc[i]>df['MA20'].iloc[i] and df['Volume'].iloc[i]>df['VOL_MA'].iloc[i]*1.2)
    add_vol = (dias_activa>0 and banda=="VOL" and df['PDI_A'].iloc[i]>df['MDI_A'].iloc[i] and df['ADX_A'].iloc[i]>32 and bool(df['ADX_A_ACCEL'].iloc[i]) and df['Close'].iloc[i]>df['High'].iloc[max(0,i-3):i].max() and df['Close'].iloc[i]>df['MA20'].iloc[i] and df['Volume'].iloc[i]>df['VOL_MA'].iloc[i]*1.4)
    add_s = "ADD-BC" if add_bc else ("ADD-VOL" if add_vol else None)

    gmap = {"S_PULL":"S_PULL","S_IMPU":"S_IMPU","S_BOLL":"S_BOLL","S_SUELO":"S_SUELO",
            "S_MACD_CROSS":"S_MACD_CROSS","S_EARLY":"S_EARLY",
            "S_REBOTE_MA50":"S_R50","S_REBOTE_MA200":"S_R200","S_BOLL_SOFT":"S_BSOFT"}
    gatillos = []
    if dias_activa>0:
        for nombre,col in gmap.items():
            if df[col].iloc[-1]: gatillos.append(nombre)
    if add_s: gatillos.append(f"⚡{add_s}")

    df['OJO']     = ((df['OSC']<35)&(df['J_V']<28)&(df['Close']<=df['BB_DN']*1.01)).fillna(False)
    df['CRUCE_J'] = ((df['J_V']>10)&(df['J_V'].shift(1).fillna(100)<=12)).fillna(False)
    df['BTD']     = (df['OJO'].shift(1).fillna(False)&df['CRUCE_J']&df['GIRO_MACD'].fillna(False)).fillna(False)

    def safe(col): v=df[col].iloc[-1]; return float(v) if not pd.isna(v) else 0.0
    rsi_v=safe('OSC'); adx_v=safe('ADX_V'); jv_v=safe('J_V'); bdn_v=safe('BB_DN')

    return {
        "Ticker":       ticker_name,
        "Banda":        banda,
        "Precio":       f"${precio:.2f}",
        "precio_raw":   precio,
        "P.Entrada":    ep_s,
        "RSI":          f"{rsi_v:.1f}",
        "rsi_raw":      rsi_v,
        "ADX":          f"{adx_v:.1f}",
        "J(V)":         f"{jv_v:.1f}",
        "BB_DN":        f"${bdn_v:.2f}",
        "Días":         dias_activa,
        "Gatillos":     ", ".join(gatillos) if gatillos else "—",
        "TP1":          tp1_s,
        "Falta TP1":    ft_s,
        "SL −3%":       sl_s,
        "Dist. SL":     ds_s,
        "pf":           pf,
        "pd":           pd_,
        "Radar_OJO":    bool(df['OJO'].iloc[-2:].any()),
        "Radar_BTD":    bool(df['BTD'].iloc[-2:].any()),
        "Add_Senal":    add_s,
    }, None

def exportar_excel(dfs_dict):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as w:
        for n,d in dfs_dict.items():
            if d is not None and not d.empty: d.to_excel(w, sheet_name=n[:31], index=False)
    return buf.getvalue()

# ======================================================================
# SIDEBAR
# ======================================================================
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    st.markdown("---")
    periodo    = st.selectbox("Período histórico",["2y","1y","6mo"],index=0)
    rsi_umbral = st.slider("Umbral RSI sobreventa",25,45,33)
    dias_max   = st.slider("Señal activa máx. días",1,5,3)
    usar_gex   = st.toggle("Put/Call Wall GEX (próximas 5 semanas)",value=True)
    st.markdown("---")
    ejecutar = st.button("▶ Ejecutar escáner",use_container_width=True,type="primary")
    st.markdown('<p style="color:#334155;font-size:11px;text-align:center;margin-top:8px;">SG6 · v19.0 · Solo fines educativos</p>',unsafe_allow_html=True)

# ======================================================================
# HEADER
# ======================================================================
st.markdown("""
<div class="main-header">
    <h1>📊 SG6 Screener · Santo Grial</h1>
    <p>SISTEMA KW-DNA · BC/VOL ADAPTATIVO · 9 GATILLOS · ADD · PUT/CALL WALL · RSI WILDER</p>
</div>
""", unsafe_allow_html=True)

if not ejecutar:
    c1,c2,c3 = st.columns(3)
    with c1: st.info("**9 Gatillos de entrada**\n\nS_PULL · S_IMPU · S_BOLL · S_SUELO · S_MACD_CROSS · S_EARLY · S_REBOTE_MA50 · S_REBOTE_MA200 · S_BOLL_SOFT")
    with c2: st.info("**ADD automático ⚡**\n\nDetecta señales ADD-BC y ADD-VOL sobre posiciones abiertas")
    with c3: st.info("**GEX Put/Call Wall · 5 semanas**\n\n🟢 Favorable · 🟠 Cerca techo · 🔴 Techo activo · 🟡 Piso gamma")
    st.stop()

# ======================================================================
# EJECUCION
# ======================================================================
lista_compras,lista_rsi,lista_radar,lista_desc = [],[],[],[]
progreso   = st.progress(0, text="Iniciando escáner...")
status_box = st.empty()

for idx,ticker in enumerate(TICKERS_DEFAULT):
    pct = int((idx+1)/len(TICKERS_DEFAULT)*100)
    progreso.progress(pct, text=f"Analizando {ticker}  ({idx+1}/{len(TICKERS_DEFAULT)})")

    datos, motivo = analizar_ticker(ticker, periodo)
    if datos is None:
        lista_desc.append({"Ticker":ticker,"Motivo":motivo}); continue

    gex = None
    if usar_gex and not any(x in ticker for x in ['-USD','ETH','BTC','SOL']):
        gex = calcular_gex(ticker, datos["precio_raw"])
    pw = gex["Put Wall"]  if gex else "—"
    cw = gex["Call Wall"] if gex else "—"
    gx = gex["GEX"]       if gex else "—"

    es_c = 0 < datos["Días"] <= dias_max
    es_a = datos["Add_Senal"] is not None

    if es_c or es_a:
        ant = "Día 1" if datos["Días"]==1 else f"Activa {datos['Días']}d" if datos["Días"]>0 else "ADD"
        lista_compras.append({"Ticker":datos["Ticker"],"Banda":datos["Banda"],"Antigüedad":ant,
            "Gatillos":datos["Gatillos"],"P.Entrada":datos["P.Entrada"],"Precio":datos["Precio"],
            "RSI":datos["RSI"],"ADX":datos["ADX"],"TP1":datos["TP1"],"Falta TP1":datos["Falta TP1"],
            "SL −3%":datos["SL −3%"],"Dist. SL":datos["Dist. SL"],
            "Put Wall":pw,"Call Wall":cw,"GEX":gx,"_pf":datos["pf"],"_pd":datos["pd"]})

    if datos["rsi_raw"] < rsi_umbral:
        lista_rsi.append({"Ticker":datos["Ticker"],"Banda":datos["Banda"],"Precio":datos["Precio"],
            "RSI":datos["RSI"],"J(V)":datos["J(V)"],"ADX":datos["ADX"],"Put Wall":pw,"Call Wall":cw,"GEX":gx})

    if datos["Radar_BTD"]:
        lista_radar.append({"Ticker":datos["Ticker"],"Señal":"🟢 BTD","Banda":datos["Banda"],"Precio":datos["Precio"],"RSI":datos["RSI"],"J(V)":datos["J(V)"],"BB_DN":datos["BB_DN"],"Put Wall":pw,"Call Wall":cw,"GEX":gx})
    elif datos["Radar_OJO"]:
        lista_radar.append({"Ticker":datos["Ticker"],"Señal":"🟡 OJO","Banda":datos["Banda"],"Precio":datos["Precio"],"RSI":datos["RSI"],"J(V)":datos["J(V)"],"BB_DN":datos["BB_DN"],"Put Wall":pw,"Call Wall":cw,"GEX":gx})

progreso.empty()
status_box.success(f"✅ Escáner completado — {len(TICKERS_DEFAULT)} tickers procesados")

# ======================================================================
# BOTONES DE SECCION — SON LOS CONTADORES Y ABREN/CIERRAN
# ======================================================================
if "seccion" not in st.session_state:
    st.session_state.seccion = None

c1,c2,c3 = st.columns(3)
with c1:
    if st.button(f"🚀 Compras + ADD\n\n{len(lista_compras)}", use_container_width=True):
        st.session_state.seccion = None if st.session_state.seccion=="compras" else "compras"
with c2:
    if st.button(f"📉 RSI < {rsi_umbral}\n\n{len(lista_rsi)}", use_container_width=True):
        st.session_state.seccion = None if st.session_state.seccion=="rsi" else "rsi"
with c3:
    if st.button(f"🎯 Radar OJO/BTD\n\n{len(lista_radar)}", use_container_width=True):
        st.session_state.seccion = None if st.session_state.seccion=="radar" else "radar"

# ======================================================================
# HELPERS
# ======================================================================
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
def cf(v):
    s=str(v)
    if "sup." in s: return "color:#34d399;font-weight:600"
    try:
        r=float(s.replace('%','').replace('+',''))
        if r<=2: return "color:#34d399;font-weight:600"
        if r<=5: return "color:#fbbf24;font-weight:600"
    except: pass
    return "color:#94a3b8"
def cs(v):
    try:
        r=float(str(v).replace('%',''))
        if r<1: return "color:#f87171;font-weight:600"
        if r<2: return "color:#fbbf24;font-weight:600"
    except: pass
    return "color:#94a3b8"

G1="""<div class="glosario"><b>Banda</b> — BC (baja volatilidad) · VOL (alta volatilidad) &nbsp;|&nbsp; <b>Antigüedad</b> — días desde la vela gatillo &nbsp;|&nbsp; <b>Gatillos</b> — señales que activaron la entrada · ⚡ = ADD sobre posición abierta &nbsp;|&nbsp; <b>P.Entrada</b> — precio de cierre de la vela gatillo (fijo) &nbsp;|&nbsp; <b>Precio</b> — precio actual &nbsp;|&nbsp; <b>RSI</b> — momentum: rojo &lt;33 · verde &gt;65 &nbsp;|&nbsp; <b>ADX</b> — fuerza de tendencia (&gt;25 relevante) &nbsp;|&nbsp; <b>TP1</b> — objetivo desde P.Entrada + ATR×mult &nbsp;|&nbsp; <b>Falta TP1</b> — distancia al objetivo · ✅ = ya superado &nbsp;|&nbsp; <b>SL −3%</b> — stop loss fijo 3% bajo P.Entrada &nbsp;|&nbsp; <b>Dist. SL</b> — margen actual al stop · rojo = peligro &nbsp;|&nbsp; <b>Put/Call Wall</b> — soporte/resistencia gamma opciones 5 semanas &nbsp;|&nbsp; <b>GEX</b> — 🟢 favorable · 🟠 cerca techo · 🔴 techo activo · 🟡 piso gamma</div>"""
G2="""<div class="glosario"><b>RSI</b> — Wilder: rojo &lt;33 sobreventa extrema &nbsp;|&nbsp; <b>J(V)</b> — KDJ: &lt;20 zona de posible giro alcista &nbsp;|&nbsp; <b>ADX</b> — fuerza de tendencia &nbsp;|&nbsp; <b>Put/Call Wall</b> — soporte y resistencia gamma 5 semanas &nbsp;|&nbsp; <b>GEX</b> — contexto gamma actual</div>"""
G3="""<div class="glosario"><b>OJO 🟡</b> — alerta temprana: RSI &lt;35 + J(V) &lt;28 + precio cerca banda inferior Bollinger &nbsp;|&nbsp; <b>BTD 🟢</b> — Buy The Dip confirmado: ayer OJO + hoy J cruza + MACD gira &nbsp;|&nbsp; <b>BB_DN</b> — banda inferior Bollinger</div>"""

def dl_buttons(df_out, base):
    c1,c2,_ = st.columns([1,1,4])
    with c1:
        st.download_button("⬇️ Excel", exportar_excel({base:df_out.reset_index(drop=True)}),
                           f"{base}_sg6.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",key=f"xl_{base}")
    with c2:
        st.download_button("⬇️ CSV", df_out.to_csv(index=False).encode("utf-8"),
                           f"{base}_sg6.csv","text/csv",key=f"csv_{base}")

# ======================================================================
# SECCIONES — se muestran solo si el botón está activo
# ======================================================================
st.markdown("---")

if st.session_state.seccion == "compras":
    st.markdown('<div class="seccion-header"><h4>🚀 Señales activas — compras frescas y ADD</h4><p>TP1 y SL calculados desde la vela gatillo · ⚡ = ADD sobre posición abierta</p></div>', unsafe_allow_html=True)
    st.markdown(G1, unsafe_allow_html=True)
    if lista_compras:
        df1 = pd.DataFrame(lista_compras)
        df1['_o'] = df1['Gatillos'].apply(lambda x: 1 if '⚡' in str(x) and not any(
            g in str(x) for g in ['S_PULL','S_IMPU','S_BOLL','S_SUELO','S_MACD','S_EARLY','S_REBOTE','SOFT']) else 0)
        df1 = df1.sort_values('_o').drop(columns=['_o','_pf','_pd']).reset_index(drop=True)
        df1.index = range(1, len(df1)+1)
        st.dataframe(df1.style.map(cb,subset=["Banda"]).map(cr,subset=["RSI"]).map(cf,subset=["Falta TP1"]).map(cs,subset=["Dist. SL"]), use_container_width=True)
        dl_buttons(df1, "compras")
    else:
        st.info("Ninguna compra fresca ni ADD activo hoy.")

elif st.session_state.seccion == "rsi":
    st.markdown('<div class="seccion-header"><h4>📉 Activos en sobreventa</h4><p>RSI Wilder por debajo del umbral configurado</p></div>', unsafe_allow_html=True)
    st.markdown(G2, unsafe_allow_html=True)
    if lista_rsi:
        df2 = pd.DataFrame(lista_rsi).sort_values("RSI").reset_index(drop=True)
        df2.index = range(1, len(df2)+1)
        st.dataframe(df2.style.map(cb,subset=["Banda"]).map(cr,subset=["RSI"]), use_container_width=True)
        dl_buttons(df2, "sobreventa")
    else:
        st.info("Ningún activo en sobreventa extrema hoy.")

elif st.session_state.seccion == "radar":
    st.markdown('<div class="seccion-header"><h4>🎯 Radar temprano — formación de suelo</h4><p>OJO: alerta · BTD: confirmación</p></div>', unsafe_allow_html=True)
    st.markdown(G3, unsafe_allow_html=True)
    if lista_radar:
        df3 = pd.DataFrame(lista_radar)
        df3["_o"] = df3["Señal"].apply(lambda x: 0 if "BTD" in x else 1)
        df3 = df3.sort_values(["_o","RSI"]).drop(columns="_o").reset_index(drop=True)
        df3.index = range(1, len(df3)+1)
        st.dataframe(df3.style.map(cb,subset=["Banda"]).map(cr,subset=["RSI"]), use_container_width=True)
        dl_buttons(df3, "radar")
    else:
        st.info("Sin alertas tempranas de formación de suelo.")

else:
    st.markdown('<p style="color:#334155;font-size:13px;text-align:center;padding:24px 0;">Haz clic en uno de los contadores para ver los resultados</p>', unsafe_allow_html=True)

if lista_desc:
    with st.expander(f"⚠️ Tickers descartados ({len(lista_desc)})", expanded=False):
        st.dataframe(pd.DataFrame(lista_desc), use_container_width=True, hide_index=True)

st.markdown('<p class="footer-cap">SG6 Screener · Sistema KW-DNA · RSI Wilder · GEX 5 series · Solo con fines educativos · No es asesoría financiera</p>', unsafe_allow_html=True)
