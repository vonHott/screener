# ======================================================================
# SCRIPT SANTO GRIAL 3 - TABLERO V8 , con rebote mas weno
# NOVEDADES V8:
#   - Nuevo gatillo S_REBOTE_MA50: rebote en MA50 con volumen relajado
#     contenido exclusivamente a ese patrón (no contamina el resto)
#   - Condición: toca MA50 + cierra sobre ella + entre BB_DN y BB_MID
#     + GIRO_J + MA20 ascendente + VOL > 95% VOL_MA
#   - Gatillo disponible solo en banda BC (tendencias limpias)
#   - Log de descartados integrado
#   - RSI Wilder exacto (= Moomoo/TradingView)
#   - Download 2y para calentamiento suficiente
# ======================================================================
!pip install yfinance pandas numpy -q

import yfinance as yf
import pandas as pd
import numpy as np
from IPython.display import display
import warnings
warnings.filterwarnings('ignore')

# ======================================================================
# 1. WATCHLIST
# ======================================================================
tickers_raw = [
    "CHWY", "ALT", "PLTR", "RBRK", "MORN", "CBRS", "LINK-USD", "AVAX-USD", "ISRG", "MDT",
    "NASA", "DG", "EPAM", "BRK-B", "NCLH", "XYZ", "CLS", "GILD", "FSLR", "RTX", "PSX",
    "NBIS", "ZTS", "IGV", "FICO", "BAC", "GS", "NOW", "HMC", "SIDU", "RMBS", "MRVL",
    "COF", "BHP", "ETH-USD", "SOL-USD", "BTI", "SAP", "OTIS", "FDX", "ESLT", "TME", "BLZE",
    "INTU", "SONY", "LITE", "COHR", "GDDY", "PM", "TSM", "CRDO", "NNE", "CRWV", "HUM",
    "NRG", "HII", "GFI", "BLK", "ENPH", "CLX", "NVAX", "LMT", "ZBH", "PSKY", "FIG", "DPZ",
    "D", "IONQ", "KEYS", "VRT", "VRTX", "MSFT", "AAPL", "MMM", "HD", "GOOGL", "EBAY",
    "SOFI", "MPWR", "LULU", "CPRT", "ETN", "ELV", "TJX", "ADP", "NEE", "DHR", "CL", "T",
    "B", "VZ", "QQQ", "MU", "IGM", "TXN", "PATH", "OKTA", "ZS", "AFRM", "GME", "BABA",
    "RIOT", "ARM", "XLP", "XLK", "XLI", "XLV", "CLF", "XLE", "IWM", "SPY", "UBER", "PYPL",
    "INTC", "LRCX", "AMAT", "REGN", "U", "SHOP", "HOOD", "NET", "CRWD", "DDOG", "SNOW",
    "MDB", "MARA", "COIN", "AVGO", "TX", "CSCO", "ACN", "LIN", "TMO", "LLY", "ABBV",
    "ABNB", "MRNA", "BMNR", "AMT", "ASTS", "PANW", "UL", "APH", "SMCI", "DELL", "SNDK",
    "ANET", "STX", "WDC", "RCL", "BKNG", "TMUS", "MNST", "DE", "CRM", "ADBE", "TGT",
    "COST", "CVX", "XOM", "GE", "CI", "ABT", "AMZN", "QTUM", "IYW", "BTC-USD", "SOUN",
    "IBM", "IP", "ARKQ", "SMH", "URA", "BITX", "ETHU", "CEG", "NVO", "CRML", "UA", "XT",
    "MRK", "SPOT", "EQIX", "BA", "FCX", "AEM", "MSTR", "PEP", "KO", "WMT", "PFE", "DIS",
    "O", "JNJ", "MCD", "JPM", "WM", "MA", "CAT", "SBUX", "CRCL", "PG", "RACE", "UNH",
    "NVDA", "NFLX", "MELI", "NKE", "CMCSA", "META", "ORCL", "ASML", "TSLA", "AMD",
    "QQQM", "VOO", "ACHR"
]

