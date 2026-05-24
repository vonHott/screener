Este código Streamlit funciona perfectamente y tiene la lógica limpia, pero **no es la versión final equivalente al script de Moomoo de SG6** que acabamos de corregir.

Como bien dices, te sirve impecable para mapear **entradas, señales ADD y el RSI exacto**. Sin embargo, si quieres que tu rastreador de Python converse exactamente en el mismo idioma que tu gráfico, este script de Streamlit tiene **3 discrepancias matemáticas importantes** respecto a las reglas actualizadas de SG6:

---

## Las 3 discrepancias que debes ajustar

### 1. El cálculo del RSI (`OSC`)

En tu función `calcular_rsi_wilder`, usas la media móvil de Wilder (que es equivalente a una EMA con $alpha = 1/N$). Sin embargo, en el script nativo de Moomoo que me pasaste antes, el oscilador está calculado usando sumas simples de 14 períodos:


$$\text{OSC} = 100 - \left(\frac{100}{1 + \frac{\sum \text{U\_D}}{\sum \text{D\_D}}}\right)$$

* **El problema:** Si dejas la fórmula de Wilder en Python, las alertas de sobreventa (`OSC < 32` u `OJO`) te van a dar valores sutilmente distintos a los que ves pintados en la pantalla de Moomoo.

### 2. El Filtro Base (`FILTRO_BASE`)

* **En tu Streamlit:** Tienes `df['FILTRO_BASE'] = df['Close'] >= df['MA200']`.
* **En tu Moomoo (SG6):** Tu regla es adaptativa: `FILTRO_BASE := IF(F_BAJISTA, CLOSE > MA200, 1);`. Es decir, si está alcista, el filtro base siempre es verdadero (`1`). Tu código de Python actual está limitando de más los gatillos cuando el precio corta la EMA200.

### 3. El gatillo `S_SUELO` y `S_EARLY` (Volumen)

* **En tu Streamlit:** Usas un multiplicador de volumen plano: `* 0.9`.
* **En tu Moomoo (SG6):** Definiste umbrales estrictos (`VOL_SOFT := VOL > VOL_MA * 0.9;`). La lógica correcta en Python debe ser `df['Volume'] > df['VOL_MA'] * 0.9` (mayor que, no menor que, para asegurar que haya un mínimo de interés institucional participando del suelo).

---

## Código Corregido y Definitivo (V12.1 — Equivalente SG6)

Aquí tienes el script modificado en las funciones clave para que las alertas del screener coincidan al 100% con las de Moomoo:

