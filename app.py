# ======================================================================
# SG6 SCREENER — APP STREAMLIT V16
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

# ======================================================================
# CONFIGURACION Y CSS
# ======================================================================
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
    margin-bottom: 24px;
}
.main-header h1 { color: #f1f5f9; font-size: 22px; font-weight: 600; letter-spacing: -0.3px; margin: 0 0 4px 0; }
.main-header p  { color: #64748b; font-size: 12px; margin: 0; letter-spacing: 0.5px; }
[data-testid="metric-container"] { background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 12px 16px; }
[data-testid="stTabs"] button { font-size: 13px; font-weight: 500; color: #64748b; }
[data-testid="stTabs"] button[aria-selected="true"] { color: #38bdf8; border-bottom-color: #38bdf8; }
[data-testid="stDataFrame"] { border: 1px solid #1e293b; border-radius: 6px; overflow: hidden; }
[data-testid="stSidebar"] { background: #0f172a; border-right: 1px solid #1e293b; }
.footer-cap { color: #334155; font-size: 11px; text-align: center; padding-top: 16px; }
</style>
""", unsafe_allow_html=True)

# ======================================================================
# WATCHLIST
# ======================================================================
TICKERS_DEFAULT = [
    "CHWY", "ALT", "PLTR", "RBRK", "MORN", "CBRS", "ISRG", "MDT",
    "DG", "EPAM", "BRK-B", "NCLH", "CLS", "GILD", "FSLR", "RTX", "PSX",
    "NBIS", "ZTS", "FICO", "BAC", "GS", "NOW", "RMBS", "MRVL",
    "COF", "BHP", "ETH-USD", "SOL-USD", "BTI", "SAP", "FDX", "TME",
    "INTU", "SONY", "COHR", "GDDY", "PM", "TSM", "CRDO", "NNE",
    "NRG", "BLK", "ENPH", "LMT", "DPZ", "IONQ", "VRT", "VRTX",
    "MSFT", "AAPL", "MMM", "HD", "GOOGL", "EBAY", "SOFI", "MPWR",
    "LULU", "CPRT", "ETN", "TJX", "ADP", "NEE", "DHR", "T", "VZ",
    "QQQ", "MU", "TXN", "OKTA", "ZS", "AFRM", "GME", "BABA",
    "RIOT", "ARM", "XLP", "XLK", "XLI", "XLV", "XLE", "IWM", "SPY",
    "UBER", "PYPL", "INTC", "LRCX", "AMAT", "REGN", "SHOP", "HOOD",
    "NET", "CRWD", "DDOG", "SNOW", "MDB", "MARA", "COIN", "AVGO",
    "CSCO", "ACN", "LIN", "TMO", "LLY", "ABBV", "ABNB", "MRNA",
    "AMT", "ASTS", "PANW", "APH", "SMCI", "DELL", "ANET", "STX",
    "WDC", "RCL", "BKNG", "TMUS", "DE", "CRM", "ADBE", "TGT",
    "COST", "CVX", "XOM", "GE", "ABT", "AMZN", "BTC-USD", "SOUN",
    "IBM", "SMH", "URA", "CEG", "NVO", "MRK", "SPOT", "EQIX",
    "BA", "FCX", "AEM", "MSTR", "PEP", "KO", "WMT", "PFE", "DIS",
    "JNJ", "MCD", "JPM", "MA", "CAT", "SBUX", "PG", "UNH",
    "NVDA", "NFLX", "MELI", "NKE", "META", "ORCL", "ASML", "TSLA",
    "AMD", "QQQM", "VOO", "ACHR", "LINK-USD", "AVAX-USD"
]

# ======================================================================
# RSI
# ======================================================================
def calcular_rsi(close_series, periodo=14):
    if USE_PANDAS_TA:
        try:
            return ta.rsi(close_series, length=periodo)
        except Exception:
            pass
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
    avg_loss_safe = np.where(avg_loss == 0, 1e-8, avg_loss)
    rs  = avg_gain / avg_loss_safe
    rsi = 100 - (100 / (1 + rs))
    rsi[:periodo] = np.nan
    return pd.Series(rsi, index=close_series.index)

# ======================================================================
# GEX — PUT WALL / CALL WALL (5 SERIES)
# ======================================================================
@st.cache_data(ttl=14400, show_spinner=False)
def calcular_gex(ticker_name, precio_actual):
    try:
        tk   = yf.Ticker(ticker_name)
        exps = tk.options
        if not exps:
            return None
        puts_all, calls_all = [], []
        for exp in exps[:5]:
            try:
                chain = tk.option_chain(exp)
                puts_all.append(chain.puts[['strike','openInterest']].copy())
                calls_all.append(chain.calls[['strike','openInterest']].copy())
            except Exception:
                continue
        if not puts_all or not calls_all:
            return None
        puts_df  = pd.concat(puts_all).groupby('strike')['openInterest'].sum().reset_index()
        calls_df = pd.concat(calls_all).groupby('strike')['openInterest'].sum().reset_index()
        rlo, rhi = precio_actual * 0.70, precio_actual * 1.30
        puts_df  = puts_df[(puts_df['strike']>=rlo) & (puts_df['strike']<=rhi)]
        calls_df = calls_df[(calls_df['strike']>=rlo) & (calls_df['strike']<=rhi)]
        if puts_df.empty or calls_df.empty:
            return None
        put_wall  = float(puts_df.loc[puts_df['openInterest'].idxmax(), 'strike'])
        call_wall = float(calls_df.loc[calls_df['openInterest'].idxmax(), 'strike'])
        if precio_actual > call_wall:
            emoji, ctx = "🔴", "Techo gamma"
        elif precio_actual < put_wall:
            emoji, ctx = "🟡", "Piso gamma"
        else:
            dist_put  = precio_actual - put_wall
            dist_call = call_wall - precio_actual
            emoji, ctx = ("🟠", "Cerca techo") if dist_call < dist_put * 0.4 else ("🟢", "Zona favorable")
        return {
            "Put Wall":  f"${put_wall:.2f}",
            "Call Wall": f"${call_wall:.2f}",
            "GEX":       f"{emoji} {ctx}",
        }
    except Exception:
        return None

# ======================================================================
# ANALISIS POR TICKER — SG6
# ======================================================================
@st.cache_data(ttl=14400, show_spinner=False)
def analizar_ticker(ticker_name, periodo):
    try:
        df = yf.download(ticker_name, period=periodo, progress=False, auto_adjust=True)
        if df.empty:
            return None, "Sin datos en yfinance"
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
    except Exception as e:
        return None, str(e)[:60]

    df = df.dropna(subset=['Close','Volume'])
    df = df[df['Volume'] > 0].copy()
    if len(df) < 250:
        return None, f"Pocas velas: {len(df)}"

    ultima_fecha = df.index[-1].strftime('%Y-%m-%d')

    df['RET_V']    = df['Close'].pct_change() * 100
    df['BETA_RAW'] = df['RET_V'].rolling(60).std(ddof=0)
    df['BETA_S']   = df['BETA_RAW'].rolling(20).mean()
    df['BANDA']    = np.where(df['BETA_S'] < 1.4, "BC", "VOL")

    df['MA20']  = df['Close'].ewm(span=20,  adjust=False).mean()
    df['MA50']  = df['Close'].ewm(span=50,  adjust=False).mean()
    df['MA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    df['F_BAJISTA']   = df['Close'] < df['MA200']
    df['F_ALCISTA']   = df['Close'] > df['MA200']
    df['MA20_UP']     = df['MA20'] > df['MA20'].shift(1)
    df['FILTRO_BASE'] = df['Close'] >= df['MA200']

    df['H_L']  = df['High'] - df['Low']
    df['H_PC'] = (df['High'] - df['Close'].shift(1)).abs()
    df['L_PC'] = (df['Low']  - df['Close'].shift(1)).abs()
    df['TR_V'] = df[['H_L','H_PC','L_PC']].max(axis=1)
    df['ATR_V'] = df['TR_V'].rolling(14).mean()

    df['HD'] = df['High'] - df['High'].shift(1)
    df['LD'] = df['Low'].shift(1) - df['Low']
    df['DMP_RAW'] = np.where((df['HD']>0)&(df['HD']>df['LD']), df['HD'], 0)
    df['DMM_RAW'] = np.where((df['LD']>0)&(df['LD']>df['HD']), df['LD'], 0)
    tr_sum = df['TR_V'].rolling(14).sum().replace(0,1e-8)
    df['PDI'] = df['DMP_RAW'].rolling(14).sum() * 100 / tr_sum
    df['MDI'] = df['DMM_RAW'].rolling(14).sum() * 100 / tr_sum
    pdi_mdi_sum = (df['PDI']+df['MDI']).replace(0,1e-8)
    df['ADX_V']   = (abs(df['PDI']-df['MDI'])/pdi_mdi_sum*100).rolling(9).mean()
    df['ADX_REQ'] = np.where(df['F_BAJISTA'], 28, 20)

    tr_sum6   = df['TR_V'].rolling(6).sum().replace(0,1e-8)
    df['PDI_A'] = df['DMP_RAW'].rolling(6).sum() * 100 / tr_sum6
    df['MDI_A'] = df['DMM_RAW'].rolling(6).sum() * 100 / tr_sum6
    pdi_mdi6  = (df['PDI_A']+df['MDI_A']).replace(0,1e-8)
    df['ADX_A'] = (abs(df['PDI_A']-df['MDI_A'])/pdi_mdi6*100).rolling(6).mean()
    df['ADX_A_ACCEL'] = (df['ADX_A']>df['ADX_A'].shift(1)) & (df['ADX_A'].shift(1)>df['ADX_A'].shift(2))

    low_min   = df['Low'].rolling(9).min()
    high_max  = df['High'].rolling(9).max()
    denom_kdj = (high_max - low_min).replace(0,1e-8)
    df['RSV']  = (df['Close'] - low_min) / denom_kdj * 100
    df['KVAL'] = df['RSV'].ewm(alpha=1/3, adjust=False).mean()
    df['DVAL'] = df['KVAL'].ewm(alpha=1/3, adjust=False).mean()
    df['J_V']  = (3*df['KVAL']) - (2*df['DVAL'])
    df['GIRO_J']   = df['J_V'] > df['J_V'].shift(1)
    df['CROSS_KD'] = (df['KVAL']>df['DVAL']) & (df['KVAL'].shift(1)<=df['DVAL'].shift(1))

    df['DIF']   = df['Close'].ewm(span=12,adjust=False).mean() - df['Close'].ewm(span=26,adjust=False).mean()
    df['DEA']   = df['DIF'].ewm(span=9,adjust=False).mean()
    df['HISTO'] = df['DIF'] - df['DEA']
    df['GIRO_MACD']      = (df['HISTO']>df['HISTO'].shift(1)) & (df['HISTO'].shift(1)<=df['HISTO'].shift(2))
    df['MACD_GIRO_NEG']  = (df['HISTO']<0) & (df['HISTO']<df['HISTO'].shift(1)) & (df['HISTO'].shift(1)<df['HISTO'].shift(2))
    df['MACD_CONV_ALCI'] = (df['HISTO']<0) & (df['HISTO']>df['HISTO'].shift(1)) & (df['HISTO']>df['HISTO'].shift(2))
    df['TENDENCIA_VIVA'] = (
        ((df['DIF']>0) | df['MACD_CONV_ALCI']) &
        df['MA20_UP'] & (df['PDI']>df['MDI']) & (df['Close']>df['MA50'])
    )

    df['OSC'] = calcular_rsi(df['Close'], periodo=14)

    df['BB_MID'] = df['Close'].rolling(20).mean()
    df['BB_STD'] = df['Close'].rolling(20).std(ddof=0)
    df['BB_DN']  = df['BB_MID'] - (2*df['BB_STD'])
    df['VOL_MA'] = df['Volume'].rolling(20).mean()

    df['S_PULL'] = (
        (df['Low']<df['MA50']*1.015) & (df['Close']>df['MA50']*0.985) &
        df['GIRO_J'] & (df['Volume']>df['VOL_MA']*1.05) & df['FILTRO_BASE']
    )
    df['S_IMPU'] = (
        (df['Close']>df['High'].shift(1).rolling(5).max()) &
        (df['ADX_V']>df['ADX_REQ']) & df['MA20_UP'] &
        df['GIRO_J'] & (df['Volume']>df['VOL_MA']*1.05)
    )
    df['S_BOLL'] = (
        (df['Low'].shift(1)<=df['BB_DN']) & (df['Close']>df['BB_DN']) &
        df['GIRO_J'] & df['GIRO_MACD'] &
        (df['Volume']>df['VOL_MA']*1.05) & df['FILTRO_BASE']
    )
    df['S_SUELO'] = (
        (df['OSC']<32) & (df['J_V']<22) &
        (df['Low'].shift(1)<=df['BB_DN']) & (df['Close']>df['BB_DN']) &
        (df['Close']>df['Low'].shift(1)) & df['GIRO_MACD'] &
        (df['Volume']>df['VOL_MA']*0.9)
    )
    df['CROSS_MACD'] = (df['DIF']>df['DEA']) & (df['DIF'].shift(1)<=df['DEA'].shift(1))
    df['S_MACD_CROSS'] = (
        df['CROSS_MACD'] & (df['DIF']<0) & (df['HISTO']>df['HISTO'].shift(1)) &
        (df['Close']>df['MA20']) & df['MA20_UP'] &
        (df['Volume']>df['VOL_MA']*1.05) & df['FILTRO_BASE']
    )
    df['S_EARLY'] = (
        (df['OSC']<38) & (df['J_V']<30) & df['CROSS_KD'] &
        (df['Close']>df['Close'].shift(1)) & df['MA20_UP'] &
        (df['Volume']>df['VOL_MA']*0.9) & df['FILTRO_BASE']
    )
    df['S_REBOTE_MA50'] = (
        (df['Low']<=df['MA50']*1.008) & (df['Close']>df['MA50']) &
        (df['Close']>df['BB_DN']) & (df['Close']<df['BB_MID']) &
        df['GIRO_J'] & df['MA20_UP'] & df['F_ALCISTA'] &
        (df['Volume']>df['VOL_MA']*0.95)
    )
    df['S_REBOTE_MA200'] = (
        (df['Low']<=df['MA200']*1.01) & (df['Close']>df['MA200']) &
        (df['Close']>df['Low'].shift(1)) & df['GIRO_J'] & df['MA20_UP'] &
        (df['Volume']>df['VOL_MA']*0.95)
    )
    df['S_BOLL_SOFT'] = (
        (df['Low'].shift(1)<=df['BB_DN']) & (df['Close']>df['BB_DN']) &
        (df['Close']>df['Low'].shift(1)) & df['GIRO_J'] &
        (df['Volume']>df['VOL_MA']*0.9) & df['FILTRO_BASE'] &
        ~df['MACD_GIRO_NEG']
    )

    is_bc  = df['BANDA'] == "BC"
    is_vol = df['BANDA'] == "VOL"
    s_bc_valid = (
        df['S_PULL']|df['S_IMPU']|df['S_BOLL']|df['S_SUELO']|
        df['S_MACD_CROSS']|df['S_EARLY']|
        df['S_REBOTE_MA50']|df['S_REBOTE_MA200']|df['S_BOLL_SOFT']
    )
    s_vol_valid = (
        df['S_IMPU']|df['S_BOLL']|df['S_SUELO']|
        df['S_MACD_CROSS']|df['S_EARLY']|
        df['S_REBOTE_MA200']|df['S_BOLL_SOFT']
    )
    df['B_RAW']    = (is_bc & s_bc_valid) | (is_vol & s_vol_valid)
    df['B_SIGNAL'] = df['B_RAW'] & ~df['B_RAW'].shift(1).fillna(False)

    b_raw_list = df['B_RAW'].tolist()
    dias_activa = 0
    for val in reversed(b_raw_list[-5:]):
        if val: dias_activa += 1
        else:   break

    b_signal_list = df['B_SIGNAL'].tolist()
    duracion, e_price, atr_entry, fecha_entrada = 0, None, None, None
    for i in range(len(b_signal_list)-1, -1, -1):
        if b_signal_list[i]:
            duracion     = len(b_signal_list) - 1 - i
            e_price      = float(df['Close'].iloc[i])
            atr_entry    = float(df['ATR_V'].iloc[i])
            fecha_entrada = df.index[i].strftime('%Y-%m-%d')
            break

    precio  = float(df['Close'].iloc[-1])
    banda   = df['BANDA'].iloc[-1]
    tp_mult = 1.6 if banda == "BC" else 2.2

    # TP1 y SL calculados desde la VELA GATILLO
    if e_price and atr_entry:
        tp1_nivel = e_price + atr_entry * tp_mult
        sl_nivel  = e_price * 0.97
        # Cuanto falta para TP1 desde precio actual
        pct_falta_tp1 = (tp1_nivel - precio) / precio * 100
        # Distancia del precio actual al SL
        pct_dist_sl   = (precio - sl_nivel) / precio * 100
        tp1_str  = f"${tp1_nivel:.2f}"
        sl_str   = f"${sl_nivel:.2f}"
        falta_str = f"{pct_falta_tp1:+.1f}%" if pct_falta_tp1 >= 0 else f"✅ {abs(pct_falta_tp1):.1f}% superado"
        sl_dist_str = f"{pct_dist_sl:.1f}%"
    else:
        tp1_str = sl_str = falta_str = sl_dist_str = "—"
        tp1_nivel = sl_nivel = precio
        pct_falta_tp1 = 0

    i = len(df) - 1
    add_bc = (
        dias_activa > 0 and banda == "BC" and
        df['PDI_A'].iloc[i] > df['MDI_A'].iloc[i] and
        df['ADX_A'].iloc[i] > 28 and bool(df['ADX_A_ACCEL'].iloc[i]) and
        bool(df['CROSS_KD'].iloc[i]) and df['KVAL'].iloc[i] < 75 and
        df['Close'].iloc[i] > df['MA20'].iloc[i] and
        df['Volume'].iloc[i] > df['VOL_MA'].iloc[i] * 1.2
    )
    add_vol = (
        dias_activa > 0 and banda == "VOL" and
        df['PDI_A'].iloc[i] > df['MDI_A'].iloc[i] and
        df['ADX_A'].iloc[i] > 32 and bool(df['ADX_A_ACCEL'].iloc[i]) and
        df['Close'].iloc[i] > df['High'].iloc[max(0,i-3):i].max() and
        df['Close'].iloc[i] > df['MA20'].iloc[i] and
        df['Volume'].iloc[i] > df['VOL_MA'].iloc[i] * 1.4
    )
    add_senal = "ADD-BC" if add_bc else ("ADD-VOL" if add_vol else None)

    gatillos = []
    if dias_activa > 0:
        for nombre, col in [
            ("S_PULL","S_PULL"),("S_IMPU","S_IMPU"),("S_BOLL","S_BOLL"),
            ("S_SUELO","S_SUELO"),("S_MACD_CROSS","S_MACD_CROSS"),
            ("S_EARLY","S_EARLY"),("S_REBOTE_MA50","S_REBOTE_MA50"),
            ("S_REBOTE_MA200","S_REBOTE_MA200"),("S_BOLL_SOFT","S_BOLL_SOFT"),
        ]:
            if df[col].iloc[-1]: gatillos.append(nombre)
    if add_senal:
        gatillos.append(f"⚡{add_senal}")

    df['OJO'] = (
        (df['OSC']<35) & (df['J_V']<28) & (df['Close']<=df['BB_DN']*1.01)
    ).fillna(False)
    df['CRUCE_J'] = (
        (df['J_V']>10) & (df['J_V'].shift(1).fillna(100)<=12)
    ).fillna(False)
    df['BTD'] = (
        df['OJO'].shift(1).fillna(False) & df['CRUCE_J'] & df['GIRO_MACD'].fillna(False)
    ).fillna(False)

    rsi_val = float(df['OSC'].iloc[-1])  if not pd.isna(df['OSC'].iloc[-1])  else 50.0
    adx_val = float(df['ADX_V'].iloc[-1]) if not pd.isna(df['ADX_V'].iloc[-1]) else 0.0
    jv_val  = float(df['J_V'].iloc[-1])  if not pd.isna(df['J_V'].iloc[-1])  else 50.0
    bdn_val = float(df['BB_DN'].iloc[-1]) if not pd.isna(df['BB_DN'].iloc[-1]) else 0.0

    return {
        "Ticker":        ticker_name,
        "Fecha":         ultima_fecha,
        "F.Entrada":     fecha_entrada or "—",
        "Banda":         banda,
        "Precio":        f"${precio:.2f}",
        "precio_raw":    precio,
        "RSI":           f"{rsi_val:.1f}",
        "rsi_raw":       rsi_val,
        "ADX":           f"{adx_val:.1f}",
        "J(V)":          f"{jv_val:.1f}",
        "BB_DN":         f"${bdn_val:.2f}",
        "Días":          dias_activa,
        "Duracion":      duracion,
        "Gatillos":      ", ".join(gatillos) if gatillos else "—",
        "TP1":           tp1_str,
        "Falta %TP1":    falta_str,
        "SL (−3%)":      sl_str,
        "Dist. SL":      sl_dist_str,
        "Radar_OJO":     bool(df['OJO'].iloc[-2:].any()),
        "Radar_BTD":     bool(df['BTD'].iloc[-2:].any()),
        "Add_Senal":     add_senal,
        "pct_falta_raw": pct_falta_tp1,
    }, None

# ======================================================================
# EXPORTAR EXCEL
# ======================================================================
def exportar_excel(dfs_dict):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        for nombre, df in dfs_dict.items():
            if df is not None and not df.empty:
                df.to_excel(writer, sheet_name=nombre[:31], index=False)
    return buffer.getvalue()

# ======================================================================
# SIDEBAR — SIMPLIFICADO
# ======================================================================
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    st.markdown("---")
    periodo    = st.selectbox("Período histórico", ["2y","1y","6mo"], index=0)
    rsi_umbral = st.slider("Umbral RSI sobreventa", 25, 45, 33)
    dias_max   = st.slider("Señal activa máx. días", 1, 5, 3)
    usar_gex   = st.toggle(
        "Put/Call Wall GEX (próximas 5 semanas)",
        value=True,
        help="5 series de vencimientos de opciones. Solo acciones USA. Aumenta el tiempo de ejecución."
    )
    st.markdown("---")
    ejecutar = st.button("▶ Ejecutar escáner", use_container_width=True, type="primary")
    st.markdown('<p style="color:#334155;font-size:11px;text-align:center;margin-top:8px;">SG6 · v16.0 · Solo fines educativos</p>', unsafe_allow_html=True)

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
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.info("**9 Gatillos de entrada**\n\nS_PULL · S_IMPU · S_BOLL · S_SUELO · S_MACD_CROSS · S_EARLY · S_REBOTE_MA50 · S_REBOTE_MA200 · S_BOLL_SOFT")
    with col_b:
        st.info("**ADD automático ⚡**\n\nDetecta señales ADD-BC y ADD-VOL sobre posiciones abiertas y las muestra en la columna Gatillos")
    with col_c:
        st.info("**GEX Put/Call Wall · 5 semanas**\n\n🟢 Zona favorable · 🟠 Cerca techo · 🔴 Techo activo · 🟡 Piso gamma")
    st.stop()

tickers = TICKERS_DEFAULT

# ======================================================================
# EJECUCION
# ======================================================================
lista_compras, lista_rsi, lista_radar, lista_desc = [], [], [], []
progreso = st.progress(0, text="Iniciando escáner...")
col1, col2, col3 = st.columns(3)
m_compras = col1.empty()
m_rsi     = col2.empty()
m_radar   = col3.empty()

for idx, ticker in enumerate(tickers):
    pct = int((idx+1)/len(tickers)*100)
    progreso.progress(pct, text=f"Analizando {ticker}  ({idx+1}/{len(tickers)})")
    m_compras.metric("🚀 Compras + ADD", len(lista_compras))
    m_rsi.metric(f"📉 RSI < {rsi_umbral}", len(lista_rsi))
    m_radar.metric("🎯 Radar OJO/BTD", len(lista_radar))

    datos, motivo = analizar_ticker(ticker, periodo)
    if datos is None:
        lista_desc.append({"Ticker": ticker, "Motivo": motivo})
        continue

    gex = None
    if usar_gex and not any(x in ticker for x in ['-USD','ETH','BTC','SOL']):
        gex = calcular_gex(ticker, datos["precio_raw"])
    put_wall  = gex["Put Wall"]  if gex else "—"
    call_wall = gex["Call Wall"] if gex else "—"
    gex_ctx   = gex["GEX"]       if gex else "—"

    es_compra = 0 < datos["Días"] <= dias_max
    es_add    = datos["Add_Senal"] is not None

    if es_compra or es_add:
        estado_str = (
            "Día 1" if datos["Días"] == 1
            else f"Activa {datos['Días']}d" if datos["Días"] > 0
            else f"Abierta {datos['Duracion']}d"
        )
        lista_compras.append({
            "Ticker":      datos["Ticker"],
            "F.Entrada":   datos["F.Entrada"],
            "Banda":       datos["Banda"],
            "Antigüedad":  estado_str,
            "Gatillos":    datos["Gatillos"],
            "Precio":      datos["Precio"],
            "RSI":         datos["RSI"],
            "ADX":         datos["ADX"],
            "TP1":         datos["TP1"],
            "Falta %TP1":  datos["Falta %TP1"],
            "SL (−3%)":    datos["SL (−3%)"],
            "Dist. SL":    datos["Dist. SL"],
            "Put Wall":    put_wall,
            "Call Wall":   call_wall,
            "GEX":         gex_ctx,
        })

    if datos["rsi_raw"] < rsi_umbral:
        lista_rsi.append({
            "Ticker":    datos["Ticker"],
            "Fecha":     datos["Fecha"],
            "Banda":     datos["Banda"],
            "Precio":    datos["Precio"],
            "RSI":       datos["RSI"],
            "J(V)":      datos["J(V)"],
            "ADX":       datos["ADX"],
            "Put Wall":  put_wall,
            "Call Wall": call_wall,
            "GEX":       gex_ctx,
        })

    if datos["Radar_BTD"]:
        lista_radar.append({
            "Ticker":    datos["Ticker"],
            "Señal":     "🟢 BTD",
            "Banda":     datos["Banda"],
            "Precio":    datos["Precio"],
            "RSI":       datos["RSI"],
            "J(V)":      datos["J(V)"],
            "BB_DN":     datos["BB_DN"],
            "Put Wall":  put_wall,
            "Call Wall": call_wall,
            "GEX":       gex_ctx,
        })
    elif datos["Radar_OJO"]:
        lista_radar.append({
            "Ticker":    datos["Ticker"],
            "Señal":     "🟡 OJO",
            "Banda":     datos["Banda"],
            "Precio":    datos["Precio"],
            "RSI":       datos["RSI"],
            "J(V)":      datos["J(V)"],
            "BB_DN":     datos["BB_DN"],
            "Put Wall":  put_wall,
            "Call Wall": call_wall,
            "GEX":       gex_ctx,
        })

progreso.empty()
st.success(f"✅ Escáner completado — {len(tickers)} tickers procesados")
m_compras.metric("🚀 Compras + ADD", len(lista_compras))
m_rsi.metric(f"📉 RSI < {rsi_umbral}", len(lista_rsi))
m_radar.metric("🎯 Radar OJO/BTD", len(lista_radar))

# ======================================================================
# HELPERS DE ESTILO
# ======================================================================
def colorear_banda(v):
    if v == "BC":  return "background-color:#064e3b;color:#34d399;font-weight:600"
    if v == "VOL": return "background-color:#451a03;color:#fb923c;font-weight:600"
    return ""

def colorear_rsi(v):
    try:
        r = float(str(v))
        if r < 33: return "color:#f87171;font-weight:600"
        if r > 65: return "color:#34d399;font-weight:600"
    except Exception:
        pass
    return "color:#94a3b8"

def colorear_falta(v):
    try:
        if "superado" in str(v): return "color:#34d399;font-weight:600"
        r = float(str(v).replace('%','').replace('+',''))
        if r <= 2:  return "color:#34d399;font-weight:600"
        if r <= 5:  return "color:#fbbf24;font-weight:600"
    except Exception:
        pass
    return "color:#94a3b8"

def colorear_sl(v):
    try:
        r = float(str(v).replace('%',''))
        if r < 1:  return "color:#f87171;font-weight:600"
        if r < 2:  return "color:#fbbf24;font-weight:600"
    except Exception:
        pass
    return "color:#94a3b8"

# ======================================================================
# TABS
# ======================================================================
tab1, tab2, tab3 = st.tabs([
    f"🚀 Compras + ADD  ({len(lista_compras)})",
    f"📉 Sobreventa RSI  ({len(lista_rsi)})",
    f"🎯 Radar OJO / BTD  ({len(lista_radar)})",
])

with tab1:
    st.markdown("#### Señales activas — compras frescas y ADD")
    st.caption("TP1 y SL calculados desde la vela gatillo · ⚡ = señal ADD · Falta %TP1 = distancia al objetivo · Dist. SL = margen antes del stop")
    if lista_compras:
        df1 = pd.DataFrame(lista_compras)
        df1['_ord'] = df1['Gatillos'].apply(lambda x: 1 if '⚡' in str(x) and not any(
            g in str(x) for g in ['S_PULL','S_IMPU','S_BOLL','S_SUELO','S_MACD','S_EARLY','S_REBOTE','SOFT']
        ) else 0)
        df1 = df1.sort_values('_ord').drop(columns='_ord').reset_index(drop=True)
        df1.index = range(1, len(df1)+1)
        styled = df1.style\
            .map(colorear_banda,  subset=["Banda"])\
            .map(colorear_rsi,    subset=["RSI"])\
            .map(colorear_falta,  subset=["Falta %TP1"])\
            .map(colorear_sl,     subset=["Dist. SL"])
        st.dataframe(styled, use_container_width=True)
        c1, c2 = st.columns([1,4])
        with c1:
            st.download_button("⬇️ Excel", exportar_excel({"Compras": df1.reset_index(drop=True)}),
                               "compras_sg6.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with c2:
            st.download_button("⬇️ CSV", df1.to_csv(index=False).encode("utf-8"), "compras_sg6.csv", "text/csv")
    else:
        st.info("Ninguna compra fresca ni ADD activo hoy.")

with tab2:
    st.markdown(f"#### Activos con RSI < {rsi_umbral}")
    if lista_rsi:
        df2 = pd.DataFrame(lista_rsi).sort_values("RSI").reset_index(drop=True)
        df2.index = range(1, len(df2)+1)
        styled2 = df2.style\
            .map(colorear_banda, subset=["Banda"])\
            .map(colorear_rsi,   subset=["RSI"])
        st.dataframe(styled2, use_container_width=True)
        c1, c2 = st.columns([1,4])
        with c1:
            st.download_button("⬇️ Excel", exportar_excel({"Sobreventa": df2.reset_index(drop=True)}),
                               "sobreventa_sg6.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with c2:
            st.download_button("⬇️ CSV", df2.to_csv(index=False).encode("utf-8"), "sobreventa_sg6.csv", "text/csv")
    else:
        st.info("Ningún activo en sobreventa extrema hoy.")

with tab3:
    st.markdown("#### Radar temprano — formación de suelo")
    if lista_radar:
        df3 = pd.DataFrame(lista_radar)
        df3["_ord"] = df3["Señal"].apply(lambda x: 0 if "BTD" in x else 1)
        df3 = df3.sort_values(["_ord","RSI"]).drop(columns="_ord").reset_index(drop=True)
        df3.index = range(1, len(df3)+1)
        styled3 = df3.style\
            .map(colorear_banda, subset=["Banda"])\
            .map(colorear_rsi,   subset=["RSI"])
        st.dataframe(styled3, use_container_width=True)
        c1, c2 = st.columns([1,4])
        with c1:
            st.download_button("⬇️ Excel", exportar_excel({"Radar": df3.reset_index(drop=True)}),
                               "radar_sg6.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with c2:
            st.download_button("⬇️ CSV", df3.to_csv(index=False).encode("utf-8"), "radar_sg6.csv", "text/csv")
    else:
        st.info("Sin alertas tempranas de formación de suelo.")

if lista_desc:
    with st.expander(f"⚠️ Tickers descartados ({len(lista_desc)})", expanded=False):
        st.dataframe(pd.DataFrame(lista_desc), use_container_width=True, hide_index=True)

st.markdown('<p class="footer-cap">SG6 Screener · Sistema KW-DNA · RSI Wilder · GEX 5 series · Solo con fines educativos · No es asesoría financiera</p>', unsafe_allow_html=True)
