"""
CRH V3 — port fiel del indicador M-language de Moomoo a Python.

Fuente: CRH.ftindex (CRH V3 / CARLOS REINALDO HIBRIDO / DIARIO)

Cada bloque conserva la numeracion y los nombres del original para que
puedas comparar linea a linea contra el .ftindex.

Equivalencias de M-language usadas:
    REF(X,n)        -> X.shift(n)
    MA(X,n)         -> media simple
    EMA(X,n)        -> ewm(span=n, adjust=False)
    SMA(X,n,m)      -> ewm(alpha=m/n, adjust=False)   [SMA china de Moomoo]
    STD(X,n)        -> desviacion estandar muestral (ddof=1)
    HHV/LLV(X,n)    -> rolling max / min
    SUM(X,n)        -> rolling sum
    COUNT(c,n)      -> rolling sum de booleanos
    CROSS(A,B)      -> A>B y previo A<=B
    VALUEWHEN(c,X)  -> valor de X en la ultima vez que c fue cierto
    BARSLAST(c)     -> barras transcurridas desde la ultima vez que c fue cierto
"""

import numpy as np
import pandas as pd

BIG = 10**6  # sustituto de "nunca ocurrio" para BARSLAST


# ===========================================================================
# PRIMITIVAS M-LANGUAGE
# ===========================================================================

def REF(s, n):
    return s.shift(n)


def MA(s, n):
    return s.rolling(n, min_periods=n).mean()


def EMA(s, n):
    return s.ewm(span=n, adjust=False).mean()


def SMA(s, n, m):
    """SMA china de Moomoo: y = (m*x + (n-m)*y_prev) / n"""
    return s.ewm(alpha=m / n, adjust=False).mean()


def STD(s, n):
    return s.rolling(n, min_periods=n).std(ddof=1)


def HHV(s, n):
    return s.rolling(n, min_periods=1).max()


def LLV(s, n):
    return s.rolling(n, min_periods=1).min()


def SUM(s, n):
    return s.rolling(n, min_periods=n).sum()


def COUNT(cond, n):
    return cond.astype(float).rolling(n, min_periods=1).sum()


def CROSS(a, b):
    return (a > b) & (a.shift(1) <= b.shift(1))


def IF(cond, a, b):
    return pd.Series(np.where(cond, a, b), index=cond.index)


def MAXS(a, b):
    return pd.Series(np.maximum(a, b), index=a.index if hasattr(a, "index") else b.index)


def MINS(a, b):
    return pd.Series(np.minimum(a, b), index=a.index if hasattr(a, "index") else b.index)


def BARSLAST(cond):
    """Barras desde la ultima vez que cond fue True. 0 si es True ahora."""
    c = cond.fillna(False).astype(bool).values
    n = len(c)
    out = np.full(n, BIG, dtype=float)
    last = -1
    for i in range(n):
        if c[i]:
            last = i
        out[i] = (i - last) if last >= 0 else BIG
    return pd.Series(out, index=cond.index)


def VALUEWHEN(cond, x):
    """Valor de x en la ultima barra donde cond fue True."""
    c = cond.fillna(False).astype(bool)
    return x.where(c).ffill()


def HHV_DESDE_ENTRADA(serie, senal):
    """
    Equivalente a HHV(serie, DURACION+1): maximo desde la barra de entrada
    inclusive. Se resuelve agrupando por bloque de operacion.
    """
    bloque = senal.fillna(False).astype(int).cumsum()
    return serie.groupby(bloque).cummax()


def HHV_VENTANA_VARIABLE(serie, ventanas):
    """HHV con largo de ventana distinto en cada barra."""
    v = serie.values
    w = ventanas.fillna(1).astype(int).clip(lower=1).values
    n = len(v)
    out = np.empty(n)
    for i in range(n):
        ini = max(0, i - w[i] + 1)
        out[i] = np.nanmax(v[ini:i + 1])
    return pd.Series(out, index=serie.index)


# ===========================================================================
# CRH V5
# ===========================================================================

