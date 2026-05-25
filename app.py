# ======================================================================
# SG4 SCREENER — APP STREAMLIT V12
# ======================================================================
# NOVEDADES V12:
#   - ADD-BC y ADD-VOL detectados y mostrados en columna Gatillos
#     de compras frescas, separados por coma
#   - Dias activa muestra cuantos dias lleva la operacion abierta
#   - Put Wall, Call Wall y GEX en las 4 secciones (5 series)
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
# GEX — PUT WALL, CALL WALL (5 SERIES = 5 VENCIMIENTOS)
# ======================================================================
def calcular_gex(ticker_name, precio_actual):
    try:
        tk   = yf.Ticker(ticker_name)
        exps = tk.options
        if not exps:
            return None

        exps_usar = exps[:5]  # 5 series = semana actual + 4
        puts_all  = []
        calls_all = []

        for exp in exps_usar:
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

        rango_low  = precio_actual * 0.70
        rango_high = precio_actual * 1.30
        puts_df  = puts_df[(puts_df['strike'] >= rango_low) & (puts_df['strike'] <= rango_high)]
        calls_df = calls_df[(calls_df['strike'] >= rango_low) & (calls_df['strike'] <= rango_high)]

        if puts_df.empty or calls_df.empty:
            return None

        put_wall  = float(puts_df.loc[puts_df['openInterest'].idxmax(), 'strike'])
        call_wall = float(calls_df.loc[calls_df['openInterest'].idxmax(), 'strike'])

        if precio_actual > call_wall:
            emoji    = "🔴"
            contexto = "Techo gamma activo"
        elif precio_actual < put_wall:
            emoji    = "🟡"
            contexto = "Piso gamma, rebote"
        else:
            dist_put  = precio_actual - put_wall
            dist_call = call_wall - precio_actual
            if dist_call < dist_put * 0.4:
                emoji    = "🟠"
                contexto = "Cerca techo gamma"
            else:
                emoji    = "🟢"
                contexto = "Zona gamma favorable"

        return {
            "Put Wall":  round(put_wall, 2),
            "Call Wall": round(call_wall, 2),
            "GEX":       f"{emoji} {contexto}",
        }

    except Exception:
        return None

