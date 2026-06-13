#!/usr/bin/env python3
"""
snapshot.py — Foto diaria de las TOP PICKS (score >= 4) del Rebote Screener.
Corre en GitHub Actions tras el cierre de NY. Guarda en el Gist con memoria de 15 días.
Autocontenido: no depende de app_mobile.py.
"""
import os, json, urllib.request
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
import pandas as pd
import numpy as np

GIST_ID = "00c849548b7f82e35530eb837df20a3a"
ARCHIVO_SNAP = "historial.json"      # archivo dentro del Gist para las fotos
DIAS_MEMORIA = 15
SCORE_MIN = 4                         # TOP = score >= 4

# ====================== LISTA DE TICKERS ======================
TICKERS = [
    "CHWY","ALT","PLTR","RBRK","MORN","CBRS","ISRG","MDT","DG","EPAM",
    "BRK-B","NCLH","CLS","GILD","FSLR","RTX","PSX","NBIS","ZTS","FICO",
    "BAC","GS","NOW","RMBS","MRVL","COF","BHP","SOL-USD","BTI","SAP",
    "FDX","TME","INTU","SONY","COHR","GDDY","PM","TSM","CRDO","NNE",
    "NRG","BLK","ENPH","LMT","DPZ","IONQ","VRT","VRTX","MSFT","AAPL",
    "MMM","HD","GOOGL","EBAY","SOFI","MPWR","LULU","CPRT","ETN","TJX",
    "ADP","NEE","DHR","T","VZ","QQQ","MU","TXN","OKTA","ZS",
    "AFRM","GME","BABA","RIOT","ARM","XLP","XLK","XLI","XLV","XLE",
    "IWM","SPY","UBER","PYPL","INTC","LRCX","AMAT","REGN","SHOP","HOOD",
    "NET","CRWD","DDOG","SNOW","MDB","MARA","COIN","AVGO","CSCO","ACN",
    "LIN","TMO","LLY","ABBV","ABNB","MRNA","AMT","ASTS","PANW","APH",
    "SMCI","DELL","ANET","STX","WDC","RCL","BKNG","TMUS","DE","CRM",
    "ADBE","TGT","COST","CVX","XOM","GE","ABT","AMZN","BTC-USD","SOUN",
    "IBM","SMH","URA","CEG","NVO","MRK","SPOT","EQIX","BA","FCX",
    "AEM","MSTR","PEP","KO","WMT","PFE","DIS","JNJ","MCD","JPM",
    "MA","CAT","SBUX","PG","UNH","NVDA","NFLX","MELI","NKE","META",
    "ORCL","ASML","TSLA","AMD","QQQM","VOO","ACHR","LINK-USD","AVAX-USD",
    "CL=F","NG=F","SI=F","HG=F","GC=F","NQ=F",
    "EURUSD=X","USDCHF=X","GBPUSD=X","USDJPY=X","USDCOP=X","USDCLP=X","USDBRL=X",
    "ZIM","DLTR","BBY","WBD","GT","WYNN","MGM","SNAP","CVNA","ROKU",
    "HUM","ELV","UHS","ILMN","SWK","FNV","SBSW","GOLD","SQM","ALB",
    "GSK","AZN","BAYN.DE","ROG.SW","9988.HK",
    "GM","UPS","SYY","CNC","V","CL","ON","BUD","NXPI","WM",
    "HSY","TSN","TSCO","PINS","SPGI","MDLZ","SNDK","PSA","CMG","STLD",
    "CLF","ALK","IBKR","MCO","UNP","HON","HCA","MSCI","VST","CI",
    "LEVI","AZO","CSGP","HIVE","SCHW","ONDS","PRZO","WVE","NOK","NU",
    "LOW","DECK","NASA","XYZ","IGV","HMC","SIDU","ETH-USD","OTIS","ESLT",
    "BLZE","LITE","CRWV","HII","GFI","CLX","NVAX","ZBH","PSKY","FIG",
    "D","KEYS","B","IGM","PATH","U","TX","BMNR","UL","MNST",
    "QTUM","IYW","IP","ARKQ","BITX","ETHU","CRML","UA","XT","O",
    "CRCL","RACE","CMCSA",
]

