# ======================================================================
# APALANCADOS — CRH Swing sobre perps de acciones de Bitget (x5)
# ----------------------------------------------------------------------
# Modulo ADICIONAL. No toca el screener: app.py solo lo importa y llama
# a render_apalancados() al final. Si este archivo falla, el screener
# sigue funcionando igual.
#
# MOTOR = crh.py, el mismo que usa el screener y el bot de Telegram.
#
# QUE HACE DISTINTO AL SCREENER
#   El screener es un radar sobre 300+ papeles para mirar 10 a mano, en
#   spot, con fundamentales. Esto es lo contrario: un filtro CERRADO sobre
#   los 144 papeles que tienen perp en Bitget, que solo deja pasar la
#   configuracion validada para operar apalancado.
#
# EL FILTRO (validado sobre 2 años de datos diarios, 144 tickers)
#   gatillo S_BOLL  +  ADX >= 25  +  ATR 3-8% del precio  +  banda VOL
#     -> 172 señales, PF 2.12, ratio ganadora/perdedora 4.64:1
#     -> peor trade -8.3%  (sin stop duro como orden real: -28.4%)
#     -> año 1 PF 1.52  ->  año 2 PF 2.69  (walk-forward, no se degrado)
#   Comparacion de gatillos sueltos: S_BOLL PF 1.81, el resto 1.17-1.37.
#
# LO QUE ESTO NO ES
#   No es una señal de compra automatica. Es la lista corta de lo que
#   califica para apalancar. Medido sobre los ultimos 60 dias habiles de
#   estos 144 papeles: 33 señales = ~12 al mes, o sea 0 o 1 por dia. La
#   mayoria de los dias esta vacio, y eso es correcto, no es un error.
#
# ENTRADA PASADA
#   El backtest entra al CIERRE de la vela de señal. El SL_DURO queda fijo
#   ahi. Si la señal fue hace dias y el precio derivo en contra, el stop
#   sigue donde estaba y queda muy poco aire: entrar tarde NO es la
#   operacion validada. El modulo separa esas y no las ofrece como
#   operables. (Caso real al construir esto: CMCSA, señal a $22.93, precio
#   $22.42, stop duro $22.24 -> 0.8% de aire, que a x5 es -4% pero ya casi
#   tocando. Sin esta separacion se veia como la mejor tarjeta del dia.)
#
# LIMITACION CONOCIDA
#   Los datos son de yfinance (spot diario), que es exactamente con lo que
#   se valido el CRH Swing. El perp de Bitget sigue de cerca al spot en
#   diario. La divergencia spot-vs-perp que nos mordio antes era INTRADIA
#   (velas 5m premarket), donde el rvol salia hasta 15x distinto. En
#   diario no aplica, pero el precio de entrada real lo pone Bitget.
# ======================================================================

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

from crh import crh

# ---------------------------------------------------------------- #
# UNIVERSO: papeles con perp de acciones en Bitget (144)
# ---------------------------------------------------------------- #
PERPS = [
    "AAL", "AAOI", "AAPL", "ABNB", "ACHR", "ADBE", "ADI", "AEHR", "ALAB",
    "AMAT", "AMC", "AMD", "AMGN", "AMKR", "AMZN", "ANET", "APD", "APLD",
    "APP", "ARM", "ASML", "ASTS", "ASX", "AVAV", "AVGO", "AXON", "BABA",
    "BAC", "BA", "BKNG", "BMNR", "BRK-B", "BUD", "BX", "CAT", "CCL",
    "CIEN", "CMCSA", "COHR", "COIN", "COST", "CPNG", "CRCL", "CRDO",
    "CRM", "CRWD", "CRWV", "CSCO", "DDOG", "DELL", "DJT", "DKNG", "ETN",
    "FOXA", "FUTU", "GE", "GEV", "GFS", "GILD", "GLW", "GME", "GOOGL",
    "GS", "HOOD", "HPE", "HPQ", "IBM", "INTC", "IONQ", "IREN", "ISRG",
    "JD", "JOBY", "JPM", "KLAC", "KO", "KTOS", "LIN", "LLY", "LMT",
    "LRCX", "MARA", "MAR", "MCD", "MDB", "MELI", "META", "MP", "MRK",
    "MRNA", "MRVL", "MSFT", "MSTR", "MUFG", "MU", "NBIS", "NET", "NIO",
    "NKE", "NOC", "NOW", "NTAP", "NVDA", "OKLO", "OPEN", "ORCL", "OSS",
    "OXY", "PANW", "PDD", "PEP", "PLTR", "PYPL", "QBTS", "QCOM", "QUBT",
    "RDDT", "RGTI", "RKLB", "ROK", "SHOP", "SIMO", "SMCI", "SMR", "SNDK",
    "SNOW", "SOFI", "SONY", "TM", "TSEM", "TSLA", "TSM", "TTWO", "TWLO",
    "TXN", "UBER", "UNH", "VRT", "VST", "V", "WDC", "WMT", "XOM", "ZM",
]

