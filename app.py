# ======================================================================
# SG4 SCREENER — APP STREAMLIT V12 (RSI WILDER + ADD + RADAR EXACTO)
# ======================================================================
# - RSI Wilder (original, como en V10)
# - Radar OJO/BTD con umbrales exactos del Pine
# - Nueva pestaña ADD (señales de aumento)
# - 9 gatillos de entrada originales
# ======================================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ======================================================================
# CONFIGURACION
# ======================================================================
st.set_page_config(
    page_title="SG4 Screener",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================================================
# WATCHLIST BASE (la misma de siempre)
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
# RSI WILDER (exactamente como en tu V10)
# ======================================================================
def calcular_rsi_wilder(close_series, periodo=14):
    close = close_series.copy().reset_index(drop=True)
    n = len(close)
    delta = close.diff()
    gain = delta.clip(lower=0).fillna(0)
    loss = (-delta).clip(lower=0).fillna(0)
    avg_gain = np.zeros(n)
    avg_loss = np.zeros(n)
    if n > periodo:
        avg_gain[periodo] = gain.iloc[1:periodo + 1].mean()
        avg_loss[periodo] = loss.iloc[1:periodo + 1].mean()
        for i in range(periodo + 1, n):
            avg_gain[i] = (avg_gain[i-1] * (periodo-1) + gain.iloc[i]) / periodo
            avg_loss[i] = (avg_loss[i-1] * (periodo-1) + loss.iloc[i]) / periodo
    avg_loss_safe = np.where(avg_loss == 0, 1e-8, avg_loss)
    rs = avg_gain / avg_loss_safe
    rsi = 100 - (100 / (1 + rs))
    rsi[:periodo] = np.nan
    return pd.Series(rsi, index=close_series.index)

# ======================================================================
# ANALISIS POR TICKER (con RSI Wilder, ADD y radar exacto)
# ======================================================================
def analizar_ticker(df, ticker_name):
    df = df.dropna(subset=['Close', 'Volume'])
    df = df[df['Volume'] > 0].copy()
    if len(df) < 250:
        return None, f"Pocas velas: {len(df)}"

    ultima_fecha = df.index[-1].strftime('%Y-%m-%d')

    # BANDA
    df['RET_V']    = df['Close'].pct_change() * 100
    df['BETA_RAW'] = df['RET_V'].rolling(60).std(ddof=0)
    df['BETA_S']   = df['BETA_RAW'].rolling(20).mean()
    df['BANDA']    = np.where(df['BETA_S'] < 1.4, "BC", "VOL")

    # MEDIAS
    df['MA20']  = df['Close'].ewm(span=20,  adjust=False).mean()
    df['MA50']  = df['Close'].ewm(span=50,  adjust=False).mean()
    df['MA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    df['F_BAJISTA']   = df['Close'] < df['MA200']
    df['F_ALCISTA']   = df['Close'] > df['MA200']
    df['MA20_UP']     = df['MA20'] > df['MA20'].shift(1)
    df['FILTRO_BASE'] = df['Close'] >= df['MA200']

    # ATR
    df['H_L']  = df['High'] - df['Low']
    df['H_PC'] = (df['High'] - df['Close'].shift(1)).abs()
    df['L_PC'] = (df['Low']  - df['Close'].shift(1)).abs()
    df['TR_V'] = df[['H_L', 'H_PC', 'L_PC']].max(axis=1)
    df['ATR_V'] = df['TR_V'].rolling(14).mean()

    # ADX
    df['HD'] = df['High'] - df['High'].shift(1)
    df['LD'] = df['Low'].shift(1) - df['Low']
    df['DMP_RAW'] = np.where((df['HD'] > 0) & (df['HD'] > df['LD']), df['HD'], 0)
    df['DMM_RAW'] = np.where((df['LD'] > 0) & (df['LD'] > df['HD']), df['LD'], 0)
    tr_sum = df['TR_V'].rolling(14).sum().replace(0, 1e-8)
    df['PDI'] = df['DMP_RAW'].rolling(14).sum() * 100 / tr_sum
    df['MDI'] = df['DMM_RAW'].rolling(14).sum() * 100 / tr_sum
    pdi_mdi_sum = (df['PDI'] + df['MDI']).replace(0, 1e-8)
    df['ADX_V']   = (abs(df['PDI'] - df['MDI']) / pdi_mdi_sum * 100).rolling(9).mean()
    df['ADX_REQ'] = np.where(df['F_BAJISTA'], 28, 20)

    # KDJ
    low_min   = df['Low'].rolling(9).min()
    high_max  = df['High'].rolling(9).max()
    denom_kdj = (high_max - low_min).replace(0, 1e-8)
    df['RSV']  = (df['Close'] - low_min) / denom_kdj * 100
    df['KVAL'] = df['RSV'].ewm(alpha=1/3, adjust=False).mean()
    df['DVAL'] = df['KVAL'].ewm(alpha=1/3, adjust=False).mean()
    df['J_V']  = (3 * df['KVAL']) - (2 * df['DVAL'])
    df['GIRO_J'] = df['J_V'] > df['J_V'].shift(1)
    df['CROSS_KD'] = (df['KVAL'] > df['DVAL']) & (df['KVAL'].shift(1) <= df['DVAL'].shift(1))

    # MACD
    df['DIF']   = (df['Close'].ewm(span=12, adjust=False).mean()
                 - df['Close'].ewm(span=26, adjust=False).mean())
    df['DEA']   = df['DIF'].ewm(span=9, adjust=False).mean()
    df['HISTO'] = df['DIF'] - df['DEA']
    df['GIRO_MACD'] = (
        (df['HISTO'] > df['HISTO'].shift(1)) &
        (df['HISTO'].shift(1) <= df['HISTO'].shift(2))
    )
    df['CROSS_MACD'] = (df['DIF'] > df['DEA']) & (df['DIF'].shift(1) <= df['DEA'].shift(1))

    # RSI WILDER (original)
    df['OSC'] = calcular_rsi_wilder(df['Close'], periodo=14)

    # BOLLINGER Y VOLUMEN
    df['BB_MID'] = df['Close'].rolling(20).mean()
    df['BB_STD'] = df['Close'].rolling(20).std(ddof=0)
    df['BB_DN']  = df['BB_MID'] - (2 * df['BB_STD'])
    df['VOL_MA'] = df['Volume'].rolling(20).mean()
    df['VOL_OK']    = df['Volume'] > df['VOL_MA'] * 1.05
    df['VOL_MED']   = df['Volume'] > df['VOL_MA'] * 1.20
    df['VOL_ALT']   = df['Volume'] > df['VOL_MA'] * 1.40
    df['VOL_RELAX'] = df['Volume'] > df['VOL_MA'] * 0.95
    df['VOL_SOFT']  = df['Volume'] > df['VOL_MA'] * 0.90

    # ========== GATILLOS (exactamente igual a V10) ==========
    df['S_PULL'] = (
        (df['Low'] < df['MA50'] * 1.015) & (df['Close'] > df['MA50'] * 0.985) &
        df['GIRO_J'] & df['VOL_OK'] & df['FILTRO_BASE']
    )
    df['S_IMPU'] = (
        (df['Close'] > df['High'].shift(1).rolling(5).max()) &
        (df['ADX_V'] > df['ADX_REQ']) & df['MA20_UP'] &
        df['GIRO_J'] & df['VOL_OK']
    )
    df['S_BOLL'] = (
        (df['Low'].shift(1) <= df['BB_DN']) & (df['Close'] > df['BB_DN']) &
        df['GIRO_J'] & df['GIRO_MACD'] &
        df['VOL_OK'] & df['FILTRO_BASE']
    )
    df['S_SUELO'] = (
        (df['OSC'] < 32) & (df['J_V'] < 22) &
        (df['Low'].shift(1) <= df['BB_DN']) & (df['Close'] > df['BB_DN']) &
        (df['Close'] > df['Low'].shift(1)) & df['GIRO_MACD'] &
        df['VOL_SOFT']
    )
    df['S_MACD_CROSS'] = (
        df['CROSS_MACD'] & (df['DIF'] < 0) & (df['HISTO'] > df['HISTO'].shift(1)) &
        (df['Close'] > df['MA20']) & df['MA20_UP'] &
        df['VOL_OK'] & df['FILTRO_BASE']
    )
    df['S_EARLY'] = (
        (df['OSC'] < 38) & (df['J_V'] < 30) & df['CROSS_KD'] &
        (df['Close'] > df['Close'].shift(1)) & df['MA20_UP'] &
        df['VOL_SOFT'] & df['FILTRO_BASE']
    )
    df['S_REBOTE_MA50'] = (
        (df['Low'] <= df['MA50'] * 1.008) & (df['Close'] > df['MA50']) &
        (df['Close'] > df['BB_DN']) & (df['Close'] < df['BB_MID']) &
        df['GIRO_J'] & df['MA20_UP'] & df['F_ALCISTA'] & df['VOL_RELAX']
    )
    df['S_REBOTE_MA200'] = (
        (df['Low'] <= df['MA200'] * 1.01) & (df['Close'] > df['MA200']) &
        (df['Close'] > df['Low'].shift(1)) & df['GIRO_J'] &
        df['MA20_UP'] & df['VOL_RELAX']
    )
    df['S_BOLL_SOFT'] = (
        (df['Low'].shift(1) <= df['BB_DN']) & (df['Close'] > df['BB_DN']) &
        (df['Close'] > df['Low'].shift(1)) & df['GIRO_J'] &
        df['VOL_SOFT'] & df['FILTRO_BASE']
    )

    # Lógica B_RAW
    is_bc  = df['BANDA'] == "BC"
    is_vol = df['BANDA'] == "VOL"
    s_bc_valid = (
        df['S_PULL'] | df['S_IMPU'] | df['S_BOLL'] | df['S_SUELO'] |
        df['S_MACD_CROSS'] | df['S_EARLY'] |
        df['S_REBOTE_MA50'] | df['S_REBOTE_MA200'] | df['S_BOLL_SOFT']
    )
    s_vol_valid = (
        df['S_IMPU'] | df['S_BOLL'] | df['S_SUELO'] |
        df['S_MACD_CROSS'] | df['S_EARLY'] |
        df['S_REBOTE_MA200'] | df['S_BOLL_SOFT']
    )
    df['B_RAW'] = (is_bc & s_bc_valid) | (is_vol & s_vol_valid)

    # Días consecutivos activa
    b_raw_list = df['B_RAW'].tolist()
    dias_activa = 0
    for val in reversed(b_raw_list[-5:]):
        if val: dias_activa += 1
        else: break

    # Gatillos activos hoy
    gatillos = []
    if dias_activa > 0:
        for nombre, col in [
            ("S_PULL","S_PULL"),("S_IMPU","S_IMPU"),("S_BOLL","S_BOLL"),
            ("S_SUELO","S_SUELO"),("S_MACD_CROSS","S_MACD_CROSS"),
            ("S_EARLY","S_EARLY"),("S_REBOTE_MA50","S_REBOTE_MA50"),
            ("S_REBOTE_MA200","S_REBOTE_MA200"),("S_BOLL_SOFT","S_BOLL_SOFT")
        ]:
            if df[col].iloc[-1]: gatillos.append(nombre)

    tp_mult = 1.6 if df['BANDA'].iloc[-1] == "BC" else 2.2
    tp_ideal = df['Close'].iloc[-1] + (df['ATR_V'].iloc[-1] * tp_mult)

    # ========== RADAR EXACTO (Pine) ==========
    df['OJO'] = (df['OSC'] < 32) & (df['J_V'] < 25) & (df['Close'] < df['BB_DN'])
    df['CRUCE_J'] = (df['J_V'] > 10) & (df['J_V'].shift(1) <= 10)
    df['BTD'] = df['OJO'].shift(1) & df['CRUCE_J'] & df['GIRO_MACD']
    ojo_reciente = bool(df['OJO'].iloc[-2:].any())
    btd_reciente = bool(df['BTD'].iloc[-2:].any())

    # ========== ADD (aumento) ==========
    dmp_a = df['DMP_RAW'].rolling(6).sum()
    dmm_a = df['DMM_RAW'].rolling(6).sum()
    tr6 = df['TR_V'].rolling(6).sum().replace(0, 1e-8)
    pdi_a = dmp_a * 100 / tr6
    mdi_a = dmm_a * 100 / tr6
    adx_a = (abs(pdi_a - mdi_a) / (pdi_a + mdi_a).replace(0, 1e-8) * 100).rolling(6).mean()
    adx_a_accel = (adx_a > adx_a.shift(1)) & (adx_a.shift(1) > adx_a.shift(2))

    add_bc = (
        (df['BANDA'] == "BC") & (pdi_a > mdi_a) & (adx_a > 28) & adx_a_accel &
        df['CROSS_KD'] & (df['KVAL'] < 75) & (df['Close'] > df['MA20']) & df['VOL_MED']
    )
    max_high_3 = df['High'].rolling(3).max().shift(1)
    add_vol = (
        (df['BANDA'] == "VOL") & (pdi_a > mdi_a) & (adx_a > 32) & adx_a_accel &
        (df['Close'] > max_high_3) & (df['Close'] > df['MA20']) & df['VOL_ALT']
    )
    df['ADD'] = add_bc | add_vol
    add_hoy = bool(df['ADD'].iloc[-1])

    return {
        "Ticker": ticker_name, "Fecha": ultima_fecha, "Banda": df['BANDA'].iloc[-1],
        "Precio": round(float(df['Close'].iloc[-1]), 2),
        "RSI": round(float(df['OSC'].iloc[-1]), 2),
        "ADX": round(float(df['ADX_V'].iloc[-1]), 2),
        "J_V": round(float(df['J_V'].iloc[-1]), 2),
        "BB_DN": round(float(df['BB_DN'].iloc[-1]), 2),
        "Dias_Activa": dias_activa, "Gatillos": ", ".join(gatillos) if gatillos else "—",
        "TP1": round(float(tp_ideal), 2),
        "Radar_OJO": ojo_reciente, "Radar_BTD": btd_reciente,
        "ADD": add_hoy, "ADX_A": round(float(adx_a.iloc[-1]), 2),
        "KVAL": round(float(df['KVAL'].iloc[-1]), 2),
        "Volumen_MA": round(float(df['VOL_MA'].iloc[-1]), 0),
        "Volumen": round(float(df['Volume'].iloc[-1]), 0),
    }, None

# ======================================================================
# SIDEBAR Y MAIN (igual que antes, con 4 pestañas)
# ======================================================================
with st.sidebar:
    st.title("Configuracion SG4")
    periodo = st.selectbox("Periodo historico", ["2y","1y","6mo"], index=0)
    rsi_umbral = st.slider("Umbral RSI sobreventa", 25, 45, 33)
    dias_max = st.slider("Señal activa max. dias", 1, 5, 3)
    st.markdown("---")
    st.markdown("**Watchlist personalizada**")
    tickers_input = st.text_area("Un ticker por linea o separado por comas", height=140, placeholder="AAPL\nNVDA\nTSLA")
    st.markdown("---")
    st.caption("SG4 v12 · RSI Wilder · ADD · Radar exacto")
    ejecutar = st.button("🚀 Ejecutar escaner", use_container_width=True, type="primary")

st.title("📊 SG4 — Santo Grial 4 · Screener")
st.caption("Sistema KW-DNA · RSI Wilder · ADD · Radar exacto · v12.0")

if not ejecutar:
    st.info("Configura los parametros en la barra lateral y presiona Ejecutar escaner.")
    with st.expander("📖 Gatillos del sistema SG4", expanded=False):
        st.markdown("""
| Gatillo | Descripcion | Banda | Vol min |
|---|---|---|---|
| S_PULL | Pullback a MA50 con rebote y KDJ girando | BC | 105% |
| S_IMPU | Ruptura de maximos con ADX fuerte | BC+VOL | 105% |
| S_BOLL | Rebote desde BB inferior + GIRO_MACD | BC+VOL | 105% |
| S_SUELO | RSI+KDJ sobreventa extrema + giro MACD | BC+VOL | 90% |
| S_MACD_CROSS | Cruce DIF/DEA bajo cero con momentum | BC+VOL | 105% |
| S_EARLY | Cruce KD en sobreventa anticipado | BC+VOL | 90% |
| S_REBOTE_MA50 | Rebote limpio en MA50, entre BB_DN y BB_MID | Solo BC | 95% |
| S_REBOTE_MA200 | Rebote en MA200, soporte dinamico principal | BC+VOL | 95% |
| S_BOLL_SOFT | Rebote BB inferior sin GIRO_MACD | BC+VOL | 90% |
| **ADD** | Aumento de posicion (ADX acelerado + cruce K/D + volumen alto) | BC/VOL | 120%/140% |
        """)
    st.stop()

# Watchlist
if tickers_input.strip():
    tickers = [t.strip().upper() for t in tickers_input.replace(',','\n').splitlines() if t.strip()]
    tickers = list(dict.fromkeys(tickers))
else:
    tickers = TICKERS_DEFAULT

# Ejecucion
lista_compras, lista_rsi, lista_radar, lista_add, lista_desc = [], [], [], [], []
progreso = st.progress(0, text="Iniciando...")
col1, col2, col3, col4 = st.columns(4)
m_compras = col1.empty()
m_rsi = col2.empty()
m_radar = col3.empty()
m_add = col4.empty()

for idx, ticker in enumerate(tickers):
    pct = int((idx + 1) / len(tickers) * 100)
    progreso.progress(pct, text=f"Procesando {ticker}... ({idx+1}/{len(tickers)})")
    m_compras.metric("🚀 Compras frescas", len(lista_compras))
    m_rsi.metric(f"📉 RSI < {rsi_umbral}", len(lista_rsi))
    m_radar.metric("🎯 Radar OJO/BTD", len(lista_radar))
    m_add.metric("➕ ADD", len(lista_add))

    try:
        df = yf.download(ticker, period=periodo, progress=False, auto_adjust=True)
        if df.empty:
            lista_desc.append({"Ticker": ticker, "Motivo": "Sin datos"})
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        datos, motivo = analizar_ticker(df, ticker)
        if datos is None:
            lista_desc.append({"Ticker": ticker, "Motivo": motivo})
            continue

        # Compras frescas
        if 0 < datos["Dias_Activa"] <= dias_max:
            lista_compras.append({
                "Ticker": datos["Ticker"], "Fecha": datos["Fecha"], "Banda": datos["Banda"],
                "Antiguedad": "Dia 1" if datos["Dias_Activa"]==1 else f"Activa {datos['Dias_Activa']}d",
                "Gatillos": datos["Gatillos"], "Precio": datos["Precio"],
                "RSI": datos["RSI"], "ADX": datos["ADX"], "TP1": datos["TP1"]
            })

        # Sobreventa
        if datos["RSI"] < rsi_umbral:
            lista_rsi.append({
                "Ticker": datos["Ticker"], "Fecha": datos["Fecha"], "Banda": datos["Banda"],
                "Precio": datos["Precio"], "RSI": datos["RSI"], "J_V": datos["J_V"], "ADX": datos["ADX"]
            })

        # Radar
        if datos["Radar_BTD"]:
            lista_radar.append({
                "Ticker": datos["Ticker"], "Senal": "🟢 BTD", "Banda": datos["Banda"],
                "Precio": datos["Precio"], "RSI": datos["RSI"], "J_V": datos["J_V"], "BB_DN": datos["BB_DN"]
            })
        elif datos["Radar_OJO"]:
            lista_radar.append({
                "Ticker": datos["Ticker"], "Senal": "🟡 OJO", "Banda": datos["Banda"],
                "Precio": datos["Precio"], "RSI": datos["RSI"], "J_V": datos["J_V"], "BB_DN": datos["BB_DN"]
            })

        # ADD
        if datos["ADD"]:
            lista_add.append({
                "Ticker": datos["Ticker"], "Banda": datos["Banda"], "Precio": datos["Precio"],
                "ADX_A": datos["ADX_A"], "KVAL": datos["KVAL"],
                "Volumen": datos["Volumen"], "Vol_MA": datos["Volumen_MA"], "RSI": datos["RSI"]
            })
    except Exception as e:
        lista_desc.append({"Ticker": ticker, "Motivo": str(e)[:80]})

progreso.empty()
st.success(f"✅ Escaner completado — {len(tickers)} tickers procesados")

# Mostrar 4 pestañas
tab1, tab2, tab3, tab4 = st.tabs([
    f"🚀 Compras frescas ({len(lista_compras)})",
    f"📉 Sobreventa RSI ({len(lista_rsi)})",
    f"🎯 Radar OJO/BTD ({len(lista_radar)})",
    f"➕ ADD ({len(lista_add)})"
])

with tab1:
    if lista_compras:
        df1 = pd.DataFrame(lista_compras).reset_index(drop=True)
        for c in ["Precio","RSI","ADX","TP1"]: df1[c] = df1[c].round(2)
        st.dataframe(df1.style.map(lambda v: "background-color:#1a3d2b" if v=="BC" else "background-color:#3d2e0a", subset=["Banda"]), use_container_width=True, hide_index=True)
        st.download_button("⬇️ CSV", df1.to_csv(index=False).encode("utf-8"), "compras_sg4_v12.csv")
    else: st.info("Ninguna compra fresca.")

with tab2:
    if lista_rsi:
        df2 = pd.DataFrame(lista_rsi).sort_values("RSI").reset_index(drop=True)
        for c in ["Precio","RSI","J_V","ADX"]: df2[c] = df2[c].round(2)
        st.dataframe(df2, use_container_width=True, hide_index=True)
        st.download_button("⬇️ CSV", df2.to_csv(index=False).encode("utf-8"), "sobreventa_sg4_v12.csv")
    else: st.info("Ningun activo en sobreventa.")

with tab3:
    if lista_radar:
        df3 = pd.DataFrame(lista_radar)
        df3["_ord"] = df3["Senal"].apply(lambda x: 0 if "BTD" in x else 1)
        df3 = df3.sort_values(["_ord","RSI"]).drop(columns="_ord").reset_index(drop=True)
        for c in ["Precio","RSI","J_V","BB_DN"]: df3[c] = df3[c].round(2)
        st.dataframe(df3, use_container_width=True, hide_index=True)
        st.download_button("⬇️ CSV", df3.to_csv(index=False).encode("utf-8"), "radar_sg4_v12.csv")
    else: st.info("Sin alertas de suelo.")

with tab4:
    if lista_add:
        df4 = pd.DataFrame(lista_add).sort_values("ADX_A", ascending=False).reset_index(drop=True)
        for c in ["Precio","ADX_A","KVAL","RSI"]: df4[c] = df4[c].round(2)
        df4["Volumen"] = df4["Volumen"].apply(lambda x: f"{x:,.0f}")
        df4["Vol_MA"] = df4["Vol_MA"].apply(lambda x: f"{x:,.0f}")
        st.dataframe(df4.style.map(lambda v: "background-color:#1a3d2b" if v=="BC" else "background-color:#3d2e0a", subset=["Banda"]), use_container_width=True, hide_index=True)
        st.download_button("⬇️ CSV", df4.to_csv(index=False).encode("utf-8"), "add_sg4_v12.csv")
    else: st.info("No se detectaron señales ADD.")

if lista_desc:
    with st.expander(f"⚠️ Descartados ({len(lista_desc)})", expanded=False):
        st.dataframe(pd.DataFrame(lista_desc), use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("SG4 v12 · RSI Wilder (original) · Radar exacto · ADD · Solo fines educativos.")
