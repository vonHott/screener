# ======================================================================
# SG3 SCREENER — APP STREAMLIT V9.1
# ======================================================================
# CAMBIOS V9.1:
#   - Numeros con 2 decimales en todas las tablas
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
    page_title="SG3 Screener",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================================================================
# WATCHLIST BASE
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
# RSI WILDER EXACTO (= MOOMOO / TRADINGVIEW)
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
# ANALISIS POR TICKER
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

    # MACD
    df['DIF']   = (df['Close'].ewm(span=12, adjust=False).mean()
                 - df['Close'].ewm(span=26, adjust=False).mean())
    df['DEA']   = df['DIF'].ewm(span=9, adjust=False).mean()
    df['HISTO'] = df['DIF'] - df['DEA']
    df['GIRO_MACD'] = (
        (df['HISTO'] > df['HISTO'].shift(1)) &
        (df['HISTO'].shift(1) <= df['HISTO'].shift(2))
    )

    # RSI WILDER
    df['OSC'] = calcular_rsi_wilder(df['Close'], periodo=14)

    # BOLLINGER Y VOLUMEN
    df['BB_MID'] = df['Close'].rolling(20).mean()
    df['BB_STD'] = df['Close'].rolling(20).std(ddof=0)
    df['BB_DN']  = df['BB_MID'] - (2 * df['BB_STD'])
    df['VOL_MA'] = df['Volume'].rolling(20).mean()

    # GATILLOS ORIGINALES
    df['S_PULL'] = (
        (df['Low'] < df['MA50'] * 1.015) & (df['Close'] > df['MA50'] * 0.985) &
        df['GIRO_J'] & (df['Volume'] > df['VOL_MA'] * 1.05) & df['FILTRO_BASE']
    )
    df['S_IMPU'] = (
        (df['Close'] > df['High'].shift(1).rolling(5).max()) &
        (df['ADX_V'] > df['ADX_REQ']) & df['MA20_UP'] &
        df['GIRO_J'] & (df['Volume'] > df['VOL_MA'] * 1.05)
    )
    df['S_BOLL'] = (
        (df['Low'].shift(1) <= df['BB_DN']) & (df['Close'] > df['BB_DN']) &
        df['GIRO_J'] & df['GIRO_MACD'] &
        (df['Volume'] > df['VOL_MA'] * 1.05) & df['FILTRO_BASE']
    )
    df['S_SUELO'] = (
        (df['OSC'] < 32) & (df['J_V'] < 22) &
        (df['Low'].shift(1) <= df['BB_DN']) & (df['Close'] > df['BB_DN']) &
        (df['Close'] > df['Low'].shift(1)) & df['GIRO_MACD'] &
        (df['Volume'] > df['VOL_MA'] * 0.9)
    )
    df['CROSS_MACD'] = (df['DIF'] > df['DEA']) & (df['DIF'].shift(1) <= df['DEA'].shift(1))
    df['S_MACD_CROSS'] = (
        df['CROSS_MACD'] & (df['DIF'] < 0) & (df['HISTO'] > df['HISTO'].shift(1)) &
        (df['Close'] > df['MA20']) & df['MA20_UP'] &
        (df['Volume'] > df['VOL_MA'] * 1.05) & df['FILTRO_BASE']
    )
    df['CROSS_KD'] = (df['KVAL'] > df['DVAL']) & (df['KVAL'].shift(1) <= df['DVAL'].shift(1))
    df['S_EARLY'] = (
        (df['OSC'] < 38) & (df['J_V'] < 30) & df['CROSS_KD'] &
        (df['Close'] > df['Close'].shift(1)) & df['MA20_UP'] &
        (df['Volume'] > df['VOL_MA'] * 0.9) & df['FILTRO_BASE']
    )

    # NUEVO V9 — S_REBOTE_MA50 (solo BC, volumen relajado)
    df['S_REBOTE_MA50'] = (
        (df['Low'] <= df['MA50'] * 1.008) &
        (df['Close'] > df['MA50']) &
        (df['Close'] > df['BB_DN']) &
        (df['Close'] < df['BB_MID']) &
        df['GIRO_J'] &
        df['MA20_UP'] &
        df['FILTRO_BASE'] &
        (df['Volume'] > df['VOL_MA'] * 0.95)
    )

    # B_RAW POR BANDA
    is_bc  = df['BANDA'] == "BC"
    is_vol = df['BANDA'] == "VOL"
    s_bc_valid = (
        df['S_PULL'] | df['S_IMPU'] | df['S_BOLL'] |
        df['S_SUELO'] | df['S_MACD_CROSS'] | df['S_EARLY'] |
        df['S_REBOTE_MA50']
    )
    s_vol_valid = (
        df['S_IMPU'] | df['S_BOLL'] | df['S_SUELO'] |
        df['S_MACD_CROSS'] | df['S_EARLY']
    )
    df['B_RAW'] = (is_bc & s_bc_valid) | (is_vol & s_vol_valid)

    # Dias consecutivos activa
    b_raw_list  = df['B_RAW'].tolist()
    dias_activa = 0
    for val in reversed(b_raw_list[-5:]):
        if val: dias_activa += 1
        else:   break

    # Gatillos activos
    gatillos = []
    if dias_activa > 0:
        for nombre, col in [
            ("S_PULL","S_PULL"), ("S_IMPU","S_IMPU"), ("S_BOLL","S_BOLL"),
            ("S_SUELO","S_SUELO"), ("S_MACD_CROSS","S_MACD_CROSS"),
            ("S_EARLY","S_EARLY"), ("S_REBOTE_MA50","S_REBOTE_MA50"),
        ]:
            if df[col].iloc[-1]: gatillos.append(nombre)

    tp_mult  = 1.6 if df['BANDA'].iloc[-1] == "BC" else 2.2
    tp_ideal = df['Close'].iloc[-1] + (df['ATR_V'].iloc[-1] * tp_mult)

    # RADAR
    df['OJO'] = (
        (df['OSC'] < 35) & (df['J_V'] < 28) &
        (df['Close'] <= df['BB_DN'] * 1.01)
    ).fillna(False)
    df['CRUCE_J'] = (
        (df['J_V'] > 10) & (df['J_V'].shift(1).fillna(100) <= 12)
    ).fillna(False)
    df['BTD'] = (
        df['OJO'].shift(1).fillna(False) &
        df['CRUCE_J'] &
        df['GIRO_MACD'].fillna(False)
    ).fillna(False)

    ojo_reciente = bool(df['OJO'].iloc[-2:].any())
    btd_reciente = bool(df['BTD'].iloc[-2:].any())

    return {
        "Ticker":      ticker_name,
        "Fecha":       ultima_fecha,
        "Banda":       df['BANDA'].iloc[-1],
        "Precio":      round(float(df['Close'].iloc[-1]), 2),
        "RSI":         round(float(df['OSC'].iloc[-1]), 2),
        "ADX":         round(float(df['ADX_V'].iloc[-1]), 2),
        "J_V":         round(float(df['J_V'].iloc[-1]), 2),
        "BB_DN":       round(float(df['BB_DN'].iloc[-1]), 2),
        "Dias_Activa": dias_activa,
        "Gatillos":    ", ".join(gatillos) if gatillos else "—",
        "TP1":         round(float(tp_ideal), 2),
        "Radar_OJO":   ojo_reciente,
        "Radar_BTD":   btd_reciente,
    }, None