def crh(df):
    """
    df debe traer columnas: open, high, low, close, volume (minusculas),
    ordenado de mas antiguo a mas reciente.

    Devuelve el mismo df con todas las variables del indicador agregadas.
    """
    d = df.copy()
    CLOSE = d["close"]
    HIGH = d["high"]
    LOW = d["low"]
    OPEN = d["open"]
    VOL = d["volume"]

    # --- 1. CLASIFICACION DE BANDA ------------------------------------
    RET_V = (CLOSE - REF(CLOSE, 1)) / REF(CLOSE, 1) * 100
    BETA_RAW = STD(RET_V, 60)
    BETA_SMOOTH = MA(BETA_RAW, 20)
    BANDA_PRE = IF(BETA_SMOOTH < 1.0, 1, IF(BETA_SMOOTH < 1.8, 2, 3))

    # --- 2. MEDIAS Y CONTEXTO MACRO -----------------------------------
    MA20 = EMA(CLOSE, 20)
    MA50 = EMA(CLOSE, 50)
    MA200 = EMA(CLOSE, 200)
    MA20_UP = MA20 > REF(MA20, 1)
    MA50_SUBE = MA50 > REF(MA50, 3)
    EMA200_BAJA = MA200 < REF(MA200, 1)
    ES_BAJISTA_CRITICO = (CLOSE < MA200) & EMA200_BAJA & (CLOSE < MA20)
    EN_TENDENCIA = COUNT((CLOSE > MA50) & MA50_SUBE & (MA50 > MA200), 5) >= 3
    TENDENCIA_VIVA_MACRO = (CLOSE > MA50) & MA20_UP

    # --- 3. ATR WILDER -------------------------------------------------
    TR_V1 = MAXS(HIGH - LOW, (HIGH - REF(CLOSE, 1)).abs())
    TR_V = MAXS(TR_V1, (LOW - REF(CLOSE, 1)).abs())
    ATR_V = SMA(TR_V, 14, 1)

    # --- 4. ADX --------------------------------------------------------
    HD = HIGH - REF(HIGH, 1)
    LD = REF(LOW, 1) - LOW
    DMP = SUM(IF((HD > 0) & (HD > LD), HD, 0), 14)
    DMM = SUM(IF((LD > 0) & (LD > HD), LD, 0), 14)
    TR14 = SUM(TR_V, 14)
    PDI = DMP * 100 / TR14
    MDI = DMM * 100 / TR14
    ADX_V = MA((PDI - MDI).abs() / (PDI + MDI) * 100, 9)
    ADX_REQ = IF(ES_BAJISTA_CRITICO, 28, IF(BANDA_PRE == 3, 22, 18))

    # ADX corto para ADD
    TR6 = SUM(TR_V, 6)
    PDI_A = SUM(IF((HD > 0) & (HD > LD), HD, 0), 6) * 100 / TR6
    MDI_A = SUM(IF((LD > 0) & (LD > HD), LD, 0), 6) * 100 / TR6
    ADX_A = MA((PDI_A - MDI_A).abs() / (PDI_A + MDI_A) * 100, 6)
    ADX_A_ACCEL = (ADX_A > REF(ADX_A, 1)) & (REF(ADX_A, 1) > REF(ADX_A, 2))

    # --- 5. KDJ --------------------------------------------------------
    RSV = (CLOSE - LLV(LOW, 9)) / (HHV(HIGH, 9) - LLV(LOW, 9)) * 100
    KVAL = SMA(RSV, 3, 1)
    DVAL = SMA(KVAL, 3, 1)
    J_V = (3 * KVAL) - (2 * DVAL)
    GIRO_J = J_V > REF(J_V, 1)
    CROSS_KD = CROSS(KVAL, DVAL)

    # --- 6. MACD -------------------------------------------------------
    DIF = EMA(CLOSE, 12) - EMA(CLOSE, 26)
    DEA = EMA(DIF, 9)
    HISTO = DIF - DEA
    GIRO_MACD = (HISTO > REF(HISTO, 1)) & (REF(HISTO, 1) <= REF(HISTO, 2))
    MACD_CONV_ALCI = (HISTO < 0) & (HISTO > REF(HISTO, 1)) & (HISTO > REF(HISTO, 2))
    TENDENCIA_VIVA = ((DIF > 0) | MACD_CONV_ALCI) & MA20_UP & (PDI > MDI) & (CLOSE > MA50)

    # --- 7. RSI NATIVO -------------------------------------------------
    LC = REF(CLOSE, 1)
    RSI_UP = SUM(MAXS(CLOSE - LC, pd.Series(0.0, index=CLOSE.index)), 14)
    RSI_DN = SUM(MAXS(LC - CLOSE, pd.Series(0.0, index=CLOSE.index)), 14)
    OSC = RSI_UP / (RSI_UP + RSI_DN) * 100

    # --- 8. BOLLINGER --------------------------------------------------
    BB_MID = MA(CLOSE, 20)
    BB_STD = STD(CLOSE, 20)
    BB_UP = BB_MID + (2 * BB_STD)
    BB_DN = BB_MID - (2 * BB_STD)

    # --- 9. VOLUMEN ----------------------------------------------------
    VOL_MA = MA(VOL, 20)
    VOL_OK = VOL > VOL_MA * 1.02
    VOL_MED = VOL > VOL_MA * 1.2
    VOL_ALT = VOL > VOL_MA * 1.4
    VOL_SOFT = VOL > VOL_MA * 0.88
    VOL_SECO = VOL < VOL_MA * 0.80

    # --- 10. RANGO LATERAL ---------------------------------------------
    ADX_CAYENDO = (ADX_V < REF(ADX_V, 2)) & (ADX_V < REF(ADX_V, 4))
    EN_LATERAL = ADX_CAYENDO & (CLOSE < BB_MID) & (~TENDENCIA_VIVA)

    # --- 11. GATILLOS DE ENTRADA ---------------------------------------
    MA50_ALCISTA = MA50 > REF(MA50, 5)
    VENIA_SOBRE_MA50 = COUNT(REF(CLOSE, 1) > MA50, 3) >= 2
    MA200_PLANA_O_SUBE = MA200 >= REF(MA200, 3)


    S_PULL = ((LOW < MA50 * 1.015) & (CLOSE > MA50 * 0.985) & GIRO_J
              & VOL_OK & MA50_ALCISTA & VENIA_SOBRE_MA50)

    S_IMPU = ((CLOSE > REF(HHV(HIGH, 5), 1)) & (ADX_V > ADX_REQ)
              & MA20_UP & GIRO_J & VOL_OK)

    S_BOLL = ((REF(LOW, 1) <= REF(BB_DN, 0)) & (CLOSE > BB_DN) & GIRO_J
              & GIRO_MACD & VOL_SOFT)

    S_SUELO = ((OSC < 35) & (J_V < 25) & (CLOSE > REF(LOW, 1))
               & GIRO_MACD & VOL_SOFT)

    S_MACD_CROSS = (CROSS(DIF, DEA) & (HISTO > REF(HISTO, 1))
                    & MA20_UP & VOL_OK)

    S_EARLY = ((OSC < 40) & (J_V < 30) & CROSS_KD & MA20_UP
               & VOL_SOFT)

    S_CONT = ((CLOSE > REF(HHV(HIGH, 10), 1)) & (CLOSE > MA50)
              & MA50_SUBE & GIRO_J)

    S_REBOTE_MA200 = ((LOW <= MA200 * 1.01) & (CLOSE > MA200)
                      & (CLOSE > REF(LOW, 1)) & GIRO_J & MA20_UP
                      & MA200_PLANA_O_SUBE & VOL_OK)

    TODOS = (S_PULL | S_IMPU | S_BOLL | S_SUELO | S_MACD_CROSS
             | S_EARLY | S_CONT | S_REBOTE_MA200)

    B_BC = (BANDA_PRE == 1) & TODOS
    B_HYB = (BANDA_PRE == 2) & TODOS
    B_VOL = (BANDA_PRE == 3) & (S_IMPU | S_BOLL | S_SUELO | S_MACD_CROSS
                                | S_CONT | S_REBOTE_MA200)

    B_RAW = B_BC | B_HYB | B_VOL
    B_SIGNAL = B_RAW & (~REF(B_RAW, 1).fillna(False).astype(bool))

    # --- 12. PARAMETROS FIJADOS EN VELA DE ENTRADA ---------------------
    BANDA = VALUEWHEN(B_SIGNAL, BANDA_PRE)
    E_PRICE = VALUEWHEN(B_SIGNAL, CLOSE)
    DURACION = BARSLAST(B_SIGNAL)
    ATR_ENTRY = VALUEWHEN(B_SIGNAL, ATR_V)

    SL_MULT = IF(BANDA == 1, 1.3, IF(BANDA == 2, 1.5, 1.8))
    SL_DURO = E_PRICE - (ATR_ENTRY * SL_MULT)
    SL_MAX_PCT = E_PRICE * 0.97
    SL_DURO_PRE = MAXS(SL_DURO, SL_MAX_PCT)
    SL_DURO_FINAL = MINS(SL_DURO_PRE, E_PRICE * 0.999)

    M_BASE = IF(BANDA == 1, 1.8, IF(BANDA == 2, 2.1, 2.4))
    M_DECAY = IF(BANDA == 1, 0.05, IF(BANDA == 2, 0.04, 0.03))
    M_MIN = IF(BANDA == 1, 1.2, IF(BANDA == 2, 1.4, 1.6))
    M_RAW = MAXS(M_BASE - (DURACION.clip(upper=200) * M_DECAY), M_MIN)
    MULT_T = IF(ES_BAJISTA_CRITICO, M_RAW * 0.85, M_RAW)

    # --- TP1 -----------------------------------------------------------
    TP1_MULT = IF(BANDA == 1, 1.6, IF(BANDA == 2, 2.0, 2.5))
    TP1_LEVEL = VALUEWHEN(B_SIGNAL, CLOSE + ATR_V * TP1_MULT)
    MAX_DESDE_ENTRADA = HHV_DESDE_ENTRADA(HIGH, B_SIGNAL)
    TP1_HIT = MAX_DESDE_ENTRADA > TP1_LEVEL
    BE_HIT = MAX_DESDE_ENTRADA > (E_PRICE + ATR_ENTRY * TP1_MULT * 0.6)

    # --- 13. STOP MULTICAPA --------------------------------------------
    VELOCIDAD = (CLOSE - REF(CLOSE, 3)) / REF(CLOSE, 3) * 100
    RALLY_RAPIDO = VELOCIDAD > 3.0

    MULT_ZONA = IF(TP1_HIT, MULT_T * 0.45, MULT_T)

    LIMIT_DUR = IF(RALLY_RAPIDO,
                   MINS(DURACION + 1, pd.Series(6.0, index=CLOSE.index)),
                   MINS(DURACION + 1, pd.Series(4.0, index=CLOSE.index)))
    TRAILING_RAW = HHV_VENTANA_VARIABLE(HIGH, LIMIT_DUR) - (ATR_V * MULT_ZONA)
    TRAILING = IF(DURACION >= 2, TRAILING_RAW, SL_DURO_FINAL)

    TRAILING_FILTRADO = IF(TENDENCIA_VIVA_MACRO,
                           MAXS(TRAILING, MA20 * 0.98), TRAILING)

    FLEX_STOP = IF(RALLY_RAPIDO, REF(LLV(LOW, 4), 1), REF(LLV(LOW, 2), 1))
    TRAILING_MOM = IF(TENDENCIA_VIVA_MACRO, TRAILING_FILTRADO,
                      MAXS(TRAILING_FILTRADO, FLEX_STOP))

    PISO_MA = IF(BE_HIT, IF(TRAILING_MOM > MA50, MA50, SL_DURO_FINAL),
                 SL_DURO_FINAL)
    BASE_STOP = IF(EN_TENDENCIA, MAXS(TRAILING_MOM, PISO_MA), TRAILING_MOM)
    STOP_FINAL = MAXS(BASE_STOP, SL_DURO_FINAL)

    # --- 14. SALIDAS ADICIONALES ---------------------------------------
    ADX_LIMS = IF(BANDA == 1, 18, IF(BANDA == 2, 20, 22))
    ADX_AGOTA = (ADX_V < ADX_LIMS) & (ADX_V < REF(ADX_V, 2)) & (CLOSE < BB_MID)
    V_AGOTA = TP1_HIT & (CLOSE < REF(LLV(LOW, 2), 1))

    DIAS_MAX = IF(BANDA == 1, 28, IF(BANDA == 2, 22, 16))
    SIN_AVANCE = ((DURACION >= DIAS_MAX)
                  & (MAX_DESDE_ENTRADA < E_PRICE + ATR_ENTRY * 0.6)
                  & VOL_SECO & (~TENDENCIA_VIVA))

    MACD_REV = (HISTO < 0) & (HISTO < REF(HISTO, 1)) & (REF(HISTO, 1) < REF(HISTO, 2))
    MACD_GIRO_N = MACD_REV & (DIF < DEA) & (DIF < REF(DIF, 1))
    SALIDA_MACD = BE_HIT & MACD_GIRO_N & (CLOSE < BB_MID) & (DIF < 0)

    # --- 15. LOGICA DE POSICION ----------------------------------------
    EXIT_COND = ((CLOSE < STOP_FINAL) | V_AGOTA | SIN_AVANCE
                 | ADX_AGOTA | SALIDA_MACD)
    IS_LONG = BARSLAST(B_SIGNAL) < BARSLAST(EXIT_COND)
    BUY_OK = IS_LONG & (~REF(IS_LONG, 1).fillna(False).astype(bool))
    SELL_OK = (~IS_LONG) & REF(IS_LONG, 1).fillna(False).astype(bool)

    # --- 16. ADD DIFERENCIADO ------------------------------------------
    ADD_BC = (IS_LONG & (BANDA == 1) & (PDI_A > MDI_A) & (ADX_A > 28)
              & ADX_A_ACCEL & CROSS_KD & (KVAL < 75) & (CLOSE > MA20)
              & VOL_MED & (~TP1_HIT))
    ADD_HYB = (IS_LONG & (BANDA == 2) & (PDI_A > MDI_A) & (ADX_A > 30)
               & ADX_A_ACCEL & CROSS_KD & (KVAL < 75) & (CLOSE > MA20)
               & VOL_MED & (~TP1_HIT))
    ADD_VOL = (IS_LONG & (BANDA == 3) & (PDI_A > MDI_A) & (ADX_A > 32)
               & ADX_A_ACCEL & (CLOSE > REF(HHV(HIGH, 3), 1)) & (CLOSE > MA20)
               & VOL_ALT & (~TP1_HIT))
    ADD_OK = ADD_BC | ADD_HYB | ADD_VOL

    # --- 18. RADAR OJO / BTD -------------------------------------------
    ALERTA_OJO = (OSC < 32) & (J_V < 25) & (CLOSE < BB_DN)
    CRUCE_J = (J_V > 10) & (REF(J_V, 1) <= 10)
    BTD_OK = REF(ALERTA_OJO, 1).fillna(False).astype(bool) & CRUCE_J & GIRO_MACD

    # --- salida --------------------------------------------------------
    d["BANDA_PRE"] = BANDA_PRE
    d["BANDA"] = BANDA
    d["MA20"] = MA20
    d["MA50"] = MA50
    d["MA200"] = MA200
    d["ATR_V"] = ATR_V
    d["ADX_V"] = ADX_V
    d["PDI"] = PDI
    d["MDI"] = MDI
    d["OSC"] = OSC
    d["J_V"] = J_V
    d["KVAL"] = KVAL
    d["DVAL"] = DVAL
    d["DIF"] = DIF
    d["DEA"] = DEA
    d["HISTO"] = HISTO
    d["BB_MID"] = BB_MID
    d["BB_UP"] = BB_UP
    d["BB_DN"] = BB_DN
    d["ES_BAJISTA_CRITICO"] = ES_BAJISTA_CRITICO
    d["EN_LATERAL"] = EN_LATERAL

    d["S_PULL"] = S_PULL
    d["S_IMPU"] = S_IMPU
    d["S_BOLL"] = S_BOLL
    d["S_SUELO"] = S_SUELO
    d["S_MACD_CROSS"] = S_MACD_CROSS
    d["S_EARLY"] = S_EARLY
    d["S_CONT"] = S_CONT
    d["S_REBOTE_MA200"] = S_REBOTE_MA200

    d["B_SIGNAL"] = B_SIGNAL
    d["DURACION"] = DURACION
    d["E_PRICE"] = E_PRICE
    d["SL_DURO_FINAL"] = SL_DURO_FINAL
    d["STOP_FINAL"] = STOP_FINAL
    d["TP1_LEVEL"] = TP1_LEVEL
    d["TP1_HIT"] = TP1_HIT
    d["BE_HIT"] = BE_HIT
    d["IS_LONG"] = IS_LONG
    d["BUY_OK"] = BUY_OK
    d["SELL_OK"] = SELL_OK
    d["ADD_OK"] = ADD_OK
    d["ALERTA_OJO"] = ALERTA_OJO
    d["BTD_OK"] = BTD_OK

    return d