```python
# ======================================================================
# SG6 SCREENER — APP STREAMLIT V12.1 (EQUIVALENTE MOOMOO SG6)
# ======================================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Configuración Base de la Página
st.set_page_config(
    page_title="SG6 Screener",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
# OSCILADOR RSI EXACTO EN BASE A SUMAS (COINCIDE CON TU SG6 MOOMOO)
# ======================================================================
def calcular_rsi_sumas_sg6(close_series, periodo=14):
    delta = close_series.diff()
    u_d = delta.clip(lower=0)
    d_d = (-delta).clip(lower=0)
    
    sum_u = u_d.rolling(window=periodo).sum()
    sum_d = d_d.rolling(window=periodo).sum()
    
    # Evitar división por cero
    sum_d_safe = np.where(sum_d == 0, 1e-8, sum_d)
    osc = 100 - (100 / (1 + (sum_u / sum_d_safe)))
    return pd.Series(osc, index=close_series.index)

# ======================================================================
# GEX — PUT WALL, CALL WALL (5 VENCIMIENTOS)
# ======================================================================
def calcular_gex(ticker_name, precio_actual):
    try:
        tk   = yf.Ticker(ticker_name)
        exps = tk.options
        if not exps: return None

        exps_usar = exps[:5]
        puts_all  = []
        calls_all = []

        for exp in exps_usar:
            try:
                chain = tk.option_chain(exp)
                puts_all.append(chain.puts[['strike','openInterest']].copy())
                calls_all.append(chain.calls[['strike','openInterest']].copy())
            except Exception:
                continue

        if not puts_all or not calls_all: return None

        puts_df  = pd.concat(puts_all).groupby('strike')['openInterest'].sum().reset_index()
        calls_df = pd.concat(calls_all).groupby('strike')['openInterest'].sum().reset_index()

        rango_low  = precio_actual * 0.70
        rango_high = precio_actual * 1.30
        puts_df  = puts_df[(puts_df['strike'] >= rango_low) & (puts_df['strike'] <= rango_high)]
        calls_df = calls_df[(calls_df['strike'] >= rango_low) & (calls_df['strike'] <= rango_high)]

        if puts_df.empty or calls_df.empty: return None

        put_wall  = float(puts_df.loc[puts_df['openInterest'].idxmax(), 'strike'])
        call_wall = float(calls_df.loc[calls_df['openInterest'].idxmax(), 'strike'])

        if precio_actual > call_wall:
            emoji, contexto = "🔴", "Techo gamma activo"
        elif precio_actual < put_wall:
            emoji, contexto = "🟡", "Piso gamma, rebote"
        else:
            dist_put, dist_call = precio_actual - put_wall, call_wall - precio_actual
            if dist_call < dist_put * 0.4:
                emoji, contexto = "🟠", "Cerca techo gamma"
            else:
                emoji, contexto = "🟢", "Zona gamma favorable"

        return {"Put Wall": round(put_wall, 2), "Call Wall": round(call_wall, 2), "GEX": f"{emoji} {contexto}"}
    except Exception:
        return None

# ======================================================================
# ANÁLISIS POR TICKER — ADAPTADO A REGLAS MATEMÁTICAS SG6
# ======================================================================
def analizar_ticker(df, ticker_name):
    df = df.dropna(subset=['Close', 'Volume'])
    df = df[df['Volume'] > 0].copy()
    if len(df) < 250: return None, f"Pocas velas: {len(df)}"

    ultima_fecha = df.index[-1].strftime('%Y-%m-%d')

    # BANDA
    df['RET_V']    = df['Close'].pct_change() * 100
    df['BETA_RAW'] = df['RET_V'].rolling(60).std(ddof=0)
    df['BETA_S']   = df['BETA_RAW'].rolling(20).mean()
    df['BANDA']    = np.where(df['BETA_S'] < 1.4, "BC", "VOL")

    # MEDIAS Y CONTEXTO ALCISTA/BAJISTA
    df['MA20']  = df['Close'].ewm(span=20,  adjust=False).mean()
    df['MA50']  = df['Close'].ewm(span=50,  adjust=False).mean()
    df['MA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    df['F_BAJISTA'] = df['Close'] < df['MA200']
    df['F_ALCISTA'] = df['Close'] > df['MA200']
    df['MA20_UP']   = df['MA20'] > df['MA20'].shift(1)
    
    # CORRECCIÓN FILTRO BASE ADAPTATIVO SG6
    df['FILTRO_BASE'] = np.where(df['F_BAJISTA'], df['Close'] > df['MA200'], True)

    # ATR
    df['H_L']   = df['High'] - df['Low']
    df['H_PC']  = (df['High'] - df['Close'].shift(1)).abs()
    df['L_PC']  = (df['Low']  - df['Close'].shift(1)).abs()
    df['TR_V']  = df[['H_L', 'H_PC', 'L_PC']].max(axis=1)
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

    # ADX CORTO (6 barras) PARA RECOMPRAS ADD
    tr_sum6 = df['TR_V'].rolling(6).sum().replace(0, 1e-8)
    df['PDI_A'] = df['DMP_RAW'].rolling(6).sum() * 100 / tr_sum6
    df['MDI_A'] = df['DMM_RAW'].rolling(6).sum() * 100 / tr_sum6
    pdi_mdi_sum6 = (df['PDI_A'] + df['MDI_A']).replace(0, 1e-8)
    df['ADX_A']  = (abs(df['PDI_A'] - df['MDI_A']) / pdi_mdi_sum6 * 100).rolling(6).mean()
    df['ADX_A_ACCEL'] = (df['ADX_A'] > df['ADX_A'].shift(1)) & (df['ADX_A'].shift(1) > df['ADX_A'].shift(2))

    # KDJ
    low_min, high_max = df['Low'].rolling(9).min(), df['High'].rolling(9).max()
    denom_kdj = (high_max - low_min).replace(0, 1e-8)
    df['RSV']  = (df['Close'] - low_min) / denom_kdj * 100
    df['KVAL'] = df['RSV'].ewm(alpha=1/3, adjust=False).mean()
    df['DVAL'] = df['KVAL'].ewm(alpha=1/3, adjust=False).mean()
    df['J_V']  = (3 * df['KVAL']) - (2 * df['DVAL'])
    df['GIRO_J']   = df['J_V'] > df['J_V'].shift(1)
    df['CROSS_KD'] = (df['KVAL'] > df['DVAL']) & (df['KVAL'].shift(1) <= df['DVAL'].shift(1))

    # MACD
    df['DIF']   = df['Close'].ewm(span=12, adjust=False).mean() - df['Close'].ewm(span=26, adjust=False).mean()
    df['DEA']   = df['DIF'].ewm(span=9, adjust=False).mean()
    df['HISTO'] = df['DIF'] - df['DEA']
    df['GIRO_MACD'] = (df['HISTO'] > df['HISTO'].shift(1)) & (df['HISTO'].shift(1) <= df['HISTO'].shift(2))
    df['MACD_GIRO_NEG'] = (df['HISTO'] < 0) & (df['HISTO'] < df['HISTO'].shift(1)) & (df['HISTO'].shift(1) < df['HISTO'].shift(2))

    # RSI CORREGIDO A SUMAS DE SG6
    df['OSC'] = calcular_rsi_sumas_sg6(df['Close'], periodo=14)

    # BOLLINGER Y VOLUMEN MULTICAPA
    df['BB_MID'] = df['Close'].rolling(20).mean()
    df['BB_STD'] = df['Close'].rolling(20).std(ddof=0)
    df['BB_DN']  = df['BB_MID'] - (2 * df['BB_STD'])
    
    df['VOL_MA'] = df['Volume'].rolling(20).mean()
    df['VOL_OK']   = df['Volume'] > df['VOL_MA'] * 1.05
    df['VOL_MED']  = df['Volume'] > df['VOL_MA'] * 1.2
    df['VOL_ALT']  = df['Volume'] > df['VOL_MA'] * 1.4
    df['VOL_SOFT'] = df['Volume'] > df['VOL_MA'] * 0.9

    # ================================================================
    # GATILLOS EQUIVALENTES AL 100% CON TU GRÁFICO SG6
    # ================================================================
    df['S_PULL'] = (df['Low'] < df['MA50'] * 1.015) & (df['Close'] > df['MA50'] * 0.985) & df['GIRO_J'] & df['VOL_OK'] & df['FILTRO_BASE']
    df['S_IMPU'] = (df['Close'] > df['High'].shift(1).rolling(5).max()) & (df['ADX_V'] > df['ADX_REQ']) & df['MA20_UP'] & df['GIRO_J'] & df['VOL_OK']
    df['S_BOLL'] = (df['Low'].shift(1) <= df['BB_DN']) & (df['Close'] > df['BB_DN']) & df['GIRO_J'] & df['GIRO_MACD'] & df['VOL_OK'] & df['FILTRO_BASE']
    df['S_SUELO'] = (df['OSC'] < 32) & (df['J_V'] < 22) & (df['Low'].shift(1) <= df['BB_DN']) & (df['Close'] > df['BB_DN']) & (df['Close'] > df['Low'].shift(1)) & df['GIRO_MACD'] & df['VOL_SOFT']
    
    df['CROSS_MACD'] = (df['DIF'] > df['DEA']) & (df['DIF'].shift(1) <= df['DEA'].shift(1))
    df['S_MACD_CROSS'] = df['CROSS_MACD'] & (df['DIF'] < 0) & (df['HISTO'] > df['HISTO'].shift(1)) & (df['Close'] > df['MA20']) & df['MA20_UP'] & df['VOL_OK'] & df['FILTRO_BASE']
    df['S_EARLY'] = (df['OSC'] < 38) & (df['J_V'] < 30) & df['CROSS_KD'] & (df['Close'] > df['Close'].shift(1)) & df['MA20_UP'] & df['VOL_SOFT'] & df['FILTRO_BASE']

    # GATILLOS EXCLUSIVOS SG4/SG6
    df['S_REBOTE_MA50'] = (df['Low'] <= df['MA50'] * 1.008) & (df['Close'] > df['MA50']) & (df['Close'] > df['BB_DN']) & (df['Close'] < df['BB_MID']) & df['GIRO_J'] & df['MA20_UP'] & df['F_ALCISTA'] & (df['Volume'] > df['VOL_MA'] * 0.95)
    df['S_REBOTE_MA200'] = (df['Low'] <= df['MA200'] * 1.01) & (df['Close'] > df['MA200']) & (df['Close'] > df['Low'].shift(1)) & df['GIRO_J'] & df['MA20_UP'] & (df['Volume'] > df['VOL_MA'] * 0.95)
    df['S_BOLL_SOFT'] = (df['Low'].shift(1) <= df['BB_DN']) & (df['Close'] > df['BB_DN']) & (df['Close'] > df['Low'].shift(1)) & df['GIRO_J'] & df['VOL_SOFT'] & df['FILTRO_BASE'] & ~df['MACD_GIRO_NEG']

    # LOGICA DE ASIGNACIÓN POR BANDA
    is_bc, is_vol = df['BANDA'] == "BC", df['BANDA'] == "VOL"
    s_bc_valid = df['S_PULL'] | df['S_IMPU'] | df['S_BOLL'] | df['S_SUELO'] | df['S_MACD_CROSS'] | df['S_EARLY'] | df['S_REBOTE_MA50'] | df['S_REBOTE_MA200'] | df['S_BOLL_SOFT']
    s_vol_valid = df['S_IMPU'] | df['S_BOLL'] | df['S_SUELO'] | df['S_MACD_CROSS'] | df['S_EARLY'] | df['S_REBOTE_MA200'] | df['S_BOLL_SOFT']
    
    df['B_RAW'] = (is_bc & s_bc_valid) | (is_vol & s_vol_valid)
    df['B_SIGNAL'] = df['B_RAW'] & ~df['B_RAW'].shift(1).fillna(False)

    # Duración de Señales Activas
    b_raw_list, dias_activa = df['B_RAW'].tolist(), 0
    for val in reversed(b_raw_list[-5:]):
        if val: dias_activa += 1
        else: break

    b_signal_list, duracion = df['B_SIGNAL'].tolist(), 0
    for i in range(len(b_signal_list)-1, -1, -1):
        if b_signal_list[i]:
            duracion = len(b_signal_list) - 1 - i
            break

    # TP1 Histórico
    tp_mult = 1.6 if df['BANDA'].iloc[-1] == "BC" else 2.2
    tp_ideal = df['Close'].iloc[-1] + (df['ATR_V'].iloc[-1] * tp_mult)

    e_price = None
    for i in range(len(b_signal_list)-1, -1, -1):
        if b_signal_list[i]:
            e_price = df['Close'].iloc[i]
            break

    tp1_hit = False
    if e_price is not None and duracion > 0:
        ventana_high = df['High'].iloc[-(duracion+1):]
        tp1_nivel = e_price + df['ATR_V'].iloc[-1] * tp_mult
        tp1_hit = bool(ventana_high.max() > tp1_nivel)

    # ================================================================
    # FILTRO EXACTO DE RECOMPRAS (ADD)
    # ================================================================
    i = len(df) - 1
    add_bc = (dias_activa > 0 and df['BANDA'].iloc[i] == "BC" and df['PDI_A'].iloc[i] > df['MDI_A'].iloc[i] and df['ADX_A'].iloc[i] > 28 and bool(df['ADX_A_ACCEL'].iloc[i]) and bool(df['CROSS_KD'].iloc[i]) and df['KVAL'].iloc[i] < 75 and df['Close'].iloc[i] > df['MA20'].iloc[i] and df['VOL_MED'].iloc[i] and not tp1_hit)
    add_vol = (dias_activa > 0 and df['BANDA'].iloc[i] == "VOL" and df['PDI_A'].iloc[i] > df['MDI_A'].iloc[i] and df['ADX_A'].iloc[i] > 32 and bool(df['ADX_A_ACCEL'].iloc[i]) and df['Close'].iloc[i] > df['High'].iloc[max(0,i-3):i].max() and df['Close'].iloc[i] > df['MA20'].iloc[i] and df['VOL_ALT'].iloc[i] and not tp1_hit)
    add_senal = "ADD-BC" if add_bc else ("ADD-VOL" if add_vol else None)

    # Construcción de string de Gatillos
    gatillos = []
    if dias_activa > 0:
        for nombre, col in [("S_PULL","S_PULL"), ("S_IMPU","S_IMPU"), ("S_BOLL","S_BOLL"), ("S_SUELO","S_SUELO"), ("S_MACD_CROSS","S_MACD_CROSS"), ("S_EARLY","S_EARLY"), ("S_REBOTE_MA50","S_REBOTE_MA50"), ("S_REBOTE_MA200","S_REBOTE_MA200"), ("S_BOLL_SOFT","S_BOLL_SOFT")]:
            if df[col].iloc[-1]: gatillos.append(nombre)

    if add_senal: gatillos.append(f"⚡{add_senal}")

    # RADAR DE SUELOS (Ajustado a tus parámetros Moomoo)
    df['OJO'] = ((df['OSC'] < 32) & (df['J_V'] < 25) & (df['Close'] < df['BB_DN'])).fillna(False)
    df['CRUCE_J'] = ((df['J_V'] > 10) & (df['J_V'].shift(1).fillna(100) <= 10)).fillna(False)
    df['BTD'] = (df['OJO'].shift(1).fillna(False) & df['CRUCE_J'] & df['GIRO_MACD'].fillna(False)).fillna(False)

    return {
        "Ticker": ticker_name,
        "Fecha": ultima_fecha,
        "Banda": df['BANDA'].iloc[-1],
        "Precio": round(float(df['Close'].iloc[-1]), 2),
        "RSI": round(float(df['OSC'].iloc[-1]), 2),
        "ADX": round(float(df['ADX_V'].iloc[-1]), 2),
        "J_V": round(float(df['J_V'].iloc[-1]), 2),
        "BB_DN": round(float(df['BB_DN'].iloc[-1]), 2),
        "Dias_Activa": dias_activa,
        "Duracion": duracion,
        "Gatillos": ", ".join(gatillos) if gatillos else "—",
        "TP1": round(float(tp_ideal), 2),
        "Radar_OJO": bool(df['OJO'].iloc[-2:].any()),
        "Radar_BTD": bool(df['BTD'].iloc[-2:].any()),
        "Add_Senal": add_senal,
    }, None

# ======================================================================
# CONTROLADOR DE RENDER SIDEBAR Y INTERFAZ DE RENDERIZADO
# ======================================================================
with st.sidebar:
    st.title("Configuración SG6")
    periodo    = st.selectbox("Periodo histórico", ["2y","1y","6mo"], index=0)
    rsi_umbral = st.slider("Umbral RSI sobreventa", 25, 45, 32)
    dias_max   = st.slider("Señal activa max. días", 1, 5, 3)
    usar_gex   = st.toggle("Incluir Put/Call Wall (GEX)", value=True)
    st.markdown("---")
    st.markdown("**Watchlist Personalizada**")
    tickers_input = st.text_area("Un ticker por línea o comas (Vacío = Lista Base)", height=140)
    st.markdown("---")
    ejecutar = st.button("🚀 Ejecutar escáner", use_container_width=True, type="primary")

if not ejecutar:
    st.info("Configura los parámetros en la barra lateral y presiona Ejecutar escáner.")
    st.stop()

if tickers_input.strip():
    tickers = [t.strip().upper() for t in tickers_input.replace(',','\n').splitlines() if t.strip()]
    tickers = list(dict.fromkeys(tickers))
else:
    tickers = TICKERS_DEFAULT

# Procesamiento en Paralelo/Bucle
lista_compras, lista_rsi, lista_radar, lista_desc = [], [], [], []
progreso = st.progress(0, text="Iniciando...")
col1, col2, col3 = st.columns(3)
m_compras, m_rsi, m_radar = col1.empty(), col2.empty(), col3.empty()

for idx, ticker in enumerate(tickers):
    pct = int((idx + 1) / len(tickers) * 100)
    progreso.progress(pct, text=f"Procesando {ticker}... ({idx+1}/{len(tickers)})")
    
    try:
        df = yf.download(ticker, period=periodo, progress=False, auto_adjust=True)
        if df.empty: continue
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

        datos, motivo = analizar_ticker(df, ticker)
        if datos is None: continue

        gex = calcular_gex(ticker, datos["Precio"]) if usar_gex and not any(x in ticker for x in ['-USD', 'ETH', 'BTC', 'SOL']) else None
        put_wall  = gex["Put Wall"] if gex else "—"
        call_wall = gex["Call Wall"] if gex else "—"
        gex_ctx   = gex["GEX"] if gex else "—"

        if (0 < datos["Dias_Activa"] <= dias_max) or (datos["Add_Senal"] is not None):
            lista_compras.append({
                "Ticker": datos["Ticker"], "Fecha": datos["Fecha"], "Banda": datos["Banda"],
                "Dias": f"Activa {datos['Dias_Activa']}d" if datos["Dias_Activa"] > 0 else f"Abierta {datos['Duracion']}d",
                "Gatillos": datos["Gatillos"], "Precio": datos["Precio"], "RSI": datos["RSI"],
                "ADX": datos["ADX"], "TP1": datos["TP1"], "Put Wall": put_wall, "Call Wall": call_wall, "GEX": gex_ctx
            })

        if datos["RSI"] < rsi_umbral:
            lista_rsi.append({
                "Ticker": datos["Ticker"], "Fecha": datos["Fecha"], "Banda": datos["Banda"], "Precio": datos["Precio"],
                "RSI": datos["RSI"], "J_V": datos["J_V"], "ADX": datos["ADX"], "Put Wall": put_wall, "Call Wall": call_wall, "GEX": gex_ctx
            })

        if datos["Radar_BTD"] or datos["Radar_OJO"]:
            lista_radar.append({
                "Ticker": datos["Ticker"], "Señal": "🟢 BTD" if datos["Radar_BTD"] else "🟡 OJO", "Banda": datos["Banda"],
                "Precio": datos["Precio"], "RSI": datos["RSI"], "J_V": datos["J_V"], "BB_DN": datos["BB_DN"], "Put Wall": put_wall, "Call Wall": call_wall, "GEX": gex_ctx
            })

    except Exception as e:
        lista_desc.append({"Ticker": ticker, "Motivo": str(e)[:50]})

progreso.empty()
st.success(f"✅ Escáner completado con éxito.")
m_compras.metric("🚀 Compras frescas", len(lista_compras))
m_rsi.metric(f"📉 RSI < {rsi_umbral}", len(lista_rsi))
m_radar.metric("🎯 Radar OJO/BTD", len(lista_radar))

tab1, tab2, tab3 = st.tabs([f"🚀 Compras + ADD ({len(lista_compras)})", f"📉 Sobreventa RSI ({len(lista_rsi)})", f"🎯 Radar OJO/BTD ({len(lista_radar)})"])

with tab1:
    if lista_compras:
        df1 = pd.DataFrame(lista_compras)
        st.dataframe(df1.style.map(lambda v: "background-color:#1a3d2b" if v == "BC" else "background-color:#3d2e0a", subset=["Banda"]), use_container_width=True, hide_index=True)
    else: st.info("Sin señales para hoy.")

with tab2:
    if lista_rsi: st.dataframe(pd.DataFrame(lista_rsi).sort_values("RSI"), use_container_width=True, hide_index=True)
    else: st.info("Sin activos en sobreventa extrema.")

with tab3:
    if lista_radar: st.dataframe(pd.DataFrame(lista_radar), use_container_width=True, hide_index=True)
    else: st.info("Radar despejado.")

```