# ======================================================================
# SIDEBAR
# ======================================================================
with st.sidebar:
    st.title("Configuracion SG3")
    periodo    = st.selectbox("Periodo historico", ["2y","1y","6mo"], index=0)
    rsi_umbral = st.slider("Umbral RSI sobreventa", 25, 45, 33)
    dias_max   = st.slider("Señal activa max. dias", 1, 5, 3)
    st.markdown("---")
    st.markdown("**Watchlist personalizada**")
    tickers_input = st.text_area(
        "Un ticker por linea o separado por comas (vacio = lista base)",
        height=140, placeholder="AAPL\nNVDA\nTSLA"
    )
    st.markdown("---")
    st.caption("SG3 v9.1 · RSI Wilder · BC/VOL Adaptativo")
    ejecutar = st.button("🚀 Ejecutar escaner", use_container_width=True, type="primary")

# ======================================================================
# MAIN
# ======================================================================
st.title("📊 SG3 — Santo Grial 3 · Screener")
st.caption("Sistema KW-DNA · BC/VOL Adaptativo · RSI Wilder · 7 Gatillos · v9.1")

if not ejecutar:
    st.info("Configura los parametros en la barra lateral y presiona Ejecutar escaner.")
    with st.expander("📖 Gatillos del sistema", expanded=False):
        st.markdown("""
| Gatillo | Descripcion | Volumen min |
|---|---|---|
| S_PULL | Pullback a MA50 con rebote y KDJ girando | 105% |
| S_IMPU | Ruptura de maximos con ADX fuerte | 105% |
| S_BOLL | Rebote desde banda inferior Bollinger | 105% |
| S_SUELO | RSI + KDJ sobreventa extrema con giro MACD | 90% |
| S_MACD_CROSS | Cruce DIF/DEA bajo cero con momentum | 105% |
| S_EARLY | Cruce KD en sobreventa antes de confirmacion | 90% |
| **S_REBOTE_MA50** | Rebote limpio en MA50, solo BC | 95% |
        """)
    st.stop()