# ====================== LECTURA TICKERS COMPARTIDOS ======================
def leer_tickers_compartidos():
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
        contenido = data["files"]["tickers.txt"]["content"]
        items = [t.strip().upper() for t in contenido.replace("\n", ",").split(",")]
        return [t for t in items if t]
    except Exception:
        return []

# ====================== FUNDAMENTALES ======================
def _num(s):
    """Convierte string de Finviz a float. '17.45'->17.45, '20.65%'->0.2065, '-'->None, '5.04B'->5.04e9."""
    if s is None: return None
    s = str(s).strip()
    if s in ("-", "", "—"): return None
    try:
        pct = s.endswith("%")
        s2 = s.replace("%", "").replace(",", "").replace("$", "")
        mult = 1.0
        if s2 and s2[-1] in "BMK":
            mult = {"B":1e9, "M":1e6, "K":1e3}[s2[-1]]
            s2 = s2[:-1]
        v = float(s2) * mult
        return v/100.0 if pct else v
    except Exception:
        return None

def fetch_finviz(sym):
    """Fundamentales desde Finviz (más completo, incluye crecimiento real EPS next 5Y)."""
    # Finviz no soporta cripto/forex/futuros/internacionales
    if any(x in sym for x in ['-USD','-F','=X','=F','.DE','.SW','.HK']):
        return None
    try:
        from finvizfinance.quote import finvizfinance
        # Finviz usa BRK-B con formato BRK-B; algunos con punto
        fv_sym = sym.replace("-", "-")
        stock = finvizfinance(fv_sym)
        f = stock.ticker_fundament()
        if not f or not isinstance(f, dict):
            return None

        # Target price y Recom
        target = _num(f.get("Target Price"))
        recom  = _num(f.get("Recom"))  # 1=Strong Buy .. 5=Sell

        # Crecimiento: prioriza EPS next 5Y, luego EPS next Y
        growth = _num(f.get("EPS next 5Y"))
        if growth is None:
            growth = _num(f.get("EPS next Y"))

        return {
            "target_mean":  target,
            "n_analysts":   None,            # Finviz no da número de analistas
            "rec_mean":     recom,
            "pe_ttm":       _num(f.get("P/E")),
            "pe_fwd":       _num(f.get("Forward P/E")),
            "eps_ttm":      _num(f.get("EPS (ttm)")),
            "fwd_eps":      None,             # se deriva si hace falta
            "book_value":   _num(f.get("Book/sh")),
            "growth":       growth,
            "_fuente":      "finviz",
        }
    except Exception:
        return None

def fetch_yf(sym):
    """Fundamentales desde yfinance (respaldo)."""
    import time
    for intento in range(2):
        try:
            info = yf.Ticker(sym).info
            if info and len(info) >= 10 and (info.get("targetMeanPrice") or info.get("trailingPE") or info.get("trailingEps")):
                return {
                    "target_mean":   info.get("targetMeanPrice"),
                    "n_analysts":    info.get("numberOfAnalystOpinions"),
                    "rec_mean":      info.get("recommendationMean"),
                    "pe_ttm":        info.get("trailingPE"),
                    "pe_fwd":        info.get("forwardPE"),
                    "eps_ttm":       info.get("trailingEps"),
                    "fwd_eps":       info.get("forwardEps"),
                    "book_value":    info.get("bookValue"),
                    "growth":        info.get("earningsGrowth"),
                    "_fuente":       "yfinance",
                }
        except Exception:
            pass
        time.sleep(0.4 * (intento + 1))
    return None

def fetch_fundamentales(sym):
    """Finviz como fuente principal (más completa). yfinance como respaldo.
    Rellena huecos de uno con el otro."""
    fv = fetch_finviz(sym)
    yf_data = None

    # Si Finviz falló por completo, usar yfinance
    if fv is None:
        return fetch_yf(sym)

    # Si Finviz no trae target o rec, completar con yfinance
    if fv.get("target_mean") is None or fv.get("rec_mean") is None:
        yf_data = fetch_yf(sym)
        if yf_data:
            if fv.get("target_mean") is None:
                fv["target_mean"] = yf_data.get("target_mean")
            if fv.get("rec_mean") is None:
                fv["rec_mean"] = yf_data.get("rec_mean")
            if fv.get("n_analysts") is None:
                fv["n_analysts"] = yf_data.get("n_analysts")

    return fv

