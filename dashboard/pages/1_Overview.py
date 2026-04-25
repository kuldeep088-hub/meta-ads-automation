import streamlit as st
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dashboard.auth import check_login, login_page
from dashboard import data, charts, styles
from dashboard.anomaly import detect_anomalies
import pandas as pd

if not check_login():
    login_page()
    st.stop()

st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")

settings    = data.get_all_settings()
brand_color = settings.get("brand_color", "#1877F2")
brand_name  = settings.get("brand_name",  "Meta Ads")
logo_path   = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "logo.png")
styles.inject(brand_color=brand_color)

# ── Top bar: date filter + sync ───────────────────────────────
top1, top2, top3 = st.columns([3, 3, 1])
with top1:
    date_opt = st.selectbox(
        "Date Range",
        ["All Time", "Last 7 Days", "Last 14 Days", "Last 30 Days", "Last 90 Days"],
        key="ov_date"
    )
with top2:
    st.markdown("")   # spacer — aligns with date filter label
with top3:
    if st.button("🔄 Sync Now", use_container_width=True, type="primary"):
        with st.spinner("Syncing from Meta API..."):
            try:
                root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                result = subprocess.run(
                    [sys.executable, "main.py", "campaign", "list", "--sync"],
                    capture_output=True, text=True, cwd=root, timeout=60
                )
                if result.returncode == 0:
                    st.success("Sync complete!")
                else:
                    st.warning(f"Sync finished with warnings. {result.stderr[:120]}")
            except subprocess.TimeoutExpired:
                st.error("Sync timed out after 60s.")
            except Exception as e:
                st.error(f"Sync error: {e}")
        st.rerun()

totals = data.get_account_totals()
stats  = data.get_stats()

styles.hero(
    f"{brand_name} — Account Overview",
    "Real-time snapshot of your Meta Ads performance",
    badges=[
        f"&#x1F7E2; {stats.get('active_campaigns',0)} Active",
        f"&#x1F4B0; &#8377;{totals.get('total_spend',0):,.0f} Spent",
        f"&#x1F3AF; {totals.get('total_leads',0):,} Leads",
    ],
    logo_path=logo_path if os.path.exists(logo_path) else None,
)

# ── KPIs ──────────────────────────────────────────────────────
styles.kpi_grid([
    ("&#x1F4B8;","Total Spend",      f"&#8377;{totals.get('total_spend',0):,.2f}", "All time",         brand_color),
    ("&#x1F4A5;","Total Clicks",     f"{totals.get('total_clicks',0):,}",         "All time",         "#E65C00"),
    ("&#x1F3AF;","Total Leads",      f"{totals.get('total_leads',0):,}",          "All time",         "#2E7D32"),
    ("&#x1F4CA;","Avg CTR",          f"{totals.get('avg_ctr',0):.2f}%",          "All campaigns",    "#9C27B0"),
    ("&#x1F680;","Active Campaigns", str(stats.get('active_campaigns',0)),        f"of {stats.get('campaigns',0)}","#00BCD4"),
    ("&#x1F4E3;","Impressions",      f"{totals.get('total_impressions',0):,}",    "All time",         "#FF5722"),
])

# ── Load time series (with date filter) ───────────────────────
time_df = data.get_spend_over_time()
if date_opt != "All Time" and not time_df.empty:
    dm = {"Last 7 Days":7,"Last 14 Days":14,"Last 30 Days":30,"Last 90 Days":90}
    time_df["date"] = pd.to_datetime(time_df["date"])
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=dm[date_opt])
    time_df = time_df[time_df["date"] >= cutoff]

# ── Anomaly Callout ───────────────────────────────────────────
insights = detect_anomalies(time_df)
if insights:
    styles.sec("🧠", "AI Insights")
    SEV_STYLE = {
        "positive": ("al-ok",   "✅"),
        "warning":  ("al-warn", "⚠️"),
        "critical": ("al-crit", "🚨"),
    }
    for ins in insights:
        css, icon = SEV_STYLE.get(ins["severity"], ("al-info","ℹ️"))
        st.markdown(f'<div class="al {css}" style="margin-bottom:6px"><span style="font-size:15px">{icon}</span> {ins["text"]}</div>', unsafe_allow_html=True)

# ── Goal / Target Progress ────────────────────────────────────
t_roas   = float(settings.get("target_roas",  3.0))
t_cpl    = float(settings.get("target_cpl",   25.0))
t_budget = float(settings.get("target_monthly_budget", 0) or 0)

styles.sec("🎯", "Goals & Targets")
g1, g2, g3 = st.columns(3)

with g1:
    avg_roas = float(time_df["roas"].mean()) if not time_df.empty and "roas" in time_df.columns else 0
    pct = min(avg_roas / t_roas * 100, 100) if t_roas else 0
    color = "#2E7D32" if pct >= 100 else "#E65C00" if pct >= 60 else "#C62828"
    st.markdown(f"""
    <div style="background:#fff;border-radius:14px;padding:18px 20px;box-shadow:0 2px 12px rgba(0,0,0,0.07)">
      <div style="font-size:11px;font-weight:800;color:#9EA3A9;text-transform:uppercase;letter-spacing:.8px">ROAS Target</div>
      <div style="font-size:22px;font-weight:900;color:#1C1E21;margin:6px 0 2px">{avg_roas:.2f}x <span style="font-size:13px;color:#9EA3A9">/ {t_roas:.1f}x</span></div>
      <div style="background:#F0F2F5;border-radius:8px;overflow:hidden;height:8px;margin-top:8px">
        <div style="width:{pct:.0f}%;height:100%;background:{color};border-radius:8px;transition:width 1.2s ease"></div>
      </div>
      <div style="font-size:11px;color:{color};font-weight:700;margin-top:5px">{pct:.0f}% of target</div>
    </div>
    """, unsafe_allow_html=True)

