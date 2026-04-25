import streamlit as st
import os

# ─────────────────────────────────────────────
#  Global CSS injected on every page
# ─────────────────────────────────────────────
GLOBAL_CSS = """
<style>
/* ──────────── KEYFRAME ANIMATIONS ──────────── */
@keyframes fadeInUp {
  from { opacity:0; transform:translateY(22px); }
  to   { opacity:1; transform:translateY(0); }
}
@keyframes fadeIn {
  from { opacity:0; }
  to   { opacity:1; }
}
@keyframes slideLeft {
  from { opacity:0; transform:translateX(-18px); }
  to   { opacity:1; transform:translateX(0); }
}
@keyframes gradientFlow {
  0%   { background-position:0% 50%; }
  50%  { background-position:100% 50%; }
  100% { background-position:0% 50%; }
}
@keyframes pulseBorder {
  0%,100% { box-shadow:0 0 0 0 rgba(198,40,40,0.45); }
  50%      { box-shadow:0 0 0 7px rgba(198,40,40,0); }
}
@keyframes shimmer {
  0%   { background-position:-400px 0; }
  100% { background-position:400px 0; }
}
@keyframes scaleIn {
  from { opacity:0; transform:scale(0.94); }
  to   { opacity:1; transform:scale(1); }
}
@keyframes bounceIn {
  0%   { opacity:0; transform:scale(0.7); }
  60%  { opacity:1; transform:scale(1.05); }
  100% {            transform:scale(1); }
}

/* ──────────── BASE ──────────── */
.stApp { background:#F0F2F5 !important; }

/* Make Streamlit top header transparent — keeps the menu button visible */
header[data-testid="stHeader"] {
  background: transparent !important;
  box-shadow: none !important;
}
[data-testid="stDecoration"] { display: none !important; }
.block-container {
  padding-top:0.6rem !important;
  padding-bottom:1.5rem !important;
  padding-left:1rem !important;
  padding-right:1rem !important;
  max-width:1280px !important;
}

/* ──────────── HERO BANNER ──────────── */
.hero {
  background: linear-gradient(135deg,#1877F2 0%,#0D47A1 55%,#311B92 100%);
  background-size:300% 300%;
  animation:gradientFlow 10s ease infinite;
  border-radius:0 0 20px 20px;
  padding:28px 32px 24px;
  color:#fff;
  position:relative;
  overflow:hidden;
  /* bleed to full container width by cancelling block-container padding */
  margin-left:-1rem;
  margin-right:-1rem;
  margin-top:-0.6rem;
  margin-bottom:22px;
  box-shadow:0 8px 32px rgba(24,119,242,0.35);
}
.hero::before {
  content:'';
  position:absolute; top:-60px; right:-40px;
  width:260px; height:260px;
  background:rgba(255,255,255,0.06);
  border-radius:50%;
}
.hero::after {
  content:'';
  position:absolute; bottom:-80px; right:80px;
  width:180px; height:180px;
  background:rgba(255,255,255,0.04);
  border-radius:50%;
}
.hero-title  { font-size:22px; font-weight:900; margin:0; letter-spacing:-0.3px; }
.hero-sub    { font-size:13px; opacity:.80; margin-top:5px; }
.hero-badges { display:flex; gap:8px; flex-wrap:wrap; margin-top:14px; }
.hero-badge  {
  display:inline-flex; align-items:center; gap:5px;
  background:rgba(255,255,255,0.15);
  border:1px solid rgba(255,255,255,0.25);
  backdrop-filter:blur(8px);
  padding:4px 14px; border-radius:20px;
  font-size:11px; font-weight:700; letter-spacing:0.3px;
}

/* ──────────── KPI CARDS (HTML grid) ──────────── */
.kpi-grid {
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:14px;
  margin-bottom:24px;
}
.kpi-card {
  background:#fff;
  border-radius:16px;
  padding:18px 20px;
  box-shadow:0 2px 14px rgba(0,0,0,0.07);
  position:relative;
  overflow:hidden;
  transition:transform .25s ease, box-shadow .25s ease;
  animation:fadeInUp .5s ease both;
  cursor:default;
}
.kpi-card:hover {
  transform:translateY(-5px);
  box-shadow:0 10px 28px rgba(0,0,0,0.13);
}
.kpi-card::before {
  content:'';
  position:absolute;
  bottom:0; left:0; right:0; height:4px;
  background:var(--accent,#1877F2);
  border-radius:0 0 16px 16px;
}
.kpi-icon {
  width:42px; height:42px; border-radius:12px;
  display:flex; align-items:center; justify-content:center;
  font-size:20px; margin-bottom:12px;
  background:var(--icon-bg,#EBF3FF);
}
.kpi-lbl  { font-size:10px; font-weight:800; color:#9EA3A9; text-transform:uppercase; letter-spacing:1px; }
.kpi-val  { font-size:26px; font-weight:900; color:#1C1E21; margin:4px 0 1px; line-height:1.1; }
.kpi-sub  { font-size:11px; color:#B0B3B8; }
/* stagger delays */
.kpi-card:nth-child(1){animation-delay:.04s}
.kpi-card:nth-child(2){animation-delay:.09s}
.kpi-card:nth-child(3){animation-delay:.14s}
.kpi-card:nth-child(4){animation-delay:.19s}
.kpi-card:nth-child(5){animation-delay:.24s}
.kpi-card:nth-child(6){animation-delay:.29s}

/* ──────────── SECTION HEADER ──────────── */
.sec {
  display:flex; align-items:center; gap:10px;
  margin:24px 0 12px;
  animation:fadeIn .35s ease;
}
.sec-bar {
  width:5px; height:22px;
  background:linear-gradient(180deg,#1877F2,#0052CC);
  border-radius:3px;
  flex-shrink:0;
}
.sec-title { font-size:16px; font-weight:800; color:#1C1E21; }

/* ──────────── CHART WRAPPER ──────────── */
.chart-box {
  background:#fff;
  border-radius:16px;
  padding:8px 8px 4px;
  box-shadow:0 2px 14px rgba(0,0,0,0.07);
  animation:fadeInUp .5s ease both;
  transition:box-shadow .25s ease;
  margin-bottom:14px;
}
.chart-box:hover { box-shadow:0 8px 24px rgba(0,0,0,0.11); }

/* ──────────── ALERT CARDS ──────────── */
.al {
  border-radius:12px; padding:12px 16px; margin:7px 0;
  animation:slideLeft .38s ease both;
  transition:transform .15s ease;
  position:relative; overflow:hidden;
}
.al:hover { transform:translateX(4px); }
.al-crit {
  background:linear-gradient(135deg,#FFEBEE,#FFCDD2);
  border-left:4px solid #C62828;
  animation:slideLeft .38s ease both, pulseBorder 2.5s infinite;
}
.al-warn { background:linear-gradient(135deg,#FFF8E1,#FFECB3); border-left:4px solid #F9A825; }
.al-info { background:linear-gradient(135deg,#E3F2FD,#BBDEFB); border-left:4px solid #1565C0; }
.al-ok   { background:linear-gradient(135deg,#E8F5E9,#C8E6C9); border-left:4px solid #2E7D32; }
.al-t    { font-weight:800; font-size:11px; text-transform:uppercase; letter-spacing:.7px; }
.al-m    { font-size:13px; color:#333; margin:3px 0; }
.al-ts   { font-size:11px; color:#90949C; }
/* stagger */
.al:nth-child(1){animation-delay:.05s}
.al:nth-child(2){animation-delay:.10s}
.al:nth-child(3){animation-delay:.15s}
.al:nth-child(4){animation-delay:.20s}
.al:nth-child(5){animation-delay:.25s}

/* ──────────── COPY CARDS ──────────── */
.copy-card {
  background:#fff; border-radius:16px; padding:20px 22px;
  box-shadow:0 2px 14px rgba(0,0,0,0.07);
  border-top:4px solid #1877F2;
  margin-bottom:14px;
  animation:fadeInUp .45s ease both;
  transition:transform .22s ease, box-shadow .22s ease;
}
.copy-card:hover { transform:translateY(-4px); box-shadow:0 10px 28px rgba(0,0,0,0.12); }
.copy-card-used  { border-top-color:#2E7D32; }
.copy-hl  { font-size:16px; font-weight:900; color:#1C1E21; line-height:1.3; }
.copy-bod { font-size:13px; color:#555; margin:8px 0; line-height:1.6; }
.copy-hook{ font-size:12px; color:#1877F2; font-style:italic; margin-bottom:6px; }
.copy-cta {
  display:inline-block;
  background:linear-gradient(135deg,#1877F2,#0052CC);
  color:#fff !important; padding:4px 16px;
  border-radius:20px; font-size:11px; font-weight:800;
  letter-spacing:.3px;
}
.copy-note{ background:#FFF3E0; color:#E65C00; padding:5px 12px; border-radius:8px; font-size:11px; margin-top:8px; }
.copy-meta{ font-size:11px; color:#90949C; margin-top:10px; }
.tag { display:inline-block; background:#F0F2F5; color:#606770; padding:2px 10px; border-radius:12px; font-size:11px; font-weight:700; margin:2px 2px 0 0; }

/* ──────────── BADGES ──────────── */
.badge { display:inline-block; padding:3px 12px; border-radius:20px; font-size:11px; font-weight:800; letter-spacing:.4px; }
.badge-active  { background:linear-gradient(135deg,#E8F5E9,#C8E6C9); color:#2E7D32; }
.badge-paused  { background:linear-gradient(135deg,#FFF3E0,#FFD0A0); color:#E65C00; }
.badge-deleted { background:linear-gradient(135deg,#FFEBEE,#FFCDD2); color:#C62828; }
.badge-archived{ background:#F5F5F5; color:#606770; }

/* ──────────── STREAMLIT COMPONENT OVERRIDES ──────────── */
/* Metric widget */
[data-testid="stMetric"] {
  background:#fff !important;
  border-radius:14px !important;
  padding:14px 18px !important;
  box-shadow:0 2px 12px rgba(0,0,0,0.07) !important;
  animation:scaleIn .35s ease !important;
  transition:box-shadow .2s ease !important;
}
[data-testid="stMetric"]:hover { box-shadow:0 6px 20px rgba(0,0,0,0.11) !important; }
[data-testid="stMetricValue"] { font-size:22px !important; font-weight:900 !important; color:#1C1E21 !important; }
[data-testid="stMetricLabel"] { font-size:10px !important; font-weight:800 !important; color:#9EA3A9 !important; text-transform:uppercase !important; letter-spacing:.8px !important; }

/* Expander */
details > summary {
  background:#fff !important;
  border-radius:12px !important;
  padding:13px 18px !important;
  font-weight:700 !important;
  box-shadow:0 1px 8px rgba(0,0,0,0.07) !important;
  transition:box-shadow .2s ease !important;
  border:none !important;
}
details > summary:hover { box-shadow:0 5px 16px rgba(0,0,0,0.11) !important; }

/* Buttons */
.stButton > button {
  border-radius:10px !important;
  font-weight:700 !important;
  transition:transform .15s ease, box-shadow .15s ease !important;
}
.stButton > button:hover {
  transform:translateY(-2px) !important;
  box-shadow:0 6px 16px rgba(0,0,0,0.15) !important;
}

/* Download button */
.stDownloadButton > button {
  background:linear-gradient(135deg,#1877F2,#0052CC) !important;
  color:#fff !important; border:none !important;
  border-radius:10px !important; font-weight:700 !important;
  transition:opacity .2s, transform .15s !important;
}
.stDownloadButton > button:hover { opacity:.88 !important; transform:translateY(-2px) !important; }

/* Inputs */
.stSelectbox > label, .stTextInput > label {
  font-size:11px !important; font-weight:800 !important;
  color:#9EA3A9 !important; text-transform:uppercase !important; letter-spacing:.7px !important;
}
.stSelectbox > div > div, .stTextInput > div > div > input {
  border-radius:10px !important;
  border-color:#E9EBEE !important;
  transition:border-color .2s, box-shadow .2s !important;
}
.stSelectbox > div > div:focus-within,
.stTextInput > div > div > input:focus {
  border-color:#1877F2 !important;
  box-shadow:0 0 0 3px rgba(24,119,242,0.15) !important;
}

/* Dataframe */
[data-testid="stDataFrame"] { border-radius:12px !important; overflow:hidden; box-shadow:0 2px 10px rgba(0,0,0,0.07) !important; }

/* Divider */
hr { border-color:#EAEBEE !important; margin:14px 0 !important; }

/* ──────────── SIDEBAR ──────────── */
section[data-testid="stSidebar"] {
  background:linear-gradient(180deg,#0D1B2A 0%,#1A2840 60%,#1E3050 100%) !important;
  border-right:1px solid rgba(255,255,255,0.06) !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div { color:#D8DCE6 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color:#fff !important; }
section[data-testid="stSidebar"] [data-testid="stMetric"] {
  background:rgba(255,255,255,0.07) !important;
  box-shadow:none !important;
}
section[data-testid="stSidebar"] [data-testid="stMetricValue"],
section[data-testid="stSidebar"] [data-testid="stMetricLabel"] { color:#fff !important; }
section[data-testid="stSidebar"] .stButton > button {
  background:rgba(255,255,255,0.1) !important;
  border:1px solid rgba(255,255,255,0.15) !important;
  color:#fff !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
  background:rgba(255,255,255,0.18) !important;
}
section[data-testid="stSidebar"] hr { border-color:rgba(255,255,255,0.1) !important; }

/* ──────────── ALIGNMENT SYSTEM ──────────── */

/*
  Core rule: when a horizontal block contains a selectbox or text input
  (which have a label above them), align ALL columns to the bottom so
  buttons/other elements sit flush with the input boxes.
*/
[data-testid="stHorizontalBlock"]:has([data-testid="stSelectbox"]),
[data-testid="stHorizontalBlock"]:has([data-testid="stTextInput"]) {
    align-items: flex-end !important;
    gap: 12px !important;
}

/* All buttons the same height as form inputs */
[data-testid="stButton"] > button,
[data-testid="stDownloadButton"] > button {
    height: 42px !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* Form inputs consistent height */
[data-testid="stSelectbox"] > div > div,
[data-testid="stTextInput"]  > div > div > input,
[data-testid="stNumberInput"]> div > div > input {
    height: 42px !important;
    min-height: 42px !important;
    line-height: 1.4 !important;
}

/* Labels above inputs — consistent size */
[data-testid="stSelectbox"]  > label,
[data-testid="stTextInput"]  > label,
[data-testid="stNumberInput"]> label,
.stSelectbox > label,
.stTextInput > label {
    font-size: 11px !important;
    font-weight: 800 !important;
    color: #9EA3A9 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.7px !important;
    margin-bottom: 4px !important;
    display: block !important;
}

/* Metric cards — all same height, centered */
[data-testid="stMetric"] {
    min-height: 82px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
}
[data-testid="stMetricValue"] {
    font-size: 22px !important;
    font-weight: 900 !important;
    line-height: 1.2 !important;
}
[data-testid="stMetricLabel"] {
    font-size: 10px !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
    margin-bottom: 2px !important;
}

/* Plotly charts — consistent radius and no overflow */
.stPlotlyChart { border-radius: 12px !important; overflow: hidden !important; }
.stPlotlyChart > div { border-radius: 12px !important; }
.js-plotly-plot .plotly { border-radius: 12px !important; }

/* Expander content padding */
[data-testid="stExpander"] details > div[data-testid="stExpanderDetails"] {
    padding: 16px 12px !important;
}
[data-testid="stExpander"] details summary {
    padding: 12px 16px !important;
}

/* Tabs */
[data-testid="stTabs"] [data-testid="stTab"] {
    font-weight: 700 !important;
    font-size: 13px !important;
    padding: 10px 18px !important;
    border-radius: 8px 8px 0 0 !important;
}
[data-testid="stTabs"] [data-testid="stTab"][aria-selected="true"] {
    color: #1877F2 !important;
    border-bottom: 3px solid #1877F2 !important;
}

/* Columns gap */
[data-testid="stHorizontalBlock"] {
    gap: 14px !important;
}

/* Info / success / error boxes */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    font-size: 13px !important;
}

/* Dataframe */
[data-testid="stDataFrame"] iframe {
    border-radius: 12px !important;
}

/* Download button full width fix */
[data-testid="stDownloadButton"] {
    width: 100% !important;
}
.stDownloadButton > button {
    background: linear-gradient(135deg, #1877F2, #0052CC) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    height: 42px !important;
}

/* Number input arrows hidden for cleaner look */
[data-testid="stNumberInput"] input::-webkit-outer-spin-button,
[data-testid="stNumberInput"] input::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
}

/* ──────────── MOBILE RESPONSIVE ──────────── */
@media (max-width: 768px) {
  /* Stack columns */
  [data-testid="stHorizontalBlock"] {
    flex-direction:column !important;
    gap:10px !important;
  }
  [data-testid="stColumn"],
  [data-testid="stHorizontalBlock"] > div {
    min-width:100% !important;
    width:100% !important;
    flex:none !important;
  }
  /* Hero */
  .hero { padding:18px 16px 16px; border-radius:14px; }
  .hero-title { font-size:17px; }
  /* KPI grid */
  .kpi-grid { grid-template-columns:repeat(2,1fr); gap:10px; }
  .kpi-val  { font-size:21px; }
  .kpi-card { padding:14px 16px; }
  /* Charts */
  .chart-box { padding:4px 4px 2px; }
  /* Touch targets */
  .stButton > button { min-height:44px !important; font-size:14px !important; }
  /* Block container */
  .block-container { padding-left:0.8rem !important; padding-right:0.8rem !important; }
  /* Scrollable tables */
  [data-testid="stDataFrame"] { overflow-x:auto !important; }
}
@media (max-width: 480px) {
  .kpi-grid   { grid-template-columns:1fr 1fr; gap:8px; }
  .hero-badge { font-size:10px; padding:3px 10px; }
  .block-container { padding-left:0.5rem !important; padding-right:0.5rem !important; }
  .sec-title  { font-size:14px; }
}
</style>
"""