# Resolver watchlist
if tickers_input.strip():
    tickers = [t.strip().upper() for t in tickers_input.replace(',','\n').splitlines() if t.strip()]
    tickers = list(dict.fromkeys(tickers))
else:
    tickers = TICKERS_DEFAULT

# ======================================================================
# EJECUCION
# ======================================================================
lista_compras, lista_rsi, lista_radar, lista_desc = [], [], [], []
progreso = st.progress(0, text="Iniciando...")
col1, col2, col3 = st.columns(3)
m_compras = col1.empty()
m_rsi     = col2.empty()
m_radar   = col3.empty()

for idx, ticker in enumerate(tickers):
    pct = int((idx + 1) / len(tickers) * 100)
    progreso.progress(pct, text=f"Procesando {ticker}... ({idx+1}/{len(tickers)})")
    m_compras.metric("🚀 Compras frescas", len(lista_compras))
    m_rsi.metric(f"📉 RSI < {rsi_umbral}", len(lista_rsi))
    m_radar.metric("🎯 Radar OJO/BTD", len(lista_radar))

    try:
        df = yf.download(ticker, period=periodo, progress=False, auto_adjust=True)
        if df.empty:
            lista_desc.append({"Ticker": ticker, "Motivo": "Sin datos en yfinance"})
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        datos, motivo = analizar_ticker(df, ticker)
        if datos is None:
            lista_desc.append({"Ticker": ticker, "Motivo": motivo})
            continue

        # Seccion 1: Compras frescas
        if 0 < datos["Dias_Activa"] <= dias_max:
            estado_str = "Dia 1" if datos["Dias_Activa"] == 1 else f"Activa {datos['Dias_Activa']}d"
            lista_compras.append({
                "Ticker":     datos["Ticker"],
                "Fecha":      datos["Fecha"],
                "Banda":      datos["Banda"],
                "Antiguedad": estado_str,
                "Gatillos":   datos["Gatillos"],
                "Precio":     datos["Precio"],
                "RSI":        datos["RSI"],
                "ADX":        datos["ADX"],
                "TP1":        datos["TP1"],
            })

        # Seccion 2: Sobreventa RSI
        if datos["RSI"] < rsi_umbral:
            lista_rsi.append({
                "Ticker": datos["Ticker"],
                "Fecha":  datos["Fecha"],
                "Banda":  datos["Banda"],
                "Precio": datos["Precio"],
                "RSI":    datos["RSI"],
                "J_V":    datos["J_V"],
                "ADX":    datos["ADX"],
            })

        # Seccion 3: Radar
        if datos["Radar_BTD"]:
            lista_radar.append({
                "Ticker": datos["Ticker"],
                "Senal":  "🟢 BTD",
                "Banda":  datos["Banda"],
                "Precio": datos["Precio"],
                "RSI":    datos["RSI"],
                "J_V":    datos["J_V"],
                "BB_DN":  datos["BB_DN"],
            })
        elif datos["Radar_OJO"]:
            lista_radar.append({
                "Ticker": datos["Ticker"],
                "Senal":  "🟡 OJO",
                "Banda":  datos["Banda"],
                "Precio": datos["Precio"],
                "RSI":    datos["RSI"],
                "J_V":    datos["J_V"],
                "BB_DN":  datos["BB_DN"],
            })

    except Exception as e:
        lista_desc.append({"Ticker": ticker, "Motivo": str(e)[:80]})