# ======================================================================
# 2. RSI WILDER EXACTO (= MOOMOO / TRADINGVIEW)
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
            avg_gain[i] = (avg_gain[i - 1] * (periodo - 1) + gain.iloc[i]) / periodo
            avg_loss[i] = (avg_loss[i - 1] * (periodo - 1) + loss.iloc[i]) / periodo

    avg_loss_safe = np.where(avg_loss == 0, 1e-8, avg_loss)
    rs = avg_gain / avg_loss_safe
    rsi = 100 - (100 / (1 + rs))
    rsi[:periodo] = np.nan
    return pd.Series(rsi, index=close_series.index)

# ======================================================================
# 3. FUNCIÓN PRINCIPAL DE ANÁLISIS
# ======================================================================
def analizar_ticker(df, ticker_name):
    df = df.dropna(subset=['Close', 'Volume'])
    df = df[df['Volume'] > 0].copy()
    if len(df) < 250:
        return None, f"Pocas velas: {len(df)}"

    ultima_fecha = df.index[-1].strftime('%Y-%m-%d')

    # --- BANDA ---
    df['RET_V']    = df['Close'].pct_change() * 100
    df['BETA_RAW'] = df['RET_V'].rolling(60).std(ddof=0)
    df['BETA_S']   = df['BETA_RAW'].rolling(20).mean()
    df['BANDA']    = np.where(df['BETA_S'] < 1.4, "BC", "VOL")

    # --- MEDIAS ---
    df['MA20']  = df['Close'].ewm(span=20,  adjust=False).mean()
    df['MA50']  = df['Close'].ewm(span=50,  adjust=False).mean()
    df['MA200'] = df['Close'].ewm(span=200, adjust=False).mean()
    df['F_BAJISTA']  = df['Close'] < df['MA200']
    df['MA20_UP']    = df['MA20'] > df['MA20'].shift(1)
    df['FILTRO_BASE'] = df['Close'] >= df['MA200']

    # --- ATR ---
    df['H_L']  = df['High'] - df['Low']
    df['H_PC'] = (df['High'] - df['Close'].shift(1)).abs()
    df['L_PC'] = (df['Low']  - df['Close'].shift(1)).abs()
    df['TR_V'] = df[['H_L', 'H_PC', 'L_PC']].max(axis=1)
    df['ATR_V'] = df['TR_V'].rolling(14).mean()

    # --- ADX ---
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

    # --- KDJ ---
    low_min   = df['Low'].rolling(9).min()
    high_max  = df['High'].rolling(9).max()
    denom_kdj = (high_max - low_min).replace(0, 1e-8)
    df['RSV']  = (df['Close'] - low_min) / denom_kdj * 100
    df['KVAL'] = df['RSV'].ewm(alpha=1/3, adjust=False).mean()
    df['DVAL'] = df['KVAL'].ewm(alpha=1/3, adjust=False).mean()
    df['J_V']  = (3 * df['KVAL']) - (2 * df['DVAL'])
    df['GIRO_J'] = df['J_V'] > df['J_V'].shift(1)

    # --- MACD ---
    df['DIF']   = (df['Close'].ewm(span=12, adjust=False).mean()
                 - df['Close'].ewm(span=26, adjust=False).mean())
    df['DEA']   = df['DIF'].ewm(span=9, adjust=False).mean()
    df['HISTO'] = df['DIF'] - df['DEA']
    df['GIRO_MACD'] = (
        (df['HISTO'] > df['HISTO'].shift(1)) &
        (df['HISTO'].shift(1) <= df['HISTO'].shift(2))
    )

    # --- RSI WILDER ---
    df['OSC'] = calcular_rsi_wilder(df['Close'], periodo=14)

    # --- BOLLINGER Y VOLUMEN ---
    df['BB_MID'] = df['Close'].rolling(20).mean()
    df['BB_STD'] = df['Close'].rolling(20).std(ddof=0)
    df['BB_UP']  = df['BB_MID'] + (2 * df['BB_STD'])
    df['BB_DN']  = df['BB_MID'] - (2 * df['BB_STD'])
    df['VOL_MA'] = df['Volume'].rolling(20).mean()

    # ================================================================
    # GATILLOS ORIGINALES SG3
    # ================================================================
    df['S_PULL'] = (
        (df['Low'] < df['MA50'] * 1.015) &
        (df['Close'] > df['MA50'] * 0.985) &
        df['GIRO_J'] &
        (df['Volume'] > df['VOL_MA'] * 1.05) &
        df['FILTRO_BASE']
    )
    df['S_IMPU'] = (
        (df['Close'] > df['High'].shift(1).rolling(5).max()) &
        (df['ADX_V'] > df['ADX_REQ']) &
        df['MA20_UP'] &
        df['GIRO_J'] &
        (df['Volume'] > df['VOL_MA'] * 1.05)
    )
    df['S_BOLL'] = (
        (df['Low'].shift(1) <= df['BB_DN']) &
        (df['Close'] > df['BB_DN']) &
        df['GIRO_J'] &
        df['GIRO_MACD'] &
        (df['Volume'] > df['VOL_MA'] * 1.05) &
        df['FILTRO_BASE']
    )
    df['S_SUELO'] = (
        (df['OSC'] < 32) &
        (df['J_V'] < 22) &
        (df['Low'].shift(1) <= df['BB_DN']) &
        (df['Close'] > df['BB_DN']) &
        (df['Close'] > df['Low'].shift(1)) &
        df['GIRO_MACD'] &
        (df['Volume'] > df['VOL_MA'] * 0.9)
    )
    df['CROSS_MACD'] = (df['DIF'] > df['DEA']) & (df['DIF'].shift(1) <= df['DEA'].shift(1))
    df['S_MACD_CROSS'] = (
        df['CROSS_MACD'] &
        (df['DIF'] < 0) &
        (df['HISTO'] > df['HISTO'].shift(1)) &
        (df['Close'] > df['MA20']) &
        df['MA20_UP'] &
        (df['Volume'] > df['VOL_MA'] * 1.05) &
        df['FILTRO_BASE']
    )
    df['CROSS_KD'] = (df['KVAL'] > df['DVAL']) & (df['KVAL'].shift(1) <= df['DVAL'].shift(1))
    df['S_EARLY'] = (
        (df['OSC'] < 38) &
        (df['J_V'] < 30) &
        df['CROSS_KD'] &
        (df['Close'] > df['Close'].shift(1)) &
        df['MA20_UP'] &
        (df['Volume'] > df['VOL_MA'] * 0.9) &
        df['FILTRO_BASE']
    )

    # ================================================================
    # NUEVO GATILLO V8 — S_REBOTE_MA50
    # ================================================================
    # Contexto: precio en pullback limpio hacia MA50 dentro de tendencia
    # alcista. El rebote técnico puede darse con volumen contenido porque
    # no hay pánico — es una corrección ordenada apoyada en la media.
    # Volumen relajado (95% VOL_MA) SOLO aquí, no contamina el resto.
    # Exclusivo de banda BC (activos con tendencia más limpia).
    # ================================================================
    df['S_REBOTE_MA50'] = (
        (df['Low'] <= df['MA50'] * 1.008) &      # toca o roza MA50 (margen 0.8%)
        (df['Close'] > df['MA50']) &              # cierra sobre MA50
        (df['Close'] > df['BB_DN']) &             # sobre banda inferior
        (df['Close'] < df['BB_MID']) &            # bajo banda media (no sobreextendido)
        df['GIRO_J'] &                            # KDJ girando al alza
        df['MA20_UP'] &                           # MA20 aún ascendente
        df['FILTRO_BASE'] &                       # precio sobre MA200 (alcista)
        (df['Volume'] > df['VOL_MA'] * 0.95)     # volumen relajado (único gatillo con esto)
    )

    # ================================================================
    # B_RAW POR BANDA — S_REBOTE_MA50 solo en BC
    # ================================================================
    is_bc  = df['BANDA'] == "BC"
    is_vol = df['BANDA'] == "VOL"

    s_bc_valid = (
        df['S_PULL'] | df['S_IMPU'] | df['S_BOLL'] |
        df['S_SUELO'] | df['S_MACD_CROSS'] | df['S_EARLY'] |
        df['S_REBOTE_MA50']          # <-- nuevo, solo BC
    )
    s_vol_valid = (
        df['S_IMPU'] | df['S_BOLL'] | df['S_SUELO'] |
        df['S_MACD_CROSS'] | df['S_EARLY']
        # S_REBOTE_MA50 NO incluido en VOL
    )
    df['B_RAW'] = (is_bc & s_bc_valid) | (is_vol & s_vol_valid)

    # Días consecutivos activa
    b_raw_list  = df['B_RAW'].tolist()
    dias_activa = 0
    for val in reversed(b_raw_list[-5:]):
        if val: dias_activa += 1
        else:   break

    # Gatillos activos
    gatillos = []
    if dias_activa > 0:
        for nombre, col in [
            ("S_PULL",        "S_PULL"),
            ("S_IMPU",        "S_IMPU"),
            ("S_BOLL",        "S_BOLL"),
            ("S_SUELO",       "S_SUELO"),
            ("S_MACD_CROSS",  "S_MACD_CROSS"),
            ("S_EARLY",       "S_EARLY"),
            ("S_REBOTE_MA50", "S_REBOTE_MA50"),   # nuevo
        ]:
            if df[col].iloc[-1]: gatillos.append(nombre)

    tp_mult  = 1.6 if df['BANDA'].iloc[-1] == "BC" else 2.2
    tp_ideal = df['Close'].iloc[-1] + (df['ATR_V'].iloc[-1] * tp_mult)

    # ================================================================
    # RADAR V7 CORREGIDO
    # ================================================================
    df['OJO'] = (
        (df['OSC'] < 35) &
        (df['J_V'] < 28) &
        (df['Close'] <= df['BB_DN'] * 1.01)
    ).fillna(False)
    df['CRUCE_J'] = (
        (df['J_V'] > 10) &
        (df['J_V'].shift(1).fillna(100) <= 12)
    ).fillna(False)
    df['BTD'] = (
        df['OJO'].shift(1).fillna(False) &
        df['CRUCE_J'] &
        df['GIRO_MACD'].fillna(False)
    ).fillna(False)

    ojo_reciente = bool(df['OJO'].iloc[-2:].any())
    btd_reciente = bool(df['BTD'].iloc[-2:].any())

    return {
        "Ticker":       ticker_name,
        "Fecha_Vela":   ultima_fecha,
        "Banda":        df['BANDA'].iloc[-1],
        "Precio":       round(float(df['Close'].iloc[-1]), 2),
        "RSI":          round(float(df['OSC'].iloc[-1]), 1),
        "ADX":          round(float(df['ADX_V'].iloc[-1]), 1),
        "J_V":          round(float(df['J_V'].iloc[-1]), 1),
        "BB_DN":        round(float(df['BB_DN'].iloc[-1]), 2),
        "Dias_Activa":  dias_activa,
        "Gatillos":     ", ".join(gatillos) if gatillos else "—",
        "TP1":          round(float(tp_ideal), 2),
        "Radar_OJO":    ojo_reciente,
        "Radar_BTD":    btd_reciente,
    }, None