def inject(extra="", brand_color="#1877F2"):
    """Inject global CSS, replacing the brand color placeholder."""
    css = GLOBAL_CSS.replace("#1877F2", brand_color).replace("#0052CC", _darken(brand_color))
    st.markdown(css + (f"<style>{extra}</style>" if extra else ""), unsafe_allow_html=True)


def _darken(hex_color: str) -> str:
    """Simple darken: multiply each channel by 0.75."""
    try:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return "#{:02X}{:02X}{:02X}".format(int(r*.75), int(g*.75), int(b*.75))
    except Exception:
        return "#0052CC"


def hero(title, subtitle, badges=None, logo_path=None):
    badge_html = ""
    if badges:
        inner = "".join(f'<span class="hero-badge">{b}</span>' for b in badges)
        badge_html = f'<div class="hero-badges">{inner}</div>'
    logo_html = ""
    if logo_path and os.path.exists(logo_path):
        import base64
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{b64}" style="height:44px;border-radius:8px;margin-right:14px;vertical-align:middle">'
    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">{logo_html}{title}</div>
        <div class="hero-sub">{subtitle}</div>
        {badge_html}
    </div>
    """, unsafe_allow_html=True)


def sec(icon, title):
    st.markdown(f"""
    <div class="sec">
        <div class="sec-bar"></div>
        <span class="sec-title">{icon}&nbsp; {title}</span>
    </div>
    """, unsafe_allow_html=True)


def kpi_grid(cards):
    """cards = list of (icon, label, value, sub, hex_color)"""
    inner = ""
    for icon, label, value, sub, color in cards:
        icon_bg = color + "22"  # 13% opacity hex
        inner += f"""
        <div class="kpi-card" style="--accent:{color};--icon-bg:{icon_bg}">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-lbl">{label}</div>
            <div class="kpi-val">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>"""
    st.markdown(f'<div class="kpi-grid">{inner}</div>', unsafe_allow_html=True)


def alert_card(atype, msg, ts, camp=""):
    CRITICAL = {"spend_spike", "budget_depleted"}
    WARNING  = {"low_roas", "high_cpa"}
    if atype in CRITICAL:
        css, icon = "al-crit", "&#x1F534;"
    elif atype in WARNING:
        css, icon = "al-warn", "&#x1F7E1;"
    else:
        css, icon = "al-info", "&#x1F535;"
    label    = atype.replace("_", " ").upper()
    camp_str = f'&nbsp;<span style="font-size:10px;color:#90949C">Campaign {camp}</span>' if camp else ""
    st.markdown(f"""
    <div class="al {css}">
        <div class="al-t">{icon} {label}</div>
        <div class="al-m">{msg}</div>
        <div class="al-ts">{ts}{camp_str}</div>
    </div>
    """, unsafe_allow_html=True)