# ======================================================================
# ANALISIS POR TICKER — SG4
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

    # ADX CORTO (6 barras) PARA ADD
    tr_sum6 = df['TR_V'].rolling(6).sum().replace(0, 1e-8)
    dmp6    = df['DMP_RAW'].rolling(6).sum()
    dmm6    = df['DMM_RAW'].rolling(6).sum()
    df['PDI_A'] = dmp6 * 100 / tr_sum6
    df['MDI_A'] = dmm6 * 100 / tr_sum6
    pdi_mdi_sum6 = (df['PDI_A'] + df['MDI_A']).replace(0, 1e-8)
    adx_a_raw    = abs(df['PDI_A'] - df['MDI_A']) / pdi_mdi_sum6 * 100
    df['ADX_A']  = adx_a_raw.rolling(6).mean()
    df['ADX_A_ACCEL'] = (
        (df['ADX_A'] > df['ADX_A'].shift(1)) &
        (df['ADX_A'].shift(1) > df['ADX_A'].shift(2))
    )

    # KDJ
    low_min   = df['Low'].rolling(9).min()
    high_max  = df['High'].rolling(9).max()
    denom_kdj = (high_max - low_min).replace(0, 1e-8)
    df['RSV']  = (df['Close'] - low_min) / denom_kdj * 100
    df['KVAL'] = df['RSV'].ewm(alpha=1/3, adjust=False).mean()
    df['DVAL'] = df['KVAL'].ewm(alpha=1/3, adjust=False).mean()
    df['J_V']  = (3 * df['KVAL']) - (2 * df['DVAL'])
    df['GIRO_J']  = df['J_V'] > df['J_V'].shift(1)
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
    df['MACD_GIRO_NEG'] = (
        (df['HISTO'] < 0) &
        (df['HISTO'] < df['HISTO'].shift(1)) &
        (df['HISTO'].shift(1) < df['HISTO'].shift(2))
    )

    # RSI WILDER
    df['OSC'] = calcular_rsi_wilder(df['Close'], periodo=14)

    # BOLLINGER Y VOLUMEN
    df['BB_MID'] = df['Close'].rolling(20).mean()
    df['BB_STD'] = df['Close'].rolling(20).std(ddof=0)
    df['BB_DN']  = df['BB_MID'] - (2 * df['BB_STD'])
    df['VOL_MA'] = df['Volume'].rolling(20).mean()

    # ================================================================
    # GATILLOS SG3 ORIGINALES
    # ================================================================
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
    df['S_EARLY'] = (
        (df['OSC'] < 38) & (df['J_V'] < 30) & df['CROSS_KD'] &
        (df['Close'] > df['Close'].shift(1)) & df['MA20_UP'] &
        (df['Volume'] > df['VOL_MA'] * 0.9) & df['FILTRO_BASE']
    )

    # ================================================================
    # NUEVOS GATILLOS SG4
    # ================================================================
    df['S_REBOTE_MA50'] = (
        (df['Low'] <= df['MA50'] * 1.008) & (df['Close'] > df['MA50']) &
        (df['Close'] > df['BB_DN']) & (df['Close'] < df['BB_MID']) &
        df['GIRO_J'] & df['MA20_UP'] & df['F_ALCISTA'] &
        (df['Volume'] > df['VOL_MA'] * 0.95)
    )
    df['S_REBOTE_MA200'] = (
        (df['Low'] <= df['MA200'] * 1.01) & (df['Close'] > df['MA200']) &
        (df['Close'] > df['Low'].shift(1)) & df['GIRO_J'] & df['MA20_UP'] &
        (df['Volume'] > df['VOL_MA'] * 0.95)
    )
    df['S_BOLL_SOFT'] = (
        (df['Low'].shift(1) <= df['BB_DN']) & (df['Close'] > df['BB_DN']) &
        (df['Close'] > df['Low'].shift(1)) & df['GIRO_J'] &
        (df['Volume'] > df['VOL_MA'] * 0.9) & df['FILTRO_BASE'] &
        ~df['MACD_GIRO_NEG']
    )

    # B_RAW
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
    df['B_RAW']    = (is_bc & s_bc_valid) | (is_vol & s_vol_valid)
    df['B_SIGNAL'] = df['B_RAW'] & ~df['B_RAW'].shift(1).fillna(False)

    # Dias consecutivos activa (señal de entrada)
    b_raw_list  = df['B_RAW'].tolist()
    dias_activa = 0
    for val in reversed(b_raw_list[-5:]):
        if val: dias_activa += 1
        else:   break

    # ================================================================
    # DURACION REAL DESDE B_SIGNAL (para ADD)
    # Busca la ultima señal de entrada y cuenta barras desde entonces
    # ================================================================
    b_signal_list = df['B_SIGNAL'].tolist()
    duracion = 0
    for i in range(len(b_signal_list)-1, -1, -1):
        if b_signal_list[i]:
            duracion = len(b_signal_list) - 1 - i
            break

    # TP1 aproximado (para filtro ADD — TP1 no alcanzado)
    tp_mult  = 1.6 if df['BANDA'].iloc[-1] == "BC" else 2.2
    tp_ideal = df['Close'].iloc[-1] + (df['ATR_V'].iloc[-1] * tp_mult)

    # Precio de entrada (ultimo B_SIGNAL)
    e_price = None
    for i in range(len(b_signal_list)-1, -1, -1):
        if b_signal_list[i]:
            e_price = df['Close'].iloc[i]
            break

    # TP1_HIT aproximado
    tp1_hit = False
    if e_price is not None and duracion > 0:
        ventana_high = df['High'].iloc[-(duracion+1):]
        tp1_nivel    = e_price + df['ATR_V'].iloc[-1] * tp_mult
        tp1_hit      = bool(ventana_high.max() > tp1_nivel)

    # ================================================================
    # ADD — BC Y VOL
    # ================================================================
    i = len(df) - 1

    add_bc = (
        dias_activa > 0 and
        df['BANDA'].iloc[i] == "BC" and
        df['PDI_A'].iloc[i] > df['MDI_A'].iloc[i] and
        df['ADX_A'].iloc[i] > 28 and
        bool(df['ADX_A_ACCEL'].iloc[i]) and
        bool(df['CROSS_KD'].iloc[i]) and
        df['KVAL'].iloc[i] < 75 and
        df['Close'].iloc[i] > df['MA20'].iloc[i] and
        df['Volume'].iloc[i] > df['VOL_MA'].iloc[i] * 1.2 and
        not tp1_hit
    )

    add_vol = (
        dias_activa > 0 and
        df['BANDA'].iloc[i] == "VOL" and
        df['PDI_A'].iloc[i] > df['MDI_A'].iloc[i] and
        df['ADX_A'].iloc[i] > 32 and
        bool(df['ADX_A_ACCEL'].iloc[i]) and
        df['Close'].iloc[i] > df['High'].iloc[max(0,i-3):i].max() and
        df['Close'].iloc[i] > df['MA20'].iloc[i] and
        df['Volume'].iloc[i] > df['VOL_MA'].iloc[i] * 1.4 and
        not tp1_hit
    )

    add_senal = "ADD-BC" if add_bc else ("ADD-VOL" if add_vol else None)

    # Gatillos activos
    gatillos = []
    if dias_activa > 0:
        for nombre, col in [
            ("S_PULL","S_PULL"), ("S_IMPU","S_IMPU"), ("S_BOLL","S_BOLL"),
            ("S_SUELO","S_SUELO"), ("S_MACD_CROSS","S_MACD_CROSS"),
            ("S_EARLY","S_EARLY"), ("S_REBOTE_MA50","S_REBOTE_MA50"),
            ("S_REBOTE_MA200","S_REBOTE_MA200"), ("S_BOLL_SOFT","S_BOLL_SOFT"),
        ]:
            if df[col].iloc[-1]: gatillos.append(nombre)

    # Agregar ADD al string de gatillos si aplica
    if add_senal:
        gatillos.append(f"⚡{add_senal}")

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
        "Duracion":    duracion,
        "Gatillos":    ", ".join(gatillos) if gatillos else "—",
        "TP1":         round(float(tp_ideal), 2),
        "Radar_OJO":   ojo_reciente,
        "Radar_BTD":   btd_reciente,
        "Add_Senal":   add_senal,
    }, None

