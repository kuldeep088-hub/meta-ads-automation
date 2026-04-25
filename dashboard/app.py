import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dashboard.auth import check_login, login_page, logout
from dashboard import data, charts, styles

st.set_page_config(
    page_title="Meta Ads Portal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

if not check_login():
    login_page()
    st.stop()

# ── Load settings ─────────────────────────────────────────────
settings     = data.get_all_settings()
brand_name   = settings.get("brand_name",  "Meta Ads")
brand_color  = settings.get("brand_color", "#1877F2")
logo_path    = os.path.join(os.path.dirname(__file__), "static", "logo.png")

styles.inject(brand_color=brand_color)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    logo_html = ""
    if os.path.exists(logo_path):
        import base64
        with open(logo_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        logo_html = f'<img src="data:image/png;base64,{b64}" style="height:40px;border-radius:8px;margin-bottom:6px">'

    st.markdown(f"""
    <div style="text-align:center;padding:14px 0 10px">
        {logo_html}
        <div style="font-size:18px;font-weight:900;color:#fff;letter-spacing:-0.3px">{brand_name}</div>
        <div style="font-size:11px;color:#8A9BBE;margin-top:3px">Client Reporting Portal</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # ── Multi-Account Switcher ────────────────────────────────
    accounts_df = data.get_accounts()
    if not accounts_df.empty:
        st.markdown('<p style="font-size:10px;font-weight:800;color:#8A9BBE;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">Ad Account</p>', unsafe_allow_html=True)
        acct_names = accounts_df["name"].tolist()
        active_idx = 0
        if "is_active" in accounts_df.columns:
            active_rows = accounts_df[accounts_df["is_active"] == 1]
            if not active_rows.empty:
                active_idx = acct_names.index(active_rows.iloc[0]["name"])
        chosen = st.selectbox("Account", acct_names, index=active_idx, label_visibility="collapsed")
        chosen_id = accounts_df[accounts_df["name"] == chosen].iloc[0]["account_id"]
        if st.button("Switch Account", use_container_width=True):
            data.set_active_account(chosen_id)
            st.session_state["active_account"] = chosen
            st.rerun()
        st.divider()

    # ── Live Stats ────────────────────────────────────────────
    stats  = data.get_stats()
    totals = data.get_account_totals()
    st.markdown('<p style="font-size:10px;font-weight:800;color:#8A9BBE;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">Live Stats</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.metric("Campaigns", stats.get("campaigns", 0))
    c2.metric("Active",    stats.get("active_campaigns", 0))
    c1.metric("Ad Sets",   stats.get("adsets", 0))
    c2.metric("Ads",       stats.get("ads", 0))

    st.divider()
    st.markdown(f"""
    <div style="display:flex;flex-direction:column;gap:7px">
      <div style="display:flex;justify-content:space-between;font-size:13px">
        <span>Total Spend</span><span style="font-weight:800;color:#fff">&#8377;{totals.get('total_spend',0):,.0f}</span>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:13px">
        <span>Clicks</span><span style="font-weight:800;color:#fff">{totals.get('total_clicks',0):,}</span>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:13px">
        <span>Leads</span><span style="font-weight:800;color:#fff">{totals.get('total_leads',0):,}</span>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:13px">
        <span>Avg CTR</span><span style="font-weight:800;color:#fff">{totals.get('avg_ctr',0):.2f}%</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    if st.button("&#x1F6AA;  Logout", use_container_width=True):
        logout()

# ── Hero ──────────────────────────────────────────────────────
styles.hero(
    f"{brand_name} — Client Reporting Portal",
    "Real-time campaign analytics, budget optimization, and AI-powered insights",
    badges=[
        f"&#x1F7E2; {stats.get('active_campaigns',0)} Active",
        f"&#x1F4B0; &#8377;{totals.get('total_spend',0):,.0f} Spent",
        f"&#x26A1; Live Data",
    ],
    logo_path=logo_path if os.path.exists(logo_path) else None,
)

# ── KPIs ──────────────────────────────────────────────────────
styles.kpi_grid([
    ("&#x1F4B8;","Total Spend",      f"&#8377;{totals.get('total_spend',0):,.0f}",  "All time",             brand_color),
    ("&#x1F4A5;","Total Clicks",     f"{totals.get('total_clicks',0):,}",           "All time",             "#E65C00"),
    ("&#x1F3AF;","Total Leads",      f"{totals.get('total_leads',0):,}",            "All time",             "#2E7D32"),
    ("&#x1F4CA;","Avg CTR",          f"{totals.get('avg_ctr',0):.2f}%",            "All campaigns",        "#9C27B0"),
    ("&#x1F680;","Active Campaigns", str(stats.get('active_campaigns',0)),          f"of {stats.get('campaigns',0)} total","#00BCD4"),
    ("&#x1F514;","Total Alerts",     str(stats.get('alerts',0)),                    "Triggered",            "#FF5722"),
])

# ── Charts ────────────────────────────────────────────────────
styles.sec("📈", "Spend & ROAS")
time_df = data.get_spend_over_time()
c1, c2 = st.columns(2)
with c1: st.plotly_chart(charts.spend_chart(time_df), width="stretch")
with c2: st.plotly_chart(charts.roas_chart(time_df),  width="stretch")

styles.sec("📢", "Campaign Breakdown")
camp_df = data.get_campaigns()
perf_df = data.get_campaign_performance()
c3, c4 = st.columns(2)
with c3: st.plotly_chart(charts.campaign_status_pie(camp_df), width="stretch")
with c4: st.plotly_chart(charts.top_campaigns_bar(perf_df),   width="stretch")

# ── CTR + Alerts ─────────────────────────────────────────────
styles.sec("🔔", "CTR Trend & Live Alerts")
c5, c6 = st.columns([3, 2])
with c5:
    st.plotly_chart(charts.ctr_chart(time_df), width="stretch")
with c6:
    alerts_df = data.get_alerts(limit=6)
    if alerts_df.empty:
        st.markdown('<div class="al al-ok"><div class="al-t">&#x2714; All Clear</div><div class="al-m">No alerts. All campaigns healthy.</div></div>', unsafe_allow_html=True)
    else:
        for _, row in alerts_df.iterrows():
            styles.alert_card(row.get("alert_type",""), row.get("message","N/A"),
                              str(row.get("created_at",""))[:16], row.get("campaign_id",""))

# ── Nav tiles ─────────────────────────────────────────────────
styles.sec("🗺️", "Pages")
PAGES = [
    ("📊","Overview",      "KPIs, trends, goals",           brand_color),
    ("📢","Campaigns",     "Campaign cards & health scores", "#E65C00"),
    ("📈","Reports",       "Charts + PDF/Excel export",      "#2E7D32"),
    ("🚨","Alerts",        "Alert history & distribution",   "#C62828"),
    ("⚙️","Optimization",  "Budget actions & log",           "#9C27B0"),
    ("✍️","Ad Copy",       "AI copy variations",             "#00BCD4"),
    ("🖼️","Creatives",     "Ad creative comparison",         "#FF5722"),
    ("⚙️","Settings",      "Branding, goals & scheduler",    "#607D8B"),
]
cols = st.columns(4)
for i, (icon, title, desc, color) in enumerate(PAGES):
    with cols[i % 4]:
        st.markdown(f"""
        <div style="background:#fff;border-radius:14px;padding:16px 14px;text-align:center;
                    box-shadow:0 2px 12px rgba(0,0,0,0.07);margin-bottom:14px;
                    animation:fadeInUp .5s ease {i*0.05:.2f}s both;
                    transition:transform .2s,box-shadow .2s;border-top:4px solid {color}"
             onmouseover="this.style.transform='translateY(-4px)';this.style.boxShadow='0 10px 28px rgba(0,0,0,0.12)'"
             onmouseout="this.style.transform='';this.style.boxShadow='0 2px 12px rgba(0,0,0,0.07)'">
          <div style="font-size:26px">{icon}</div>
          <div style="font-size:13px;font-weight:800;color:#1C1E21;margin-top:8px">{title}</div>
          <div style="font-size:11px;color:#90949C;margin-top:4px">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