# ---------------------------------------------------------------- #
# FILTRO VALIDADO
# ---------------------------------------------------------------- #
GATILLO_REQ = "S_BOLL"
ADX_MIN = 25.0
ATR_MIN, ATR_MAX = 3.0, 8.0
BANDA_REQ = 3              # VOL
LOOKBACK = 3               # señal disparada en las ultimas N velas
APALANCAMIENTO = 5


def _n(v, alt=0.0):
    return float(v) if pd.notna(v) else alt


def analizar_apalancado(sym, df, lookback=LOOKBACK):
    """Aplica crh.py y devuelve el estado del papel frente al filtro x5.

    Devuelve None si no hubo B_SIGNAL fresca. Si la hubo, devuelve el dict
    SIEMPRE, con 'pasa' True/False y el motivo del rechazo: asi se puede
    mostrar tambien lo que quedo fuera y por que.
    """
    if df is None or df.empty or len(df) < 260:
        return None

    d = df.dropna(subset=["Close", "Volume"]).copy()
    d = d[d["Volume"] > 0]
    if len(d) < 260:
        return None

    d.columns = [c.lower() for c in d.columns]
    try:
        d = d[["open", "high", "low", "close", "volume"]].astype(float)
    except Exception:
        return None

    try:
        r = crh(d)
    except Exception:
        return None

    sig = r["B_SIGNAL"].fillna(False).astype(bool)
    if not sig.iloc[-lookback:].any():
        return None

    i = int(np.where(sig.values)[0][-1])
    barras = int(len(sig) - 1 - i)
    f_sig = r.iloc[i]
    f_hoy = r.iloc[-1]

    precio = _n(f_hoy["close"])
    precio_sig = _n(f_sig["close"])
    if precio <= 0:
        return None

    adx = _n(f_hoy["ADX_V"])
    atr_pct = _n(f_hoy["ATR_V"]) / precio * 100
    banda = int(f_sig["BANDA_PRE"]) if pd.notna(f_sig["BANDA_PRE"]) else 2
    tiene_boll = bool(f_sig.get(GATILLO_REQ, False))

    # --- el filtro, motivo por motivo ---
    faltas = []
    if not tiene_boll:
        faltas.append("sin BOLL")
    if adx < ADX_MIN:
        faltas.append(f"ADX {adx:.0f}<{ADX_MIN:.0f}")
    if not (ATR_MIN <= atr_pct <= ATR_MAX):
        faltas.append(f"ATR {atr_pct:.1f}% fuera de {ATR_MIN:.0f}-{ATR_MAX:.0f}%")
    banda_txt = {1: "BC", 2: "HYB", 3: "VOL"}.get(banda, "?")
    if banda != BANDA_REQ:
        faltas.append(f"banda {banda_txt} (se pide VOL)")

    sl_duro = _n(f_hoy["SL_DURO_FINAL"])
    stop_sys = _n(f_hoy["STOP_FINAL"])
    tp1 = _n(f_hoy["TP1_LEVEL"])

    # distancia al stop duro y lo que significa a x5
    dist_sl = (precio - sl_duro) / precio * 100 if sl_duro > 0 else None
    roi_sl = -dist_sl * APALANCAMIENTO if dist_sl is not None else None

    # --- calidad de la entrada de HOY -------------------------------
    # El backtest entra al cierre de la vela de señal. Si la señal fue hace
    # dias y el precio ya derivo, entrar hoy NO es la operacion validada:
    # el SL_DURO esta fijo desde la entrada original, asi que el aire que
    # queda hasta el stop es menor. Sin esto, una tarjeta puede mostrar
    # "-4% de ROI a x5" que en realidad significa "el stop esta encima".
    deriva = (precio / precio_sig - 1) * 100 if precio_sig > 0 else 0.0
    if dist_sl is not None and dist_sl < 1.5:
        calidad = "pasada"
    elif barras == 0:
        calidad = "fresca"
    elif deriva < -1.0:
        calidad = "pasada"
    else:
        calidad = "tardia"

    gatillos = [ab for col, ab in [
        ("S_PULL", "PULL"), ("S_IMPU", "IMPU"), ("S_BOLL", "BOLL"),
        ("S_SUELO", "SUELO"), ("S_MACD_CROSS", "MACD"), ("S_EARLY", "EARLY"),
        ("S_CONT", "CONT"), ("S_REBOTE_MA200", "REB200")]
        if bool(f_sig.get(col, False))]

    return {
        "sym": sym,
        "pasa": len(faltas) == 0,
        "faltas": faltas,
        "precio": precio,
        "precio_sig": precio_sig,
        "barras": barras,
        "adx": adx,
        "atr_pct": atr_pct,
        "banda": banda,
        "banda_txt": banda_txt,
        "gatillos": gatillos,
        "sl_duro": sl_duro,
        "stop_sys": stop_sys,
        "tp1": tp1,
        "dist_sl": dist_sl,
        "roi_sl": roi_sl,
        "deriva": deriva,
        "calidad": calidad,
        "is_long": bool(f_hoy["IS_LONG"]),
        "sell_hoy": bool(f_hoy["SELL_OK"]),
    }