# ======================================================================
# SIDEBAR
# ======================================================================
with st.sidebar:
    st.title("Configuracion SG4")
    periodo    = st.selectbox("Periodo historico", ["2y","1y","6mo"], index=0)
    rsi_umbral = st.slider("Umbral RSI sobreventa", 25, 45, 33)
    dias_max   = st.slider("Señal activa max. dias", 1, 5, 3)
    usar_gex   = st.toggle("Incluir Put/Call Wall (GEX)", value=True,
                           help="5 series de vencimientos. Solo acciones USA. Aumenta tiempo.")
    st.markdown("---")
    st.markdown("**Watchlist personalizada**")
    tickers_input = st.text_area(
        "Un ticker por linea o separado por comas (vacio = lista base)",
        height=140, placeholder="AAPL\nNVDA\nTSLA"
    )
    st.markdown("---")
    st.caption("SG4 v12 · RSI Wilder · 9 Gatillos · ADD · GEX 5 series")
    ejecutar = st.button("🚀 Ejecutar escaner", use_container_width=True, type="primary")

# ======================================================================
# MAIN
# ======================================================================
st.title("📊 SG4 — Santo Grial 4 · Screener")
st.caption("Sistema KW-DNA · BC/VOL Adaptativo · RSI Wilder · 9 Gatillos · ADD · Put/Call Wall · v12.0")

