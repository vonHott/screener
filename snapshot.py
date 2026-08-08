#!/usr/bin/env python3
"""
snapshot.py — Foto diaria de las TOP PICKS del Screener CRH V3.

Corre en GitHub Actions tras el cierre de NY. Guarda en el Gist, memoria 15 dias.

MOTOR = crh.py (el mismo que usa app.py). Antes este archivo tenia su propio
sistema de score (RSI/GIRO/TOQUE/DI), incompatible con lo que muestra la app.
Ahora los dos leen del mismo modulo y el historial es comparable.

REQUISITO: crh.py debe estar en la raiz del repo, junto a este archivo.
"""

import json
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import yfinance as yf

from crh import crh

GIST_ID = "00c849548b7f82e35530eb837df20a3a"
ARCHIVO_SNAP = "historial.json"
DIAS_MEMORIA = 15
SCORE_MIN = 4
LOOKBACK = 3          # aceptar señal disparada en las ultimas N velas

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
    "TURB","RIVN","BB","DOCU","IOT","PAYP","ULTA","GTLB","CIEN","FIVE",
    "TEAM","MSI","BSX","HRL","UMAC","CMS","MKC","PEG","COR","AA",
    "AMC","AMPX","AVAV","GLD","GLW","ICE","IHI","NOC","PL","QNT",
    "RDW","RKLB","SERV","SPCX","STLA","CSTM","CENX",
]


# ====================== TICKERS COMPARTIDOS ======================
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


# ====================== REGIMEN ======================
def regimen_alcista():
    try:
        spy = yf.Ticker("SPY").history(period="1y")['Close'].dropna()
        if len(spy) < 50:
            return True
        ema50 = spy.ewm(span=50, adjust=False).mean()
        return float(spy.iloc[-1]) > float(ema50.iloc[-1])
    except Exception:
        return True


# ====================== FUNDAMENTALES ======================
def _num(s):
    if s is None:
        return None
    s = str(s).strip()
    if s in ("-", "", "—"):
        return None
    try:
        pct = s.endswith("%")
        s2 = s.replace("%", "").replace(",", "").replace("$", "")
        mult = 1.0
        if s2 and s2[-1] in "BMK":
            mult = {"B": 1e9, "M": 1e6, "K": 1e3}[s2[-1]]
            s2 = s2[:-1]
        v = float(s2) * mult
        return v / 100.0 if pct else v
    except Exception:
        return None


def fetch_finviz(sym):
    if any(x in sym for x in ['-USD', '-F', '=X', '=F', '.DE', '.SW', '.HK']):
        return None
    try:
        from finvizfinance.quote import finvizfinance
        stock = finvizfinance(sym)
        f = stock.ticker_fundament()
        if not f or not isinstance(f, dict):
            return None
        growth = _num(f.get("EPS next 5Y")) or _num(f.get("EPS next Y"))
        return {"target_mean": _num(f.get("Target Price")), "n_analysts": None,
                "rec_mean": _num(f.get("Recom")), "pe_ttm": _num(f.get("P/E")),
                "pe_fwd": _num(f.get("Forward P/E")), "eps_ttm": _num(f.get("EPS (ttm)")),
                "fwd_eps": None, "book_value": _num(f.get("Book/sh")), "growth": growth}
    except Exception:
        return None


def fetch_yf(sym):
    import time
    for intento in range(2):
        try:
            info = yf.Ticker(sym).info
            if info and len(info) >= 10 and (info.get("targetMeanPrice") or info.get("trailingPE") or info.get("trailingEps")):
                return {"target_mean": info.get("targetMeanPrice"), "n_analysts": info.get("numberOfAnalystOpinions"),
                        "rec_mean": info.get("recommendationMean"), "pe_ttm": info.get("trailingPE"),
                        "pe_fwd": info.get("forwardPE"), "eps_ttm": info.get("trailingEps"),
                        "fwd_eps": info.get("forwardEps"), "book_value": info.get("bookValue"),
                        "growth": info.get("earningsGrowth")}
        except Exception:
            pass
        time.sleep(0.4 * (intento + 1))
    return None