@st.cache_data(ttl=300, show_spinner=False)
def barrido_apalancados(perps_tuple, lookback=LOOKBACK):
    """Descarga propia: el universo de perps no coincide con la watchlist
    del screener, asi que no comparten el batch."""
    batch = yf.download(list(perps_tuple), period="3y", group_by="ticker",
                        progress=False, auto_adjust=False, threads=True)
    out = []
    for sym in perps_tuple:
        try:
            if isinstance(batch.columns, pd.MultiIndex):
                df = batch[sym].copy() if sym in batch.columns.get_level_values(0) else None
            else:
                df = batch.copy()
            r = analizar_apalancado(sym, df, lookback)
        except Exception:
            r = None
        if r is not None:
            out.append(r)
    orden = {"fresca": 0, "tardia": 1, "pasada": 2}
    out.sort(key=lambda x: (not x["pasa"], orden.get(x["calidad"], 3),
                            x["barras"], -x["adx"]))
    return out


# ---------------------------------------------------------------- #
# RENDER
# ---------------------------------------------------------------- #
_CSS = """
<style>
.apl-wrap{margin-top:28px}
.apl-head{background:linear-gradient(135deg,#131a2b,#0f1522);border:1px solid #2a3450;
  border-radius:12px;padding:16px 22px;margin-bottom:14px}
.apl-head h2{font-family:'Syne',sans-serif;font-size:16px;font-weight:800;color:#e2e8f0;margin:0 0 4px 0}
.apl-head h2 span{color:#b48cff}
.apl-head p{color:#4a5568;font-size:10px;margin:0;letter-spacing:.06em;line-height:1.6}
.apl-card{background:#0d1220;border:1px solid #243048;border-left:3px solid #00e5a0;
  border-radius:10px;padding:14px 18px;margin-bottom:10px}
.apl-card.no{border-left-color:#4a5568;opacity:.62}
.apl-top{display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:8px}
.apl-sym{font-family:'Syne',sans-serif;font-size:17px;font-weight:800;color:#e2e8f0}
.apl-px{color:#4a5568;font-size:12px}
.apl-row{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:10px}
@media(max-width:700px){.apl-row{grid-template-columns:1fr 1fr}}
.apl-k{color:#4a5568;font-size:9px;letter-spacing:.1em;text-transform:uppercase}
.apl-v{color:#e2e8f0;font-size:13px;margin-top:2px}
.apl-v.g{color:#00e5a0}.apl-v.r{color:#ff4d6d}.apl-v.y{color:#ffd166}
.apl-sl{background:#141a28;border:1px dashed #ff4d6d;border-radius:8px;
  padding:9px 13px;margin-top:11px;color:#ff4d6d;font-size:11px;line-height:1.6}
.apl-pasada{background:#1c1520;border:1px solid #ffd166;border-radius:8px;
  padding:9px 13px;margin-top:11px;color:#ffd166;font-size:11px;line-height:1.6}
.apl-card.vieja{border-left-color:#ffd166}
.apl-why{color:#4a5568;font-size:10px;margin-top:8px}
.apl-empty{background:#0d1220;border:1px solid #243048;border-radius:10px;
  padding:22px;text-align:center;color:#4a5568;font-size:12px;line-height:1.8}
</style>
"""