def calc_upside(precio_actual, target_mean):
    """% entre precio actual y Target 12M de analistas. Devuelve (texto, raw, bajo_target)."""
    if not target_mean or target_mean <= 0:
        return ("—", None, False)
    up = (target_mean - precio_actual) / precio_actual * 100
    bajo_target = precio_actual < target_mean
    if up >= 15:   txt = f"🟢 +{up:.0f}%"
    elif up >= 0:  txt = f"⚪ +{up:.0f}%"
    elif up >= -10: txt = f"🟡 {up:.0f}%"
    else:          txt = f"🔴 {up:.0f}%"
    return (txt, up, bajo_target)

def calc_fair_value(fund, pe_hist, precio_actual):
    """FV promedio de hasta 4 modelos: Graham + Forward P/E + Crecimiento + Target.
    Robusto ante datos faltantes. Devuelve (texto_fv, upside_txt, upside_raw)."""
    eps   = fund.get("eps_ttm")
    bv    = fund.get("book_value")
    feps  = fund.get("fwd_eps")
    g     = fund.get("growth")
    pe_fwd_val = fund.get("pe_fwd")
    target = fund.get("target_mean")

    modelos = []

    # Modelo 1: Graham √(22.5×EPS×BV) — solo value rentable
    if eps and bv and eps > 0 and bv > 0:
        modelos.append(math.sqrt(22.5 * eps * bv))

    # P/E de referencia: usa P/E TTM, si falta usa Forward P/E, si falta usa 18 (mercado)
    pe_ref = None
    if pe_hist and pe_hist > 0:
        pe_ref = pe_hist
    elif pe_fwd_val and pe_fwd_val > 0:
        pe_ref = pe_fwd_val
    else:
        pe_ref = 18.0  # P/E promedio de mercado como último recurso
    pe_ok = max(8, min(pe_ref, 40))  # saneado a rango 8-40

    # Modelo 2: Forward EPS × P/E de referencia
    if feps and feps > 0:
        modelos.append(feps * pe_ok)

    # Modelo 3: EPS proyectado 5A con crecimiento, descontado al 10%
    if eps and eps > 0:
        gr = max(-0.05, min(g if g else 0.08, 0.25))
        eps_fut = eps * (1 + gr) ** 5
        modelos.append((eps_fut * pe_ok) / (1.10 ** 5))

    # Modelo 4: si hay EPS forward pero no TTM, igual estima con forward
    if (not eps or eps <= 0) and feps and feps > 0:
        gr = max(-0.05, min(g if g else 0.08, 0.25))
        eps_fut = feps * (1 + gr) ** 4
        modelos.append((eps_fut * pe_ok) / (1.10 ** 4))

    if not modelos:
        return ("—", "—", None)

    fv = sum(modelos) / len(modelos)
    up = (fv - precio_actual) / precio_actual * 100
    if up >= 15:   txt = f"🟢 +{up:.0f}%"
    elif up >= 0:  txt = f"⚪ +{up:.0f}%"
    elif up >= -15: txt = f"🟡 {up:.0f}%"
    else:          txt = f"🔴 {up:.0f}%"
    return (f"${fv:.0f}", txt, up)
    try:
        fv = math.sqrt(22.5 * eps_ttm * book_value)
        up = (fv - precio_actual) / precio_actual * 100
        if up >= 15:   txt = f"🟢 +{up:.0f}%"
        elif up >= 0:  txt = f"⚪ +{up:.0f}%"
        elif up >= -15: txt = f"🟡 {up:.0f}%"
        else:          txt = f"🔴 {up:.0f}%"
        return (f"${fv:.0f}", txt, up)
    except:
        return ("—", "—", None)

def consenso(rec_mean, n_analysts):
    """recommendationMean (1-5) a texto + emoji. n analistas opcional."""
    if rec_mean is None or rec_mean <= 0:
        return "—"
    if rec_mean <= 1.5:   tag = "🟢 Strong Buy"
    elif rec_mean <= 2.5: tag = "🟢 Buy"
    elif rec_mean <= 3.5: tag = "⚪ Hold"
    elif rec_mean <= 4.5: tag = "🔴 Sell"
    else:                 tag = "🔴 Strong Sell"
    if n_analysts and n_analysts > 0:
        return f"{tag} ({int(n_analysts)})"
    return tag