def fetch_fundamentales(sym):
    fv = fetch_finviz(sym)
    if fv is None:
        return fetch_yf(sym)
    if fv.get("target_mean") is None or fv.get("rec_mean") is None:
        yfd = fetch_yf(sym)
        if yfd:
            for k in ("target_mean", "rec_mean", "n_analysts"):
                if fv.get(k) is None:
                    fv[k] = yfd.get(k)
    return fv


def calc_upside(precio_actual, target_mean):
    if not target_mean or target_mean <= 0:
        return ("—", None)
    up = (target_mean - precio_actual) / precio_actual * 100
    if up >= 15:   txt = f"🟢 +{up:.0f}%"
    elif up >= 0:  txt = f"⚪ +{up:.0f}%"
    elif up >= -10: txt = f"🟡 {up:.0f}%"
    else:          txt = f"🔴 {up:.0f}%"
    return (txt, up)


def calc_fair_value(fund, pe_hist, precio_actual):
    import math as _math
    eps = fund.get("eps_ttm"); bv = fund.get("book_value")
    feps = fund.get("fwd_eps"); g = fund.get("growth")
    pe_fwd_val = fund.get("pe_fwd")
    modelos = []
    if eps and bv and eps > 0 and bv > 0:
        modelos.append(_math.sqrt(22.5 * eps * bv))
    pe_ref = pe_hist if (pe_hist and pe_hist > 0) else (pe_fwd_val if (pe_fwd_val and pe_fwd_val > 0) else 18.0)
    pe_ok = max(8, min(pe_ref, 40))
    if feps and feps > 0:
        modelos.append(feps * pe_ok)
    if eps and eps > 0:
        gr = max(-0.05, min(g if g else 0.08, 0.25))
        modelos.append((eps * (1 + gr) ** 5 * pe_ok) / (1.10 ** 5))
    if (not eps or eps <= 0) and feps and feps > 0:
        gr = max(-0.05, min(g if g else 0.08, 0.25))
        modelos.append((feps * (1 + gr) ** 4 * pe_ok) / (1.10 ** 4))
    if not modelos:
        return ("—", "—", None)
    fv = sum(modelos) / len(modelos)
    up = (fv - precio_actual) / precio_actual * 100
    if up >= 15:   txt = f"🟢 +{up:.0f}%"
    elif up >= 0:  txt = f"⚪ +{up:.0f}%"
    elif up >= -15: txt = f"🟡 {up:.0f}%"
    else:          txt = f"🔴 {up:.0f}%"
    return (f"${fv:.0f}", txt, up)


def consenso(rec_mean, n_analysts):
    if rec_mean is None or rec_mean <= 0:
        return "—"
    if rec_mean <= 1.5:   tag = "🟢 Strong Buy"
    elif rec_mean <= 2.5: tag = "🟢 Buy"
    elif rec_mean <= 3.5: tag = "⚪ Hold"
    elif rec_mean <= 4.5: tag = "🔴 Sell"
    else:                 tag = "🔴 Strong Sell"
    return f"{tag} ({int(n_analysts)})" if (n_analysts and n_analysts > 0) else tag


# ====================== MOTOR CRH V3 ======================
GATILLOS_V3 = [
    ('S_PULL', 'PULL'), ('S_IMPU', 'IMPU'), ('S_BOLL', 'BOLL'),
    ('S_SUELO', 'SUELO'), ('S_MACD_CROSS', 'MACD'), ('S_EARLY', 'EARLY'),
    ('S_CONT', 'CONT'), ('S_REBOTE_MA200', 'REB200'),
]