def _card(x):
    ok = x["pasa"]
    gat = " ".join(x["gatillos"]) or "—"
    fresca = "hoy" if x["barras"] == 0 else f"hace {x['barras']}d"
    clase = "" if ok else "no"
    if ok and x["calidad"] == "pasada":
        clase = "vieja"
    sl_line = ""
    if ok and x["dist_sl"] is not None:
        if x["calidad"] == "pasada":
            sl_line = (
                f'<div class="apl-pasada">⛔ <b>ENTRADA PASADA — no tomarla hoy</b><br>'
                f'La señal fue en ${x["precio_sig"]:.2f} y el precio ya derivó '
                f'{x["deriva"]:+.1f}%. El stop duro está fijo en ${x["sl_duro"]:.2f}, '
                f'o sea a solo <b>{x["dist_sl"]:.1f}%</b> de acá: el trade ya se '
                f'comió su aire. Entrar ahora no es la operación del backtest, es '
                f'otra con mucho menos margen.</div>')
        else:
            tarde = ("" if x["calidad"] == "fresca" else
                     f'<br><b>Ojo:</b> la señal fue hace {x["barras"]}d en '
                     f'${x["precio_sig"]:.2f} ({x["deriva"]:+.1f}%). El backtest '
                     f'entra en la vela de señal, no después.')
            sl_line = (
                f'<div class="apl-sl">🛑 <b>STOP DURO OBLIGATORIO en ${x["sl_duro"]:.2f}</b>'
                f' · a {x["dist_sl"]:.1f}% del precio · a x{APALANCAMIENTO} eso es'
                f' <b>{x["roi_sl"]:.0f}% del margen</b><br>'
                f'Ponlo como orden real al abrir. Sin él, el peor trade del backtest'
                f' pasa de −8.3% a −28.4%.{tarde}</div>')
    why = ""
    if not ok:
        why = f'<div class="apl-why">No califica para apalancar: {" · ".join(x["faltas"])}. Spot nomas.</div>'
    return f"""
<div class="apl-card {clase}">
  <div class="apl-top">
    <span class="apl-sym">{x['sym']}</span>
    <span class="apl-px">${x['precio']:.2f} · señal {fresca} en ${x['precio_sig']:.2f}
      ({x['deriva']:+.1f}%)</span>
  </div>
  <div class="apl-row">
    <div><div class="apl-k">Gatillos</div><div class="apl-v {'g' if 'BOLL' in x['gatillos'] else ''}">{gat}</div></div>
    <div><div class="apl-k">ADX</div><div class="apl-v {'g' if x['adx']>=ADX_MIN else 'r'}">{x['adx']:.0f}</div></div>
    <div><div class="apl-k">ATR</div><div class="apl-v {'g' if ATR_MIN<=x['atr_pct']<=ATR_MAX else 'r'}">{x['atr_pct']:.1f}%</div></div>
    <div><div class="apl-k">Banda</div><div class="apl-v {'g' if x['banda']==BANDA_REQ else 'r'}">{x['banda_txt']}</div></div>
  </div>
  <div class="apl-row">
    <div><div class="apl-k">Stop sistema</div><div class="apl-v">${x['stop_sys']:.2f}</div></div>
    <div><div class="apl-k">TP1</div><div class="apl-v y">${x['tp1']:.2f}</div></div>
    <div><div class="apl-k">Posicion</div><div class="apl-v">{'abierta' if x['is_long'] else 'plana'}</div></div>
    <div><div class="apl-k">Venta hoy</div><div class="apl-v {'r' if x['sell_hoy'] else ''}">{'SI' if x['sell_hoy'] else 'no'}</div></div>
  </div>
  {sl_line}{why}
</div>"""