# ====================== ANÁLISIS TÉCNICO ======================
def analizar_ticker(sym, df):
    if df is None or df.empty or len(df) < 200:
        return None
    df = df.dropna(subset=['Close','Volume'])
    df = df[df['Volume']>0].copy()
    if len(df) < 200:
        return None

    # ── Medias (EMA 20/50/200/325) ──
    df['MA20']  = df['Close'].ewm(span=20,adjust=False).mean()
    df['MA50']  = df['Close'].ewm(span=50,adjust=False).mean()
    df['MA200'] = df['Close'].ewm(span=200,adjust=False).mean()
    df['MA325'] = df['Close'].ewm(span=325,adjust=False).mean()

    # ── ATR ──
    hl=(df['High']-df['Low']); hpc=(df['High']-df['Close'].shift(1)).abs(); lpc=(df['Low']-df['Close'].shift(1)).abs()
    df['ATR'] = pd.concat([hl,hpc,lpc],axis=1).max(axis=1).rolling(14).mean()

    # ── ADX ──
    hd=df['High']-df['High'].shift(1); ld=df['Low'].shift(1)-df['Low']
    dmp=np.where((hd>0)&(hd>ld),hd,0); dmm=np.where((ld>0)&(ld>hd),ld,0)
    t14=pd.concat([hl,hpc,lpc],axis=1).max(axis=1).rolling(14).sum().replace(0,1e-8)
    pdi=pd.Series(dmp,index=df.index).rolling(14).sum()*100/t14
    mdi=pd.Series(dmm,index=df.index).rolling(14).sum()*100/t14
    df['PDI'] = pdi
    df['MDI'] = mdi
    df['ADX'] = (abs(pdi-mdi)/(pdi+mdi).replace(0,1e-8)*100).rolling(9).mean()

    # ── KDJ ──
    lm=df['Low'].rolling(9).min(); hm=df['High'].rolling(9).max()
    rsv=(df['Close']-lm)/(hm-lm).replace(0,1e-8)*100
    k=rsv.ewm(alpha=1/3,adjust=False).mean()
    d=k.ewm(alpha=1/3,adjust=False).mean()
    df['K']=k; df['D']=d; df['J']=3*k-2*d
    df['GIRO_J']   = df['J'] > df['J'].shift(1)
    df['CROSS_KD'] = (k>d) & (k.shift(1) <= d.shift(1))

    # ── RSI Wilder ──
    delta=df['Close'].diff(); gain=delta.clip(lower=0); loss=(-delta).clip(lower=0)
    df['RSI'] = 100-(100/(1+(gain.ewm(alpha=1/14,adjust=False).mean()/loss.ewm(alpha=1/14,adjust=False).mean().replace(0,1e-8))))

    # ── MACD ──
    dif = df['Close'].ewm(span=12,adjust=False).mean() - df['Close'].ewm(span=26,adjust=False).mean()
    dea = dif.ewm(span=9,adjust=False).mean()
    hist = dif - dea
    df['GIRO_MACD'] = (hist > hist.shift(1)) & (hist.shift(1) <= hist.shift(2))
    df['CROSS_MACD']= (dif > dea) & (dif.shift(1) <= dea.shift(1))

    # ── Bollinger ──
    df['BB_MID'] = df['Close'].rolling(20).mean()
    df['BB_STD'] = df['Close'].rolling(20).std(ddof=0)
    df['BB_DN']  = df['BB_MID'] - 2*df['BB_STD']

    # ── Volumen ──
    df['VOL_MA'] = df['Volume'].rolling(20).mean()
    df['VOL_OK'] = df['Volume'] > df['VOL_MA'] * 0.85

    rsi_v = float(df['RSI'].iloc[-1]) if not pd.isna(df['RSI'].iloc[-1]) else 50
    j_v   = float(df['J'].iloc[-1])   if not pd.isna(df['J'].iloc[-1])  else 50
    adx_v = float(df['ADX'].iloc[-1]) if not pd.isna(df['ADX'].iloc[-1]) else 0
    precio= float(df['Close'].iloc[-1])

    # ══════════════════════════════════════════════════════════
    # 5 PUNTOS INDEPENDIENTES DE SCORE
    # ══════════════════════════════════════════════════════════

    # ── PUNTO 1: RSI < 35 (sobreventa) ──
    p_rsi = rsi_v < 35

    # ── PUNTO 2: GIRO KDJ + CRUCE MACD + volumen + cierre sobre min ayer ──
    cierre_sobre_min = precio > float(df['Low'].iloc[-2])
    vol_ok = bool(df['VOL_OK'].iloc[-1])
    p_giro = (
        bool(df['CROSS_KD'].iloc[-1] or df['CROSS_KD'].iloc[-2] or df['GIRO_J'].iloc[-1]) and
        bool(df['GIRO_MACD'].iloc[-1] or df['CROSS_MACD'].iloc[-1] or df['CROSS_MACD'].iloc[-2]) and
        cierre_sobre_min and
        vol_ok
    )

    # ── PUNTO 3: TOQUE DE SOPORTE — Bollinger inf. O EMA 50/200/325 desde arriba ──
    ma50_v  = float(df['MA50'].iloc[-1])
    ma200_v = float(df['MA200'].iloc[-1])
    ma325_v = float(df['MA325'].iloc[-1])
    low_v   = float(df['Low'].iloc[-1])
    bb_dn_y = float(df['BB_DN'].iloc[-2])
    low_y   = float(df['Low'].iloc[-2])
    bb_dn   = float(df['BB_DN'].iloc[-1])

    toca_ema = (
        (low_v <= ma50_v  * 1.015 and precio > ma50_v  * 0.985) or
        (low_v <= ma200_v * 1.015 and precio > ma200_v * 0.985) or
        (low_v <= ma325_v * 1.015 and precio > ma325_v * 0.985)
    )
    toca_bb = (low_y <= bb_dn_y and precio > bb_dn)
    # Toque válido solo con volumen y cierre sobre mínimo de ayer
    p_toque = (toca_ema or toca_bb) and cierre_sobre_min and vol_ok

    # ── PUNTO 4: DIRECCIÓN DI+ > DI- (cambio real vs trampa bajista) ──
    pdi_v = float(df['PDI'].iloc[-1]) if not pd.isna(df['PDI'].iloc[-1]) else 0
    mdi_v = float(df['MDI'].iloc[-1]) if not pd.isna(df['MDI'].iloc[-1]) else 0
    p_di = pdi_v > mdi_v   # DI+ dominante = presión alcista confirmada

    # ── PUNTO 5-6: VALOR (se calcula en fetch_fund, +1 o +2) ──

    if not (p_rsi or p_giro or p_toque):
        return None

    # Score técnico: RSI + Giro + Toque + DI = hasta 4 puntos técnicos
    score_tecnico = sum([p_rsi, p_giro, p_toque, p_di])

    return {
        "sym": sym,
        "precio": precio,
        "precio_str": f"${precio:.2f}",
        "rsi": rsi_v, "rsi_str": f"{rsi_v:.1f}",
        "j": j_v, "j_str": f"{j_v:.1f}",
        "adx": adx_v, "adx_str": f"{adx_v:.1f}",
        "score": score_tecnico,
        "p_rsi":   p_rsi,
        "p_giro":  p_giro,
        "p_toque": p_toque,
        "p_di":    p_di,
        # detalle de qué soporte tocó (para mostrar)
        "toca_ema": toca_ema,
        "toca_bb":  toca_bb,
    }