if not ejecutar:
    st.info("Configura los parametros en la barra lateral y presiona Ejecutar escaner.")
    with st.expander("📖 Gatillos SG4 + ADD + GEX", expanded=False):
        st.markdown("""
**Gatillos entrada:**
| Gatillo | Descripcion | Banda | Vol |
|---|---|---|---|
| S_PULL | Pullback a MA50 con rebote | BC | 105% |
| S_IMPU | Ruptura maximos + ADX fuerte | BC+VOL | 105% |
| S_BOLL | Rebote BB inferior + GIRO_MACD | BC+VOL | 105% |
| S_SUELO | RSI+KDJ sobreventa + MACD | BC+VOL | 90% |
| S_MACD_CROSS | Cruce DIF/DEA bajo cero | BC+VOL | 105% |
| S_EARLY | Cruce KD anticipado | BC+VOL | 90% |
| S_REBOTE_MA50 | Rebote MA50 entre bandas | Solo BC | 95% |
| S_REBOTE_MA200 | Rebote MA200 | BC+VOL | 95% |
| S_BOLL_SOFT | Rebote BB sin GIRO_MACD | BC+VOL | 90% |

**ADD (aparece en columna Gatillos con ⚡):**
- ⚡ADD-BC: ADX corto > 28 acelerando + cruce KD + KVAL < 75 + Vol > 120%
- ⚡ADD-VOL: ADX corto > 32 acelerando + nuevo maximo 3 barras + Vol > 140%

**GEX (5 series de vencimientos):**
- 🟢 Zona gamma favorable — precio entre Put y Call Wall
- 🟠 Cerca techo gamma — precio cerca del Call Wall
- 🔴 Techo gamma activo — precio sobre Call Wall
- 🟡 Piso gamma, rebote — precio bajo Put Wall
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

        # GEX
        gex = None
        if usar_gex and not any(x in ticker for x in ['-USD', 'ETH', 'BTC', 'SOL']):
            gex = calcular_gex(ticker, datos["Precio"])

        put_wall  = gex["Put Wall"]  if gex else "—"
        call_wall = gex["Call Wall"] if gex else "—"
        gex_ctx   = gex["GEX"]       if gex else "—"

        # Seccion 1: Compras frescas (1-3 dias) + ADD aunque sean mas dias
        es_compra_fresca = 0 < datos["Dias_Activa"] <= dias_max
        es_add           = datos["Add_Senal"] is not None

        if es_compra_fresca or es_add:
            estado_str = (
                "Dia 1" if datos["Dias_Activa"] == 1
                else f"Activa {datos['Dias_Activa']}d" if datos["Dias_Activa"] > 0
                else f"Abierta {datos['Duracion']}d"
            )
            lista_compras.append({
                "Ticker":     datos["Ticker"],
                "Fecha":      datos["Fecha"],
                "Banda":      datos["Banda"],
                "Dias":       estado_str,
                "Gatillos":   datos["Gatillos"],
                "Precio":     datos["Precio"],
                "RSI":        datos["RSI"],
                "ADX":        datos["ADX"],
                "TP1":        datos["TP1"],
                "Put Wall":   put_wall,
                "Call Wall":  call_wall,
                "GEX":        gex_ctx,
            })

        # Seccion 2: Sobreventa RSI
        if datos["RSI"] < rsi_umbral:
            lista_rsi.append({
                "Ticker":    datos["Ticker"],
                "Fecha":     datos["Fecha"],
                "Banda":     datos["Banda"],
                "Precio":    datos["Precio"],
                "RSI":       datos["RSI"],
                "J_V":       datos["J_V"],
                "ADX":       datos["ADX"],
                "Put Wall":  put_wall,
                "Call Wall": call_wall,
                "GEX":       gex_ctx,
            })

        # Seccion 3: Radar
        if datos["Radar_BTD"]:
            lista_radar.append({
                "Ticker":    datos["Ticker"],
                "Senal":     "🟢 BTD",
                "Banda":     datos["Banda"],
                "Precio":    datos["Precio"],
                "RSI":       datos["RSI"],
                "J_V":       datos["J_V"],
                "BB_DN":     datos["BB_DN"],
                "Put Wall":  put_wall,
                "Call Wall": call_wall,
                "GEX":       gex_ctx,
            })
        elif datos["Radar_OJO"]:
            lista_radar.append({
                "Ticker":    datos["Ticker"],
                "Senal":     "🟡 OJO",
                "Banda":     datos["Banda"],
                "Precio":    datos["Precio"],
                "RSI":       datos["RSI"],
                "J_V":       datos["J_V"],
                "BB_DN":     datos["BB_DN"],
                "Put Wall":  put_wall,
                "Call Wall": call_wall,
                "GEX":       gex_ctx,
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
    f"🚀 Compras + ADD ({len(lista_compras)})",
    f"📉 Sobreventa RSI ({len(lista_rsi)})",
    f"🎯 Radar OJO/BTD ({len(lista_radar)})",
])

with tab1:
    st.subheader("Senales activas — compras frescas y señales ADD")
    st.caption("⚡ en Gatillos indica señal ADD activa sobre posicion abierta")
    if lista_compras:
        df1 = pd.DataFrame(lista_compras).reset_index(drop=True)
        # Ordenar: ADD al fondo, compras frescas arriba
        df1['_ord'] = df1['Gatillos'].apply(lambda x: 1 if '⚡' in str(x) and not any(
            g in str(x) for g in ['S_PULL','S_IMPU','S_BOLL','S_SUELO','S_MACD','S_EARLY','S_REBOTE','S_BOLL_SOFT']
        ) else 0)
        df1 = df1.sort_values('_ord').drop(columns='_ord').reset_index(drop=True)
        for c in ["Precio", "RSI", "ADX", "TP1"]:
            df1[c] = pd.to_numeric(df1[c], errors='coerce').round(2)
        st.dataframe(
            df1.style.map(
                lambda v: "background-color:#1a3d2b" if v == "BC" else "background-color:#3d2e0a",
                subset=["Banda"]
            ),
            use_container_width=True, hide_index=True
        )
        st.download_button("⬇️ Descargar CSV", df1.to_csv(index=False).encode("utf-8"),
                           "compras_sg4_v12.csv", "text/csv")
    else:
        st.info("Ninguna compra fresca ni ADD activo hoy.")

with tab2:
    st.subheader(f"Activos con RSI Wilder < {rsi_umbral}")
    if lista_rsi:
        df2 = pd.DataFrame(lista_rsi).sort_values("RSI").reset_index(drop=True)
        for c in ["Precio", "RSI", "J_V", "ADX"]:
            df2[c] = pd.to_numeric(df2[c], errors='coerce').round(2)
        st.dataframe(df2, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Descargar CSV", df2.to_csv(index=False).encode("utf-8"),
                           "sobreventa_sg4_v12.csv", "text/csv")
    else:
        st.info("Ningun activo en sobreventa extrema hoy.")

with tab3:
    st.subheader("Radar temprano — OJO y BTD")
    if lista_radar:
        df3 = pd.DataFrame(lista_radar)
        df3["_ord"] = df3["Senal"].apply(lambda x: 0 if "BTD" in x else 1)
        df3 = df3.sort_values(["_ord","RSI"]).drop(columns="_ord").reset_index(drop=True)
        for c in ["Precio", "RSI", "J_V", "BB_DN"]:
            df3[c] = pd.to_numeric(df3[c], errors='coerce').round(2)
        st.dataframe(df3, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Descargar CSV", df3.to_csv(index=False).encode("utf-8"),
                           "radar_sg4_v12.csv", "text/csv")
    else:
        st.info("Sin alertas tempranas de formacion de suelo.")

# DESCARTADOS
if lista_desc:
    with st.expander(f"⚠️ Tickers descartados ({len(lista_desc)})", expanded=False):
        df4 = pd.DataFrame(lista_desc).reset_index(drop=True)
        st.dataframe(df4, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("SG4 Screener v12 · RSI Wilder = Moomoo/TradingView · GEX 5 series via yfinance · Solo fines educativos.")
