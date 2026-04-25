import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dashboard.auth import check_login, login_page
from dashboard import data, charts, styles

if not check_login():
    login_page()
    st.stop()

st.set_page_config(page_title="Alerts", page_icon="🚨", layout="wide")
settings    = data.get_all_settings()
brand_color = settings.get("brand_color", "#1877F2")
styles.inject(brand_color=brand_color)

styles.hero(
    "Alerts",
    "Triggered alerts and campaign health notifications — critical issues pulse in red",
    badges=["&#x1F534; Critical","&#x1F7E1; Warning","&#x1F535; Info"]
)

# ── Filters ───────────────────────────────────────────────────
f1, f2 = st.columns([2, 2])
with f1:
    type_filter = st.selectbox("Alert Type", [
        "All","spend_spike","budget_depleted","low_roas","high_cpa","low_ctr","frequency_fatigue"
    ])
with f2:
    limit = st.selectbox("Show last", [25, 50, 100, 200], index=0)

alerts_df = data.get_alerts(limit=limit)
counts    = data.get_alert_counts()

if alerts_df.empty:
    st.markdown('<div class="al al-ok" style="margin-top:20px"><div class="al-t" style="font-size:15px">&#x2714; All Clear</div><div class="al-m">No alerts have been triggered. All campaigns appear healthy.</div></div>', unsafe_allow_html=True)
    st.stop()

# ── Count badges ──────────────────────────────────────────────
ICONS = {"spend_spike":"🔴","budget_depleted":"🔴","low_roas":"🟡","high_cpa":"🟡","low_ctr":"🔵","frequency_fatigue":"🔵"}
if counts:
    styles.kpi_grid([
        (ICONS.get(k,"⚪"), k.replace("_"," ").title(), str(v), "alerts", "#C62828" if k in ("spend_spike","budget_depleted") else "#F9A825" if k in ("low_roas","high_cpa") else "#1877F2")
        for k, v in counts.items()
    ])

# ── Chart + Feed ─────────────────────────────────────────────
styles.sec("📊", "Distribution & Feed")
left, right = st.columns([1, 2])

with left:
    st.plotly_chart(charts.alerts_by_type(counts), width="stretch")

    # Severity breakdown
    CRITICAL = {"spend_spike","budget_depleted"}
    WARNING  = {"low_roas","high_cpa"}
    n_crit = sum(v for k,v in counts.items() if k in CRITICAL)
    n_warn = sum(v for k,v in counts.items() if k in WARNING)
    n_info = sum(v for k,v in counts.items() if k not in CRITICAL|WARNING)
    st.markdown(f"""
    <div style="display:flex;flex-direction:column;gap:10px;margin-top:8px">
      <div style="background:linear-gradient(135deg,#FFEBEE,#FFCDD2);border-radius:10px;padding:12px 16px;display:flex;justify-content:space-between;align-items:center">
        <span style="font-weight:800;color:#C62828;font-size:13px">&#x1F534; Critical</span>
        <span style="font-size:22px;font-weight:900;color:#C62828">{n_crit}</span>
      </div>
      <div style="background:linear-gradient(135deg,#FFF8E1,#FFECB3);border-radius:10px;padding:12px 16px;display:flex;justify-content:space-between;align-items:center">
        <span style="font-weight:800;color:#E65C00;font-size:13px">&#x1F7E1; Warning</span>
        <span style="font-size:22px;font-weight:900;color:#E65C00">{n_warn}</span>
      </div>
      <div style="background:linear-gradient(135deg,#E3F2FD,#BBDEFB);border-radius:10px;padding:12px 16px;display:flex;justify-content:space-between;align-items:center">
        <span style="font-weight:800;color:#1565C0;font-size:13px">&#x1F535; Info</span>
        <span style="font-size:22px;font-weight:900;color:#1565C0">{n_info}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

with right:
    disp_df = alerts_df if type_filter == "All" else alerts_df[alerts_df["alert_type"] == type_filter]
    if disp_df.empty:
        st.info(f"No '{type_filter}' alerts.")
    else:
        for i, (_, row) in enumerate(disp_df.iterrows()):
            styles.alert_card(
                row.get("alert_type",""),
                row.get("message","N/A"),
                str(row.get("created_at",""))[:16],
                row.get("campaign_id",""),
            )
            if i >= 19:
                st.caption(f"Showing 20 of {len(disp_df)}. Download CSV for full list.")
                break

# ── Full table ────────────────────────────────────────────────
styles.sec("📋", "Full Alerts Table")
st.dataframe(alerts_df, width="stretch", hide_index=True)
st.download_button("⬇️ Download CSV", data=alerts_df.to_csv(index=False), file_name="alerts.csv", mime="text/csv")
