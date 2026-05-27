# ======================================================================
# VMC CIPHER B SCREENER
# Ejecuta automaticamente al cargar · Sin botones · Sin bandas
# Muestra señales VMC de hoy y ayer con RSI, KDJ, ADX, Put/Call
# ======================================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="VMC Screener",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@700;800&display=swap');
:root {
    --bg:#080c14; --surface:#0d1220; --border:#1a2235; --border2:#243048;
    --text:#e2e8f0; --muted:#4a5568; --accent:#00d4ff;
    --green:#00e5a0; --red:#ff4d6d; --yellow:#ffd166;
}
html,body,[class*="css"]{font-family:'DM Mono',monospace;background:var(--bg)!important;color:var(--text)}
[data-testid="stSidebar"],[data-testid="collapsedControl"],#MainMenu,footer,header{display:none!important}
.block-container{padding:1rem 1.2rem 2rem!important;max-width:1400px!important}

.header{background:linear-gradient(135deg,var(--surface),#0f1928);border:1px solid var(--border2);border-radius:12px;padding:18px 24px;margin-bottom:20px;display:flex;align-items:center;justify-content:space-between}
.header h1{font-family:'Syne',sans-serif;font-size:clamp(15px,2.5vw,20px);font-weight:800;color:var(--text);margin:0 0 2px 0}
.header h1 span{color:var(--accent)}
.header p{color:var(--muted);font-size:10px;margin:0;letter-spacing:.08em}
.badge{background:#00d4ff15;border:1px solid #00d4ff44;color:var(--accent);font-size:10px;padding:4px 10px;border-radius:20px}

.idx-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:12px}
@media(max-width:700px){.idx-grid{grid-template-columns:1fr 1fr}}
.idx-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 14px}
.idx-label{color:var(--muted);font-size:9px;letter-spacing:.1em;text-transform:uppercase;margin-bottom:3px}
.idx-price{color:var(--text);font-size:clamp(14px,2vw,18px);font-weight:500;margin-bottom:1px}
.up{color:var(--green);font-size:11px}.down{color:var(--red);font-size:11px}

.ctx-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:16px}
@media(max-width:700px){.ctx-grid{grid-template-columns:1fr 1fr}}
.ctx-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 14px}
.ctx-label{color:var(--muted);font-size:9px;letter-spacing:.1em;text-transform:uppercase;margin-bottom:3px}
.ctx-val{color:var(--text);font-size:16px;font-weight:500}
.ctx-sub{font-size:11px;font-weight:500;margin-top:2px}
.ok{color:var(--green)}.warn{color:var(--yellow)}.bad{color:var(--red)}