progreso.empty()
st.success(f"✅ Escaner completado — {len(tickers)} tickers procesados")
m_compras.metric("🚀 Compras frescas", len(lista_compras))
m_rsi.metric(f"📉 RSI < {rsi_umbral}", len(lista_rsi))
m_radar.metric("🎯 Radar OJO/BTD", len(lista_radar))

# ======================================================================
# TABS
# ======================================================================
tab1, tab2, tab3 = st.tabs([
    f"🚀 Compras frescas ({len(lista_compras)})",
    f"📉 Sobreventa RSI ({len(lista_rsi)})",
    f"🎯 Radar OJO/BTD ({len(lista_radar)})",
])

with tab1:
    st.subheader("Senales activas en los ultimos 1-3 dias")
    if lista_compras:
        df1 = pd.DataFrame(lista_compras).reset_index(drop=True)
        for c in ["Precio", "RSI", "ADX", "TP1"]:
            df1[c] = df1[c].round(2)
        st.dataframe(
            df1.style.map(
                lambda v: "background-color:#1a3d2b" if v == "BC" else "background-color:#3d2e0a",
                subset=["Banda"]
            ),
            use_container_width=True, hide_index=True
        )
        st.download_button("⬇️ Descargar CSV", df1.to_csv(index=False).encode("utf-8"),
                           "compras_sg3_v9.csv", "text/csv")
    else:
        st.info("Ninguna compra fresca reciente.")

with tab2:
    st.subheader(f"Activos con RSI Wilder < {rsi_umbral}")
    if lista_rsi:
        df2 = pd.DataFrame(lista_rsi).sort_values("RSI").reset_index(drop=True)
        for c in ["Precio", "RSI", "J_V", "ADX"]:
            df2[c] = df2[c].round(2)
        st.dataframe(df2, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Descargar CSV", df2.to_csv(index=False).encode("utf-8"),
                           "sobreventa_sg3_v9.csv", "text/csv")
    else:
        st.info("Ningun activo en sobreventa extrema hoy.")

with tab3:
    st.subheader("Radar temprano — formacion de suelo")
    if lista_radar:
        df3 = pd.DataFrame(lista_radar)
        df3["_ord"] = df3["Senal"].apply(lambda x: 0 if "BTD" in x else 1)
        df3 = df3.sort_values(["_ord","RSI"]).drop(columns="_ord").reset_index(drop=True)
        for c in ["Precio", "RSI", "J_V", "BB_DN"]:
            df3[c] = df3[c].round(2)
        st.dataframe(df3, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Descargar CSV", df3.to_csv(index=False).encode("utf-8"),
                           "radar_sg3_v9.csv", "text/csv")
    else:
        st.info("Sin alertas tempranas de formacion de suelo.")

# DESCARTADOS
if lista_desc:
    with st.expander(f"⚠️ Tickers descartados ({len(lista_desc)})", expanded=False):
        df4 = pd.DataFrame(lista_desc).reset_index(drop=True)
        st.dataframe(df4, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("SG3 Screener v9.1 · RSI Wilder sincronizado con Moomoo/TradingView · Solo con fines educativos.")