def render_apalancados(lookback=LOOKBACK, mostrar_descartados=True):
    """Seccion independiente. Llamar al final de app.py."""
    st.markdown(_CSS, unsafe_allow_html=True)
    st.markdown('<div class="apl-wrap">', unsafe_allow_html=True)
    st.markdown(f"""
<div class="apl-head">
  <h2>⚡ APALANCADOS <span>· perps Bitget x{APALANCAMIENTO}</span></h2>
  <p>{len(PERPS)} papeles con perp · filtro BOLL + ADX≥{ADX_MIN:.0f} + ATR {ATR_MIN:.0f}-{ATR_MAX:.0f}% + banda VOL<br>
  Validado 2 años: PF 2.12 · ratio 4.64:1 · peor trade −8.3% · año1 1.52 → año2 2.69<br>
  ~12 señales al mes en TODO el universo (33 en los últimos 60 días hábiles).
  La mayoría de los días esto está vacío, y así debe ser.</p>
</div>""", unsafe_allow_html=True)

    with st.spinner(f"Escaneando {len(PERPS)} perps con el motor CRH..."):
        todos = barrido_apalancados(tuple(PERPS), lookback)

    pasan = [x for x in todos if x["pasa"] and x["calidad"] != "pasada"]
    tarde = [x for x in todos if x["pasa"] and x["calidad"] == "pasada"]
    fuera = [x for x in todos if not x["pasa"]]

    if pasan:
        st.markdown(f'<div style="color:#00e5a0;font-size:12px;margin-bottom:8px;">'
                    f'<b>{len(pasan)} operable(s) hoy</b></div>',
                    unsafe_allow_html=True)
        for x in pasan:
            st.markdown(_card(x), unsafe_allow_html=True)
    else:
        extra = ""
        if tarde:
            extra = (f"<br>Hay {len(tarde)} que pasa(n) el filtro pero con la "
                     f"entrada ya pasada — abajo, para que veas por qué.")
        st.markdown(f"""
<div class="apl-empty">
  <b>Nada operable para apalancar hoy.</b><br>
  {len(fuera)} papel(es) con señal CRH fresca, ninguno pasa el filtro x{APALANCAMIENTO}.{extra}<br>
  Esto es lo normal: el filtro deja pasar ~7 al mes sobre 144 papeles.<br>
  No operar es la decisión correcta cuando no hay nada.
</div>""", unsafe_allow_html=True)

    if tarde:
        st.markdown(f'<div style="color:#ffd166;font-size:12px;margin:16px 0 8px;">'
                    f'<b>{len(tarde)} pasa(n) el filtro pero la entrada ya se fue</b>'
                    f'</div>', unsafe_allow_html=True)
        for x in tarde:
            st.markdown(_card(x), unsafe_allow_html=True)

    if mostrar_descartados and fuera:
        with st.expander(f"Ver los {len(fuera)} con señal CRH que NO califican para apalancar", expanded=False):
            st.markdown('<div style="font-size:11px;color:#4a5568;margin-bottom:8px;">'
                        'Tienen señal del sistema, pero no la configuración validada para x5. '
                        'Sirven como candidatos de spot, no para apalancar.</div>',
                        unsafe_allow_html=True)
            for x in fuera:
                st.markdown(_card(x), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