# ====================== FETCH FUNDAMENTAL POR ITEM ======================
def procesar_fund(item):
    sym = item["sym"]
    fund = fetch_fundamentales(sym)
    item["fv"] = "—"; item["fv_up"] = "—"; item["target"] = "—"
    item["upside"] = "—"; item["pe_ttm"] = "—"; item["pe_fwd"] = "—"
    item["consenso"] = "—"; item["valor_pts"] = 0
    if not fund:
        return item
    tm = fund.get("target_mean")
    up_txt, target_up_raw, _ = calc_upside(item["precio"], tm)
    item["target"] = f"${tm:.2f}" if tm else "—"
    item["upside"] = up_txt
    pe_hist_raw = fund.get("pe_ttm")
    fv_txt, fv_up_txt, fv_up_raw = calc_fair_value(fund, pe_hist_raw, item["precio"])
    item["fv"] = fv_txt; item["fv_up"] = fv_up_txt
    pe = fund.get("pe_ttm"); pef = fund.get("pe_fwd")
    item["pe_ttm"] = f"{pe:.1f}" if pe else "—"
    item["pe_fwd"] = f"{pef:.1f}" if pef else "—"
    item["consenso"] = consenso(fund.get("rec_mean"), fund.get("n_analysts"))
    fv_ok = (fv_up_raw is not None and fv_up_raw >= 15)
    target_ok = (target_up_raw is not None and target_up_raw >= 15)
    if fv_ok and target_ok: item["valor_pts"] = 2; item["score"] += 2
    elif fv_ok:             item["valor_pts"] = 1; item["score"] += 1
    return item