# ======================================================================
# 4. MOTOR DE EJECUCIÓN
# ======================================================================
print("Iniciando Escáner SG3 V8 (+ S_REBOTE_MA50)...\n")
lista_compras  = []
lista_rsi      = []
lista_radar    = []
lista_desc     = []
procesados     = 0

for ticker in tickers_raw:
    try:
        df = yf.download(ticker, period="2y", progress=False, auto_adjust=True)
        if df.empty:
            lista_desc.append({"Ticker": ticker, "Motivo": "Sin datos en yfinance"})
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        datos, motivo = analizar_ticker(df, ticker)

        if datos is None:
            lista_desc.append({"Ticker": ticker, "Motivo": motivo})
            continue

        # --- SECCIÓN 1: Compras frescas 1–3 días ---
        if 0 < datos["Dias_Activa"] <= 3:
            estado_str = ("Día 1 (Ayer/Hoy)" if datos["Dias_Activa"] == 1
                          else f"Activa hace {datos['Dias_Activa']}d")
            lista_compras.append({
                "Ticker":    datos["Ticker"],
                "Fecha":     datos["Fecha_Vela"],
                "Banda":     datos["Banda"],
                "Antigüedad": estado_str,
                "Gatillos":  datos["Gatillos"],
                "Precio":    datos["Precio"],
                "RSI":       datos["RSI"],
                "ADX":       datos["ADX"],
                "TP1":       datos["TP1"],
            })

        # --- SECCIÓN 2: RSI < 33 ---
        if datos["RSI"] < 33:
            lista_rsi.append({
                "Ticker":  datos["Ticker"],
                "Fecha":   datos["Fecha_Vela"],
                "Banda":   datos["Banda"],
                "Precio":  datos["Precio"],
                "RSI":     datos["RSI"],
                "J_V":     datos["J_V"],
                "ADX":     datos["ADX"],
            })

        # --- SECCIÓN 3: Radar OJO / BTD ---
        if datos["Radar_BTD"]:
            lista_radar.append({
                "Ticker": datos["Ticker"],
                "Señal":  "🟢 BTD",
                "Banda":  datos["Banda"],
                "Precio": datos["Precio"],
                "RSI":    datos["RSI"],
                "J_V":    datos["J_V"],
                "BB_DN":  datos["BB_DN"],
            })
        elif datos["Radar_OJO"]:
            lista_radar.append({
                "Ticker": datos["Ticker"],
                "Señal":  "🟡 OJO",
                "Banda":  datos["Banda"],
                "Precio": datos["Precio"],
                "RSI":    datos["RSI"],
                "J_V":    datos["J_V"],
                "BB_DN":  datos["BB_DN"],
            })

    except Exception as e:
        lista_desc.append({"Ticker": ticker, "Motivo": f"Error: {str(e)[:60]}"})

    procesados += 1
    if procesados % 30 == 0:
        print(f"Procesando... ({procesados}/{len(tickers_raw)} completados)")