# ===========================================================================
# LECTURA DE LA ULTIMA BARRA
# ===========================================================================

NOMBRES_GATILLOS = [
    ("S_PULL", "PULL"),
    ("S_IMPU", "IMPU"),
    ("S_BOLL", "BOLL"),
    ("S_SUELO", "SUELO"),
    ("S_MACD_CROSS", "MACD"),
    ("S_EARLY", "EARLY"),
    ("S_CONT", "CONT"),
    ("S_REBOTE_MA200", "REB200"),
]

NOMBRE_BANDA = {1: "BC", 2: "HYB", 3: "VOL"}


def leer_ultima(d, ticker):
    """Devuelve un dict con el estado de la ultima barra, o None si no hay nada."""
    if len(d) < 210:
        return None

    f = d.iloc[-1]

    gatillos = [n for col, n in NOMBRES_GATILLOS if bool(f.get(col, False))]

    evento = None
    if bool(f["BUY_OK"]):
        evento = "BUY"
    elif bool(f["SELL_OK"]):
        evento = "SELL"
    elif bool(f["ADD_OK"]):
        evento = "ADD"
    elif bool(f["BTD_OK"]):
        evento = "BTD"
    elif bool(f["ALERTA_OJO"]) and not bool(f["IS_LONG"]):
        evento = "OJO"

    if evento is None:
        return None

    banda = f["BANDA"] if not pd.isna(f["BANDA"]) else f["BANDA_PRE"]

    return {
        "ticker": ticker,
        "evento": evento,
        "banda": NOMBRE_BANDA.get(int(banda), "?") if not pd.isna(banda) else "?",
        "gatillos": gatillos,
        "fecha": str(d.index[-1])[:10],
        "precio": round(float(f["close"]), 2),
        "stop": round(float(f["STOP_FINAL"]), 2) if not pd.isna(f["STOP_FINAL"]) else None,
        "tp1": round(float(f["TP1_LEVEL"]), 2) if not pd.isna(f["TP1_LEVEL"]) else None,
        "adx": round(float(f["ADX_V"]), 1) if not pd.isna(f["ADX_V"]) else None,
        "osc": round(float(f["OSC"]), 1) if not pd.isna(f["OSC"]) else None,
        "atr_pct": round(float(f["ATR_V"] / f["close"] * 100), 2),
    }