with g2:
    leads = int(totals.get("total_leads", 0))
    spend = float(totals.get("total_spend", 0))
    act_cpl = spend / leads if leads > 0 else 0
    pct2 = min(t_cpl / act_cpl * 100, 100) if act_cpl else 0
    color2 = "#2E7D32" if pct2 >= 80 else "#E65C00" if pct2 >= 50 else "#C62828"
    st.markdown(f"""
    <div style="background:#fff;border-radius:14px;padding:18px 20px;box-shadow:0 2px 12px rgba(0,0,0,0.07)">
      <div style="font-size:11px;font-weight:800;color:#9EA3A9;text-transform:uppercase;letter-spacing:.8px">Cost Per Lead</div>
      <div style="font-size:22px;font-weight:900;color:#1C1E21;margin:6px 0 2px">&#8377;{act_cpl:.0f} <span style="font-size:13px;color:#9EA3A9">/ &#8377;{t_cpl:.0f} target</span></div>
      <div style="background:#F0F2F5;border-radius:8px;overflow:hidden;height:8px;margin-top:8px">
        <div style="width:{pct2:.0f}%;height:100%;background:{color2};border-radius:8px;transition:width 1.2s ease"></div>
      </div>
      <div style="font-size:11px;color:{color2};font-weight:700;margin-top:5px">{"On target" if pct2>=80 else "Above target" if pct2>=50 else "Over budget"}</div>
    </div>
    """, unsafe_allow_html=True)

with g3:
    if t_budget > 0:
        spent = float(totals.get("total_spend", 0))
        pct3 = min(spent / t_budget * 100, 100)
        remaining = max(0, t_budget - spent)
        color3 = "#2E7D32" if pct3 <= 80 else "#E65C00" if pct3 <= 95 else "#C62828"
        st.markdown(f"""
        <div style="background:#fff;border-radius:14px;padding:18px 20px;box-shadow:0 2px 12px rgba(0,0,0,0.07)">
          <div style="font-size:11px;font-weight:800;color:#9EA3A9;text-transform:uppercase;letter-spacing:.8px">Monthly Budget</div>
          <div style="font-size:22px;font-weight:900;color:#1C1E21;margin:6px 0 2px">&#8377;{spent:,.0f} <span style="font-size:13px;color:#9EA3A9">/ &#8377;{t_budget:,.0f}</span></div>
          <div style="background:#F0F2F5;border-radius:8px;overflow:hidden;height:8px;margin-top:8px">
            <div style="width:{pct3:.0f}%;height:100%;background:{color3};border-radius:8px;transition:width 1.2s ease"></div>
          </div>
          <div style="font-size:11px;color:{color3};font-weight:700;margin-top:5px">&#8377;{remaining:,.0f} remaining ({100-pct3:.0f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#fff;border-radius:14px;padding:18px 20px;box-shadow:0 2px 12px rgba(0,0,0,0.07);display:flex;align-items:center;justify-content:center;min-height:90px">
          <div style="text-align:center;color:#9EA3A9;font-size:13px">Set monthly budget target<br>in <b>Settings</b> page</div>
        </div>
        """, unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────
styles.sec("📈", "Spend & ROAS")
c1, c2 = st.columns(2)
with c1: st.plotly_chart(charts.spend_chart(time_df), width="stretch")
with c2: st.plotly_chart(charts.roas_chart(time_df),  width="stretch")

styles.sec("📢", "Campaign Breakdown")
camp_df = data.get_campaigns()
perf_df = data.get_campaign_performance()
c3, c4 = st.columns(2)
with c3: st.plotly_chart(charts.campaign_status_pie(camp_df), width="stretch")
with c4: st.plotly_chart(charts.top_campaigns_bar(perf_df),   width="stretch")

# ── CTR + Alert feed ─────────────────────────────────────────
styles.sec("🔔", "CTR Trend & Live Alerts")
c5, c6 = st.columns([3, 2])
with c5:
    st.plotly_chart(charts.ctr_chart(time_df), width="stretch")
with c6:
    alerts_df = data.get_alerts(limit=7)
    if alerts_df.empty:
        st.markdown('<div class="al al-ok"><div class="al-t">&#x2714; All Clear</div><div class="al-m">No alerts. All campaigns healthy.</div></div>', unsafe_allow_html=True)
    else:
        for _, row in alerts_df.iterrows():
            styles.alert_card(row.get("alert_type",""), row.get("message","N/A"),
                              str(row.get("created_at",""))[:16], row.get("campaign_id",""))

# ── DB stats ──────────────────────────────────────────────────
styles.sec("🗃️", "Database Stats")
s1,s2,s3,s4,s5,s6 = st.columns(6)
s1.metric("Campaigns",  stats.get("campaigns",0))
s2.metric("Ad Sets",    stats.get("adsets",0))
s3.metric("Ads",        stats.get("ads",0))
s4.metric("Insights",   stats.get("insights",0))
s5.metric("Copy",       stats.get("generated_copy",0))
s6.metric("Opt Actions",stats.get("optimization_log",0))