# ======================================================================
# 5. REPORTE FINAL
# ======================================================================
sep = "=" * 80

print(f"\n{sep}")
print(" 🚀 SECCIÓN 1: COMPRAS FRESCAS (SEÑAL ACTIVA 1–3 DÍAS)")
print(sep)
if lista_compras:
    df1 = pd.DataFrame(lista_compras)
    df1.index = np.arange(1, len(df1) + 1)
    display(df1)
else:
    print("Ninguna compra fresca reciente.")

print(f"\n{sep}")
print(" 📉 SECCIÓN 2: SCREENER SOBREVENTA (RSI WILDER < 33)")
print(sep)
if lista_rsi:
    df2 = pd.DataFrame(lista_rsi).sort_values("RSI")
    df2.index = np.arange(1, len(df2) + 1)
    display(df2)
else:
    print("Ningún activo en sobreventa extrema hoy.")

print(f"\n{sep}")
print(" 🎯 SECCIÓN 3: RADAR TEMPRANO (OJO y BTD — ventana 2 barras)")
print(sep)
if lista_radar:
    df3 = pd.DataFrame(lista_radar)
    df3['_ord'] = df3['Señal'].apply(lambda x: 0 if 'BTD' in x else 1)
    df3 = df3.sort_values(['_ord', 'RSI']).drop(columns='_ord')
    df3.index = np.arange(1, len(df3) + 1)
    display(df3)
else:
    print("Sin alertas tempranas de formación de suelo.")

print(f"\n{sep}")
print(" ⚠️  TICKERS DESCARTADOS")
print(sep)
if lista_desc:
    df4 = pd.DataFrame(lista_desc)
    df4.index = np.arange(1, len(df4) + 1)
    display(df4)
else:
    print("Ninguno descartado.")

print(f"\n✅ Escáner V8 completado. Total procesados: {procesados}")
print(f"   Compras: {len(lista_compras)} | Sobreventa: {len(lista_rsi)} | Radar: {len(lista_radar)} | Descartados: {len(lista_desc)}")