.sec{font-family:'Syne',sans-serif;font-size:13px;font-weight:700;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;padding:10px 0 6px;border-bottom:1px solid var(--border2);margin-bottom:10px}
.glosario{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:10px 14px;margin-bottom:10px;font-size:11px;color:var(--muted);line-height:1.9}
.glosario b{color:#718096}
[data-testid="stDataFrame"]{border:1px solid var(--border)!important;border-radius:10px!important;font-family:'DM Mono',monospace!important;font-size:11px!important}
.footer{color:var(--border2);font-size:10px;text-align:center;padding:16px 0 4px}
[data-testid="stSelectbox"] label{font-size:11px!important;color:var(--muted)!important}
</style>
""", unsafe_allow_html=True)

# ======================================================================
# WATCHLIST
# ======================================================================
TICKERS = [
    "CHWY","ALT","PLTR","RBRK","MORN","CBRS","ISRG","MDT","DG","EPAM",
    "BRK-B","NCLH","CLS","GILD","FSLR","RTX","PSX","NBIS","ZTS","FICO",
    "BAC","GS","NOW","RMBS","MRVL","COF","BHP","SOL-USD","BTI",
    "SAP","FDX","TME","INTU","SONY","COHR","GDDY","PM","TSM","CRDO","NNE",
    "NRG","BLK","ENPH","LMT","DPZ","IONQ","VRT","VRTX","MSFT","AAPL",
    "MMM","HD","GOOGL","EBAY","SOFI","MPWR","LULU","CPRT","ETN","TJX",
    "ADP","NEE","DHR","T","VZ","QQQ","MU","TXN","OKTA","ZS","AFRM","GME",
    "BABA","RIOT","ARM","XLP","XLK","XLI","XLV","XLE","IWM","SPY","UBER",
    "PYPL","INTC","LRCX","AMAT","REGN","SHOP","HOOD","NET","CRWD","DDOG",
    "SNOW","MDB","MARA","COIN","AVGO","CSCO","ACN","LIN","TMO","LLY","ABBV",
    "ABNB","MRNA","AMT","ASTS","PANW","APH","SMCI","DELL","ANET","STX",
    "WDC","RCL","BKNG","TMUS","DE","CRM","ADBE","TGT","COST","CVX","XOM",
    "GE","ABT","AMZN","BTC-USD","SOUN","IBM","SMH","URA","CEG","NVO","MRK",
    "SPOT","EQIX","BA","FCX","AEM","MSTR","PEP","KO","WMT","PFE","DIS",
    "JNJ","MCD","JPM","MA","CAT","SBUX","PG","UNH","NVDA","NFLX","MELI",
    "NKE","META","ORCL","ASML","TSLA","AMD","QQQM","VOO","ACHR","LINK-USD","AVAX-USD",
    "CL=F","NG=F","SI=F","HG=F","GC=F","NQ=F",
    "EURUSD=X","USDCHF=X","GBPUSD=X","USDJPY=X","USDCOP=X","USDCLP=X","USDBRL=X",
    "ZIM","DLTR","BBY","WBD","GT","WYNN","MGM","SNAP","CVNA","ROKU",
    "HUM","ELV","UHS","ILMN","SWK","FNV","SBSW","GOLD","SQM","ALB","GSK","AZN",
    "BAYN.DE","ROG.SW","9988.HK",
]

# ======================================================================
# VMC CIPHER B — calculo Python fiel al Pine Script original (MPL 2.0)
# © vumanchu — https://www.tradingview.com/script/Msm4SjwI-VuManChu-Cipher-B-Divergences
# ======================================================================
def calcular_vmc(df):
    n1, n2 = 10, 21
    os2 = -53

    hlc3 = (df['High'] + df['Low'] + df['Close']) / 3
    esa  = hlc3.ewm(span=n1, adjust=False).mean()
    de   = (hlc3 - esa).abs().ewm(span=n1, adjust=False).mean()
    ci   = (hlc3 - esa) / (0.015 * de.replace(0, 1e-8))
    wt1  = ci.ewm(span=n2, adjust=False).mean()
    wt2  = wt1.rolling(4).mean()

    # MFI modificado
    mfi = ((df['Close'] - df['Open']) / (df['High'] - df['Low']).replace(0, 1e-8) * 150).rolling(60).mean()

    # Buy dot: wt2 cruza wt1 hacia arriba desde zona sobreventa + MFI positivo
    cross_up  = (wt2 > wt1) & (wt2.shift(1) <= wt1.shift(1))
    oversold  = wt2.shift(1) < os2
    vmc_buy   = cross_up & oversold & (mfi > 0)

    # Divergencia alcista: precio lower low pero wt2 higher low en sobreventa
    p_ll  = df['Close'] < df['Close'].rolling(5).min().shift(1)
    w_hl  = wt2 > wt2.rolling(5).min().shift(1)
    vmc_div = p_ll & w_hl & (wt2 < os2)

    return wt1, wt2, vmc_buy, vmc_div

# ======================================================================
# PUT/CALL RATIO
# ======================================================================
@st.cache_data(ttl=14400, show_spinner=False)
def calcular_pcr(ticker_name, precio_actual):
    try:
        tk = yf.Ticker(ticker_name)
        exps = tk.options
        if not exps: return None
        puts_all, calls_all = [], []
        total_pv = total_cv = total_po = total_co = 0
        for exp in exps[:5]:
            try:
                c = tk.option_chain(exp)
                puts_all.append(c.puts[['strike','openInterest']].copy())
                calls_all.append(c.calls[['strike','openInterest']].copy())
                total_pv += c.puts['volume'].fillna(0).sum()
                total_cv += c.calls['volume'].fillna(0).sum()
                total_po += c.puts['openInterest'].fillna(0).sum()
                total_co += c.calls['openInterest'].fillna(0).sum()
            except: continue
        if not puts_all or not calls_all: return None
        pd_ = pd.concat(puts_all).groupby('strike')['openInterest'].sum().reset_index()
        cd_ = pd.concat(calls_all).groupby('strike')['openInterest'].sum().reset_index()
        rlo, rhi = precio_actual*0.7, precio_actual*1.3
        pd_ = pd_[(pd_['strike']>=rlo)&(pd_['strike']<=rhi)]
        cd_ = cd_[(cd_['strike']>=rlo)&(cd_['strike']<=rhi)]
        if pd_.empty or cd_.empty: return None
        pw = float(pd_.loc[pd_['openInterest'].idxmax(),'strike'])
        cw = float(cd_.loc[cd_['openInterest'].idxmax(),'strike'])
        # PCR por volumen, fallback OI
        if total_cv > 0:
            pcr = round(total_pv/total_cv, 2)
        elif total_co > 0:
            pcr = round(total_po/total_co, 2)
        else:
            return None
        if   pcr < 0.7: pcr_lbl = "🟢"
        elif pcr > 1.0: pcr_lbl = "🔴"
        else:           pcr_lbl = "⚪"
        if precio_actual > cw:   gex = "🔴 Techo"
        elif precio_actual < pw: gex = "🟡 Piso"
        else:
            gex = "🟠 Cerca techo" if (cw-precio_actual)<(precio_actual-pw)*0.4 else "🟢 Zona"
        return {"pw": f"${pw:.0f}", "cw": f"${cw:.0f}", "pcr": f"{pcr_lbl} {pcr}", "gex": gex}
    except: return None

# ======================================================================
# MARKET DATA
# ======================================================================
@st.cache_data(ttl=300, show_spinner=False)
def get_market_data():
    indices = {"S&P 500":"^GSPC","Nasdaq":"^NDX","Dow":"^DJI","Russell":"^RUT"}
    result = {}
    for name, sym in indices.items():
        try:
            h = yf.Ticker(sym).history(period="5d",interval="1d")
            if len(h)>=2:
                prev=float(h['Close'].iloc[-2]); curr=float(h['Close'].iloc[-1])
                result[name]={"price":curr,"pct":(curr-prev)/prev*100}
        except: result[name]={"price":0,"pct":0}
    vix=0
    try:
        h=yf.Ticker("^VIX").history(period="5d",interval="1d")
        if not h.empty: vix=float(h['Close'].iloc[-1])
    except: pass
    btc_pct=0; btc_price=0
    try:
        h=yf.Ticker("BTC-USD").history(period="5d",interval="1d")
        if len(h)>=2:
            btc_price=float(h['Close'].iloc[-1])
            btc_pct=(btc_price-float(h['Close'].iloc[-2]))/float(h['Close'].iloc[-2])*100
    except: pass
    return result, vix, btc_pct, btc_price

# ======================================================================
# ANALIZAR TICKER
# ======================================================================
def analizar_ticker(sym):
    # Histórico largo para la banda (solo BETA necesita 2y)
    try:
        df2 = yf.download(sym, period="2y", progress=False, auto_adjust=True)
        if df2.empty: return None
        if isinstance(df2.columns, pd.MultiIndex): df2.columns = df2.columns.get_level_values(0)
        df2 = df2.dropna(subset=['Close','Volume'])
        df2 = df2[df2['Volume']>0]
    except: return None

    # 1 año para todos los indicadores
    try:
        df = yf.download(sym, period="1y", progress=False, auto_adjust=True)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.dropna(subset=['Close','Volume'])
        df = df[df['Volume']>0].copy()
        if len(df) < 200: return None
    except: return None

    # Barra de hoy en tiempo real
    try:
        dfh = yf.download(sym, period="5d", interval="1d", progress=False, auto_adjust=True)
        if isinstance(dfh.columns, pd.MultiIndex): dfh.columns = dfh.columns.get_level_values(0)
        if not dfh.empty and dfh.index[-1].date() > df.index[-1].date():
            df = pd.concat([df, dfh.iloc[[-1]][~dfh.iloc[[-1]].index.isin(df.index)]])
    except: pass

    # ── Indicadores ──
    df['MA20']  = df['Close'].ewm(span=20,adjust=False).mean()
    df['MA50']  = df['Close'].ewm(span=50,adjust=False).mean()
    df['MA200'] = df['Close'].ewm(span=200,adjust=False).mean()
    hl=(df['High']-df['Low']); hpc=(df['High']-df['Close'].shift(1)).abs(); lpc=(df['Low']-df['Close'].shift(1)).abs()
    df['ATR'] = pd.concat([hl,hpc,lpc],axis=1).max(axis=1).rolling(14).mean()

    # ADX
    hd=df['High']-df['High'].shift(1); ld=df['Low'].shift(1)-df['Low']
    dmp=np.where((hd>0)&(hd>ld),hd,0); dmm=np.where((ld>0)&(ld>hd),ld,0)
    t14=pd.concat([hl,hpc,lpc],axis=1).max(axis=1).rolling(14).sum().replace(0,1e-8)
    pdi=pd.Series(dmp,index=df.index).rolling(14).sum()*100/t14
    mdi=pd.Series(dmm,index=df.index).rolling(14).sum()*100/t14
    df['ADX'] = (abs(pdi-mdi)/(pdi+mdi).replace(0,1e-8)*100).rolling(9).mean()

    # KDJ
    lm=df['Low'].rolling(9).min(); hm=df['High'].rolling(9).max()
    rsv=(df['Close']-lm)/(hm-lm).replace(0,1e-8)*100
    k=rsv.ewm(alpha=1/3,adjust=False).mean(); d=k.ewm(alpha=1/3,adjust=False).mean()
    df['K']=k; df['D']=d; df['J']=3*k-2*d

    # RSI
    delta=df['Close'].diff(); gain=delta.clip(lower=0); loss=(-delta).clip(lower=0)
    df['RSI'] = 100-(100/(1+(gain.ewm(alpha=1/14,adjust=False).mean()/loss.ewm(alpha=1/14,adjust=False).mean().replace(0,1e-8))))

    # VMC Cipher B
    wt1, wt2, vmc_buy, vmc_div = calcular_vmc(df)
    df['VMC_BUY'] = vmc_buy
    df['VMC_DIV'] = vmc_div
    df['WT2']     = wt2

    # ── Señal: VMC hoy o ayer ──
    hoy  = bool(df['VMC_BUY'].iloc[-1] or df['VMC_DIV'].iloc[-1])
    ayer = bool(df['VMC_BUY'].iloc[-2] or df['VMC_DIV'].iloc[-2]) if len(df)>1 else False

    if not (hoy or ayer): return None

    precio = float(df['Close'].iloc[-1])
    rsi_v  = float(df['RSI'].iloc[-1]) if not pd.isna(df['RSI'].iloc[-1]) else 0
    adx_v  = float(df['ADX'].iloc[-1]) if not pd.isna(df['ADX'].iloc[-1]) else 0
    j_v    = float(df['J'].iloc[-1])   if not pd.isna(df['J'].iloc[-1])  else 0
    wt2_v  = float(df['WT2'].iloc[-1]) if not pd.isna(df['WT2'].iloc[-1]) else 0

    tipo = []
    if df['VMC_BUY'].iloc[-1]: tipo.append("🟢 Dot")
    if df['VMC_DIV'].iloc[-1]: tipo.append("🔵 Div")
    if df['VMC_BUY'].iloc[-2] if len(df)>1 else False: tipo.append("🟡 Dot-1")
    if df['VMC_DIV'].iloc[-2] if len(df)>1 else False: tipo.append("🔵 Div-1")

    return {
        "Ticker":  sym,
        "Precio":  f"${precio:.2f}",
        "precio_raw": precio,
        "Señal":   " ".join(tipo),
        "RSI":     f"{rsi_v:.1f}",
        "rsi_raw": rsi_v,
        "J(KDJ)":  f"{j_v:.1f}",
        "ADX":     f"{adx_v:.1f}",
        "WT2":     f"{wt2_v:.1f}",
    }

# ======================================================================
# HELPERS ESTILO
# ======================================================================
def cr(v):
    try:
        r=float(str(v))
        if r<33: return "color:#ff4d6d;font-weight:600"
        if r>65: return "color:#00e5a0;font-weight:600"
    except: pass
    return "color:#4a5568"

def cj(v):
    try:
        r=float(str(v))
        if r<20: return "color:#ff4d6d;font-weight:600"
        if r>80: return "color:#ffd166;font-weight:600"
    except: pass
    return "color:#4a5568"

def cs(v):
    s=str(v)
    if "🟢" in s: return "color:#00e5a0;font-weight:600"
    if "🔴" in s: return "color:#ff4d6d;font-weight:600"
    return "color:#4a5568"

# ======================================================================
# HEADER
# ======================================================================
st.markdown("""
<div class="header">
  <div>
    <h1>🌊 VMC Cipher B <span>Screener</span></h1>
    <p>WAVETREND OSCILLATOR · BUY DOTS + DIVERGENCIAS · HOY Y AYER · PUT/CALL 5 SEMANAS</p>
  </div>
  <div class="badge">LIVE</div>
</div>
""", unsafe_allow_html=True)

# ======================================================================
# MARKET DATA — siempre visible
# ======================================================================
indices, vix, btc_pct, btc_price = get_market_data()

st.markdown('<div class="idx-grid">', unsafe_allow_html=True)
for name, data in indices.items():
    p=data["price"]; pct=data["pct"]
    cls="up" if pct>=0 else "down"; sig="+" if pct>=0 else ""
    st.markdown(f'<div class="idx-card"><div class="idx-label">{name}</div><div class="idx-price">{p:,.0f}</div><div class="{cls}">{sig}{pct:.2f}%</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

sp_pct=indices.get("S&P 500",{}).get("pct",0)
vcls="ok" if vix<18 else ("warn" if vix<25 else "bad")
bcls="up" if btc_pct>=0 else "down"
bsig="+" if btc_pct>=0 else ""
bp=f"${btc_price:,.0f}" if btc_price>0 else "—"
if vix<18 and sp_pct>0:   ctx_cls,ctx_txt="ok","✅ Condiciones favorables"
elif vix>25 or sp_pct<-1: ctx_cls,ctx_txt="bad","⚠️ Mercado defensivo"
else:                      ctx_cls,ctx_txt="warn","⚪ Contexto mixto"

st.markdown(f"""
<div class="ctx-grid">
  <div class="ctx-card"><div class="ctx-label">VIX</div><div class="ctx-val">{vix:.1f}</div><div class="ctx-sub {vcls}">{"✅ Tranquilo" if vix<18 else ("⚠️ Moderado" if vix<25 else "🔴 Alto")}</div></div>
  <div class="ctx-card"><div class="ctx-label">BTC</div><div class="ctx-val {bcls}">{bp}</div><div class="ctx-sub {bcls}">{bsig}{btc_pct:.2f}%</div></div>
  <div class="ctx-card"><div class="ctx-label">Contexto</div><div class="ctx-val" style="font-size:12px;margin-top:4px;">&nbsp;</div><div class="ctx-sub {ctx_cls}" style="font-size:12px;">{ctx_txt}</div></div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ======================================================================
# ESCANEO AUTOMATICO — sin botón
# ======================================================================
st.markdown('<div class="sec">🌊 VMC BUY DOTS + DIVERGENCIAS — HOY Y AYER</div>', unsafe_allow_html=True)
st.markdown("""<div class="glosario">
<b>🟢 Dot</b> — círculo verde VMC hoy: WT2 cruza WT1 desde sobreventa + MFI positivo &nbsp;·&nbsp;
<b>🔵 Div</b> — divergencia alcista hoy: precio lower low + WT2 higher low en sobreventa &nbsp;·&nbsp;
<b>🟡 Dot-1</b> / <b>Div-1</b> — señal de ayer &nbsp;·&nbsp;
<b>WT2</b> — WaveTrend 2 (zona &lt;-53 = sobreventa extrema) &nbsp;·&nbsp;
<b>RSI</b> — rojo &lt;33 · verde &gt;65 &nbsp;·&nbsp;
<b>J(KDJ)</b> — &lt;20 zona de giro alcista &nbsp;·&nbsp;
<b>P/C</b> — Put/Call ratio por volumen 5 semanas: 🟢&lt;0.7 alcista · 🔴&gt;1.0 bajista
</div>""", unsafe_allow_html=True)

prog = st.progress(0, text="Escaneando VMC Cipher B...")
resultados = []

for idx, sym in enumerate(TICKERS):
    prog.progress(int((idx+1)/len(TICKERS)*100), text=f"{sym}  ({idx+1}/{len(TICKERS)})")
    datos = analizar_ticker(sym)
    if datos is None: continue

    # Put/Call ratio
    skip_opciones = any(x in sym for x in ['-USD','-F','=X','=F','.DE','.SW','.HK'])
    pcr_data = None
    if not skip_opciones:
        pcr_data = calcular_pcr(sym, datos["precio_raw"])

    resultados.append({
        "Ticker":  datos["Ticker"],
        "Precio":  datos["Precio"],
        "Señal":   datos["Señal"],
        "WT2":     datos["WT2"],
        "RSI":     datos["RSI"],
        "J(KDJ)":  datos["J(KDJ)"],
        "ADX":     datos["ADX"],
        "Put Wall": pcr_data["pw"]  if pcr_data else "—",
        "Call Wall":pcr_data["cw"]  if pcr_data else "—",
        "P/C":     pcr_data["pcr"] if pcr_data else "—",
        "GEX":     pcr_data["gex"] if pcr_data else "—",
    })

prog.empty()

if resultados:
    df_out = pd.DataFrame(resultados).reset_index(drop=True)
    df_out.index = range(1, len(df_out)+1)
    st.success(f"✅ {len(resultados)} señales VMC encontradas en {len(TICKERS)} tickers")
    st.dataframe(
        df_out.style
            .map(cr,  subset=["RSI"])
            .map(cj,  subset=["J(KDJ)"])
            .map(cs,  subset=["P/C","GEX"]),
        use_container_width=True
    )
    st.download_button("⬇️ CSV", df_out.to_csv(index=False).encode(), "vmc_screener.csv", "text/csv")
else:
    st.info("Sin señales VMC hoy ni ayer en la watchlist.")

st.markdown('<p class="footer">VMC Cipher B · © vumanchu MPL 2.0 · Solo fines educativos · No es asesoría financiera</p>', unsafe_allow_html=True)
