import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dashboard.auth import check_login, login_page
from dashboard import data, charts, styles
from dashboard.health import campaign_health_score, score_badge_html, score_color

if not check_login():
    login_page()
    st.stop()

st.set_page_config(page_title="Campaigns", page_icon="📢", layout="wide")
settings    = data.get_all_settings()
brand_color = settings.get("brand_color", "#1877F2")
styles.inject(brand_color=brand_color)

styles.hero("Campaigns", "All campaigns synced from your Meta Ads account — with live health scores")

# ── Filter + KPIs ─────────────────────────────────────────────
f1, f2 = st.columns([2, 6])
with f1:
    status_filter = st.selectbox("Status", ["All","ACTIVE","PAUSED","DELETED","ARCHIVED"])

perf_df = data.get_campaign_performance()
if perf_df.empty:
    st.info("No campaigns. Run: `python main.py campaign list --sync`")
    st.stop()

filtered = perf_df if status_filter == "All" else perf_df[perf_df["status"] == status_filter]

styles.kpi_grid([
    ("&#x1F4E2;","Campaigns",    str(len(filtered)),                         status_filter,  brand_color),
    ("&#x1F4B8;","Total Spend",  f"&#8377;{filtered['total_spend'].sum():,.0f}", "Period",   "#E65C00"),
    ("&#x1F4A5;","Total Clicks", f"{int(filtered['clicks'].sum()):,}",       "Period",       "#2E7D32"),
    ("&#x1F3AF;","Total Leads",  f"{int(filtered['leads'].sum()):,}",        "Period",       "#9C27B0"),
])

if filtered.empty:
    st.warning(f"No campaigns with status '{status_filter}'.")
    st.stop()

# ── Health Score Summary ──────────────────────────────────────
styles.sec("🏆", "Health Score Summary")
filtered = filtered.copy()
filtered["_health"] = filtered.apply(campaign_health_score, axis=1)

excellent = len(filtered[filtered["_health"] >= 70])
good      = len(filtered[(filtered["_health"] >= 50) & (filtered["_health"] < 70)])
fair      = len(filtered[(filtered["_health"] >= 30) & (filtered["_health"] < 50)])
poor      = len(filtered[filtered["_health"] < 30])
avg_score = int(filtered["_health"].mean()) if not filtered.empty else 0

h1,h2,h3,h4,h5 = st.columns(5)
h1.metric("Avg Health Score", f"{avg_score}/100")
h2.metric("🟢 Excellent (70+)", excellent)
h3.metric("🔵 Good (50-69)",    good)
h4.metric("🟡 Fair (30-49)",    fair)
h5.metric("🔴 Poor (<30)",      poor)

# ── Campaign Cards ────────────────────────────────────────────
styles.sec("📋", "Campaign Details")
STATUS_ICON = {"ACTIVE":"🟢","PAUSED":"🟡","DELETED":"🔴","ARCHIVED":"⚫"}