def analizar_ticker(sym, df, lookback=LOOKBACK):
    """Identico al de app.py. Devuelve dict solo si hubo señal fresca."""
    if df is None or df.empty or len(df) < 260:
        return None

    d = df.dropna(subset=['Close', 'Volume']).copy()
    d = d[d['Volume'] > 0]
    if len(d) < 260:
        return None

    d.columns = [c.lower() for c in d.columns]
    try:
        d = d[['open', 'high', 'low', 'close', 'volume']].astype(float)
    except Exception:
        return None

    try:
        r = crh(d)
    except Exception:
        return None

    sig = r['B_SIGNAL'].fillna(False).astype(bool)
    if not sig.iloc[-lookback:].any():
        return None

    pos = int(np.where(sig.values)[0][-1])
    barras_desde = int(len(sig) - 1 - pos)
    i = pos

    f_sig = r.iloc[i]
    f_hoy = r.iloc[-1]
    banda_sig = int(f_sig['BANDA_PRE']) if pd.notna(f_sig['BANDA_PRE']) else 2

    triggers, abrevs = [], []
    for col, ab in GATILLOS_V3:
        if bool(f_sig.get(col, False)):
            if banda_sig == 3 and ab in ('PULL', 'EARLY'):
                continue
            triggers.append(col); abrevs.append(ab)
    if not triggers:
        return None

    def _n(v, alt=0.0):
        return float(v) if pd.notna(v) else alt

    precio = _n(f_hoy['close'])
    pdi_v = _n(f_hoy['PDI'])
    mdi_v = _n(f_hoy['MDI'])
    osc_v = _n(f_hoy['OSC'], 50.0)
    adx_v = _n(f_hoy['ADX_V'])

    vma = d['volume'].rolling(20).mean()
    vol_med = bool(d['volume'].iloc[i] > vma.iloc[i] * 1.2) if pd.notna(vma.iloc[i]) else False

    n = len(triggers)
    score = ((2 if n >= 3 else (1 if n == 2 else 0))
             + (1 if pdi_v > mdi_v else 0)
             + (1 if vol_med else 0)
             + (1 if banda_sig <= 2 else 0))
    score = min(score, 5)

    rev = {'S_SUELO', 'S_BOLL', 'S_EARLY', 'S_REBOTE_MA200'}
    mom = {'S_IMPU', 'S_CONT', 'S_MACD_CROSS'}
    ts = set(triggers)
    tipo = 'Momentum' if (ts & mom and not ts & rev) else ('Reversión' if (ts & rev and not ts & mom) else 'Mixto')

    return {
        "sym": sym,
        "precio": precio, "precio_str": f"${precio:.2f}",
        "rsi": osc_v, "rsi_str": f"{osc_v:.1f}",
        "adx": adx_v, "adx_str": f"{adx_v:.1f}",
        "score": score, "n_trig": n,
        "trig_txt": " ".join(abrevs), "tipo": tipo,
        "banda": banda_sig,
        "barras_desde": barras_desde,
        "pdi": pdi_v, "mdi": mdi_v,
        "ma200": _n(f_hoy['MA200'], precio),
        "stop_sys": _n(f_hoy['STOP_FINAL']),
        "tp1_sys": _n(f_hoy['TP1_LEVEL']),
    }


# ====================== FUNDAMENTALES POR ITEM ======================
def procesar_fund(item):
    sym = item["sym"]
    item.update({"fv": "—", "fv_up": "—", "target": "—", "upside": "—",
                 "pe_ttm": "—", "pe_fwd": "—", "consenso": "—", "valor_pts": 0})

    if any(x in sym for x in ['-USD', '-F', '=X', '=F', '.DE', '.SW', '.HK']):
        return item

    fund = fetch_fundamentales(sym)
    if not fund:
        return item

    tm = fund.get("target_mean")
    up_txt, target_up = calc_upside(item["precio"], tm)
    item["target"] = f"${tm:.2f}" if tm else "—"
    item["upside"] = up_txt

    fv_txt, fv_up_txt, fv_up = calc_fair_value(fund, fund.get("pe_ttm"), item["precio"])
    item["fv"] = fv_txt; item["fv_up"] = fv_up_txt

    pe = fund.get("pe_ttm"); pef = fund.get("pe_fwd")
    item["pe_ttm"] = f"{pe:.1f}" if pe else "—"
    item["pe_fwd"] = f"{pef:.1f}" if pef else "—"
    item["consenso"] = consenso(fund.get("rec_mean"), fund.get("n_analysts"))

    fv_ok = (fv_up is not None and fv_up >= 15)
    tg_ok = (target_up is not None and target_up >= 15)
    item["valor_pts"] = 2 if (fv_ok and tg_ok) else (1 if fv_ok else 0)
    return item