def gatillos_str(x):
    gs = []
    if x.get("p_rsi"):   gs.append("RSI")
    if x.get("p_giro"):  gs.append("GIRO")
    if x.get("p_toque"): gs.append("BB" if x.get("toca_bb") else "EMA")
    if x.get("p_di"):    gs.append("DI+")
    vp = x.get("valor_pts",0)
    if vp == 2:   gs.append("VALOR2")
    elif vp == 1: gs.append("VALOR1")
    return " ".join(gs)

# ====================== MAIN ======================
def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: falta GITHUB_TOKEN"); return

    # Watchlist = base + compartidos (sin duplicar)
    compartidos = leer_tickers_compartidos()
    vistos=set(); watchlist=[]
    for t in list(TICKERS)+compartidos:
        if t not in vistos: watchlist.append(t); vistos.add(t)
    print(f"Escaneando {len(watchlist)} tickers...")

    # Descarga batch
    df_batch = yf.download(watchlist, period="2y", group_by="ticker",
                           progress=False, auto_adjust=True, threads=True)

    # Indicadores
    resultados=[]
    for sym in watchlist:
        try:
            df = df_batch[sym].copy() if len(watchlist)>1 else df_batch.copy()
            r = analizar_ticker(sym, df)
            if r: resultados.append(r)
        except Exception:
            continue
    print(f"{len(resultados)} candidatos técnicos")

    # Fundamentales
    with ThreadPoolExecutor(max_workers=4) as ex:
        todos = list(ex.map(procesar_fund, resultados))

    # Filtrar TOP score >= 4
    tops = [x for x in todos if x["score"] >= SCORE_MIN]
    tops.sort(key=lambda x:(-x["score"], x["rsi"]))
    print(f"{len(tops)} TOP PICKS (score>={SCORE_MIN})")

    # Foto del día (compacta)
    hoy = datetime.now(timezone(timedelta(hours=-5))).strftime("%Y-%m-%d")
    foto = {
        "fecha": hoy,
        "tops": [{
            "sym": x["sym"], "score": x["score"], "gatillos": gatillos_str(x),
            "precio": x["precio_str"], "fv": x["fv"], "fv_up": x["fv_up"],
            "target": x["target"], "upside": x["upside"],
            "rsi": x["rsi_str"], "adx": x["adx_str"], "consenso": x["consenso"],
        } for x in tops]
    }

    # Leer historial existente del Gist
    historial=[]
    try:
        url=f"https://api.github.com/gists/{GIST_ID}"
        req=urllib.request.Request(url, headers={"Accept":"application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data=json.loads(r.read().decode())
        if ARCHIVO_SNAP in data["files"]:
            historial=json.loads(data["files"][ARCHIVO_SNAP]["content"])
    except Exception as e:
        print(f"Sin historial previo: {e}")

    # Quitar foto del mismo día si existe (re-ejecución) y agregar la nueva
    historial=[h for h in historial if h.get("fecha")!=hoy]
    historial.append(foto)
    # Mantener solo últimos 15 días
    historial=sorted(historial, key=lambda h:h["fecha"])[-DIAS_MEMORIA:]

    # Guardar en Gist
    payload=json.dumps({"files":{ARCHIVO_SNAP:{"content":json.dumps(historial, ensure_ascii=False, indent=1)}}}).encode()
    req=urllib.request.Request(f"https://api.github.com/gists/{GIST_ID}", data=payload, method="PATCH",
        headers={"Accept":"application/vnd.github+json","Authorization":f"Bearer {token}","Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        print(f"✓ Guardado. Historial: {len(historial)} días. Status {r.status}")

if __name__ == "__main__":
    main()