for idx, (_, row) in enumerate(filtered.sort_values("_health", ascending=False).iterrows()):
    status  = str(row.get("status",""))
    icon    = STATUS_ICON.get(status,"⚪")
    score   = int(row["_health"])
    s_color = score_color(score)
    spend   = row["total_spend"]
    name    = row["name"]
    roas    = float(row.get("avg_roas",0))
    ctr     = float(row.get("avg_ctr",0))
    leads   = int(row.get("leads",0))
    budget  = row.get("daily_budget",0) or 0
    objective = str(row.get("objective","N/A")).replace("OUTCOME_","")

    label = f"{icon}  {name}   |  Health: {score}/100  |  ₹{spend:,.0f} spent"
    with st.expander(label, expanded=(idx == 0)):

        # Score badge + metrics in one row
        badge_col, *metric_cols = st.columns([2,1,1,1,1,1,1])
        with badge_col:
            st.markdown(f"""
            <div style="background:#fff;border-radius:12px;padding:14px 16px;box-shadow:0 1px 8px rgba(0,0,0,0.07);text-align:center;border-top:4px solid {s_color}">
              <div style="font-size:11px;font-weight:800;color:#9EA3A9;text-transform:uppercase;letter-spacing:.8px">Health Score</div>
              <div style="font-size:36px;font-weight:900;color:{s_color};line-height:1.1;margin:6px 0 2px">{score}</div>
              <div style="font-size:11px;color:{s_color};font-weight:700">out of 100</div>
              <div style="background:#F0F2F5;border-radius:8px;overflow:hidden;height:6px;margin-top:8px">
                <div style="width:{score}%;height:100%;background:{s_color};border-radius:8px"></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        for col, (lbl, val) in zip(metric_cols, [
            ("Status",       status),
            ("Objective",    objective[:10]),
            ("Spend",        f"₹{spend:,.0f}"),
            ("Daily Budget", f"₹{budget/100:,.0f}" if budget else "N/A"),
            ("ROAS",         f"{roas:.2f}x"),
            ("CTR",          f"{ctr:.2f}%"),
        ]):
            col.metric(lbl, val)

        # Progress bars
        roas_target = float(settings.get("target_roas", 3.0))
        ctr_target  = 1.5
        roas_pct = min(roas / roas_target * 100, 100) if roas_target else 0
        ctr_pct  = min(ctr  / ctr_target  * 100, 100) if ctr_target  else 0
        rc = "#2E7D32" if roas_pct>=100 else "#E65C00" if roas_pct>=50 else "#C62828"
        cc = "#2E7D32" if ctr_pct >=100 else "#E65C00" if ctr_pct >=50 else "#C62828"

        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:12px 0 4px">
          <div>
            <div style="font-size:10px;font-weight:800;color:#9EA3A9;text-transform:uppercase;letter-spacing:.8px;margin-bottom:4px">ROAS vs Target ({roas_target}x)</div>
            <div style="background:#F0F2F5;border-radius:8px;overflow:hidden;height:8px">
              <div style="width:{roas_pct:.0f}%;height:100%;background:{rc};border-radius:8px;transition:width 1s ease"></div>
            </div>
            <div style="font-size:10px;color:{rc};font-weight:700;margin-top:3px">{roas:.2f}x ({roas_pct:.0f}%)</div>
          </div>
          <div>
            <div style="font-size:10px;font-weight:800;color:#9EA3A9;text-transform:uppercase;letter-spacing:.8px;margin-bottom:4px">CTR vs Target (1.5%)</div>
            <div style="background:#F0F2F5;border-radius:8px;overflow:hidden;height:8px">
              <div style="width:{ctr_pct:.0f}%;height:100%;background:{cc};border-radius:8px;transition:width 1s ease"></div>
            </div>
            <div style="font-size:10px;color:{cc};font-weight:700;margin-top:3px">{ctr:.2f}% ({ctr_pct:.0f}%)</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # 3 charts
        time_df = data.get_spend_over_time(campaign_id=str(row["id"]))
        if not time_df.empty and time_df["spend"].sum() > 0:
            ch1,ch2,ch3 = st.columns(3)
            with ch1: st.plotly_chart(charts.spend_chart(time_df), width="stretch")
            with ch2: st.plotly_chart(charts.ctr_chart(time_df),   width="stretch")
            with ch3: st.plotly_chart(charts.roas_chart(time_df),  width="stretch")

        # Ad Sets
        adsets_df = data.get_adsets(campaign_id=str(row["id"]))
        if not adsets_df.empty:
            styles.sec("📦","Ad Sets")
            cols = ["id","name","status","daily_budget","optimization_goal"]
            disp = adsets_df[[c for c in cols if c in adsets_df.columns]].copy()
            if "daily_budget" in disp.columns:
                disp["daily_budget"] = disp["daily_budget"].apply(lambda x: f"₹{x/100:,.0f}" if x else "N/A")
            st.dataframe(disp, width="stretch", hide_index=True)