def gatillos_str(x):
    partes = [x.get("trig_txt", "")]
    vp = x.get("valor_pts", 0)
    if vp == 2:
        partes.append("VALOR2")
    elif vp == 1:
        partes.append("VALOR1")
    return " ".join(p for p in partes if p)


# ====================== MAIN ======================
def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: falta GITHUB_TOKEN")
        return

    compartidos = leer_tickers_compartidos()
    vistos = set(); watchlist = []
    for t in list(TICKERS) + compartidos:
        if t not in vistos:
            watchlist.append(t); vistos.add(t)
    print(f"Escaneando {len(watchlist)} tickers con motor CRH V3...")

    # 3 años y auto_adjust=False: igual que app.py y que la verificacion
    df_batch = yf.download(watchlist, period="3y", group_by="ticker",
                           progress=False, auto_adjust=False, threads=True)

    resultados = []
    for sym in watchlist:
        try:
            if isinstance(df_batch.columns, pd.MultiIndex):
                df = df_batch[sym].copy() if sym in df_batch.columns.get_level_values(0) else None
            else:
                df = df_batch.copy()
            r = analizar_ticker(sym, df)
            if r:
                resultados.append(r)
        except Exception:
            continue
    print(f"{len(resultados)} señales CRH frescas")

    with ThreadPoolExecutor(max_workers=4) as ex:
        todos = list(ex.map(procesar_fund, resultados))

    if not regimen_alcista():
        print("Regimen SPY bajista (<EMA50): penalizando reversiones sin DI+")
        for x in todos:
            if x.get("tipo") == "Reversión" and x["pdi"] <= x["mdi"] and x["precio"] < x.get("ma200", x["precio"]):
                x["score"] = max(0, x["score"] - 2)

    tops = [x for x in todos if x["score"] >= SCORE_MIN]
    tops.sort(key=lambda x: (-x["score"], x["barras_desde"], -x["n_trig"]))
    print(f"{len(tops)} TOP PICKS (score>={SCORE_MIN})")

    hoy = datetime.now(timezone(timedelta(hours=-5))).strftime("%Y-%m-%d")
    foto = {
        "fecha": hoy,
        "tops": [{
            "sym": x["sym"], "score": x["score"], "gatillos": gatillos_str(x),
            "precio": x["precio_str"], "fv": x["fv"], "fv_up": x["fv_up"],
            "target": x["target"], "upside": x["upside"],
            "rsi": x["rsi_str"], "adx": x["adx_str"], "consenso": x["consenso"],
            "banda": x["banda"], "tipo": x["tipo"],
            "stop": round(x["stop_sys"], 2) if x.get("stop_sys") else None,
            "tp1": round(x["tp1_sys"], 2) if x.get("tp1_sys") else None,
        } for x in tops]
    }

    historial = []
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
        if ARCHIVO_SNAP in data["files"]:
            historial = json.loads(data["files"][ARCHIVO_SNAP]["content"])
    except Exception as e:
        print(f"Sin historial previo: {e}")

    historial = [h for h in historial if h.get("fecha") != hoy]
    historial.append(foto)
    historial = sorted(historial, key=lambda h: h["fecha"])[-DIAS_MEMORIA:]

    payload = json.dumps({"files": {ARCHIVO_SNAP: {"content": json.dumps(historial, ensure_ascii=False, indent=1)}}}).encode()
    req = urllib.request.Request(f"https://api.github.com/gists/{GIST_ID}", data=payload, method="PATCH",
                                 headers={"Accept": "application/vnd.github+json",
                                          "Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        print(f"✓ Guardado. Historial: {len(historial)} dias. Status {r.status}")


if __name__ == "__main__":
    main()
