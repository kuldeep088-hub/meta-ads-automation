import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dashboard.auth import check_login, login_page
from dashboard import data, charts, styles

if not check_login():
    login_page()
    st.stop()

st.set_page_config(page_title="Optimization", page_icon="⚙️", layout="wide")
settings    = data.get_all_settings()
brand_color = settings.get("brand_color", "#1877F2")
styles.inject(brand_color=brand_color)

styles.hero(
    "Optimization Log",
    "Automated budget & bidding actions — live actions vs dry-run previews",
    badges=["&#x1F4C8; Budget Increase","&#x1F4C9; Budget Decrease","&#x23F8; Pause","&#x1F514; Alert"]
)

# ── Filters ───────────────────────────────────────────────────
f1, f2, f3 = st.columns([2, 2, 2])
with f1:
    action_filter = st.selectbox("Action", ["All","budget_increase","budget_decrease","pause","alert","no_action"])
with f2:
    dry_filter = st.selectbox("Run Type", ["All","Live only","Dry-run only"])
with f3:
    limit = st.selectbox("Show", [50, 100, 200], index=0)

log_df = data.get_optimization_log(limit=limit)

if log_df.empty:
    st.info("No optimization actions recorded. Run `python main.py optimize` to start the optimizer.")
    st.stop()

if action_filter != "All" and "action" in log_df.columns:
    log_df = log_df[log_df["action"] == action_filter]
if dry_filter == "Live only" and "dry_run" in log_df.columns:
    log_df = log_df[log_df["dry_run"] == 0]
elif dry_filter == "Dry-run only" and "dry_run" in log_df.columns:
    log_df = log_df[log_df["dry_run"] == 1]

# ── KPI row ───────────────────────────────────────────────────
if "action" in log_df.columns:
    action_counts = log_df["action"].value_counts().to_dict()
    ICONS_COL = {
        "budget_increase": ("&#x1F4C8;","#2E7D32"),
        "budget_decrease": ("&#x1F4C9;","#E65C00"),
        "pause":           ("&#x23F8;", "#C62828"),
        "alert":           ("&#x1F514;","#1877F2"),
        "no_action":       ("&#x2705;", "#606770"),
    }
    kpi_data = [
        (ICONS_COL.get(k,("⚙️","#1877F2"))[0],
         k.replace("_"," ").title(), str(v), "actions",
         ICONS_COL.get(k,("⚙️","#1877F2"))[1])
        for k, v in action_counts.items()
    ]
    # Add total + live/dry breakdown
    total  = len(log_df)
    live   = int((log_df["dry_run"]==0).sum()) if "dry_run" in log_df.columns else total
    dryrun = total - live
    kpi_data = [("&#x1F522;","Total Actions",str(total),"all time","#1877F2"),
                ("&#x26A1;","Live",str(live),"executed","#2E7D32"),
                ("&#x1F50D;","Dry-run",str(dryrun),"preview","#9C27B0")] + kpi_data
    styles.kpi_grid(kpi_data[:6])

# ── Pie + Log table ───────────────────────────────────────────
styles.sec("📊", "Action Breakdown & Log")
left, right = st.columns([1, 2])

with left:
    st.plotly_chart(charts.optimization_actions_pie(log_df), width="stretch")

    # Recent action feed
    styles.sec("🕒", "Recent Actions")
    ACTION_COLORS = {
        "budget_increase":"#2E7D32","budget_decrease":"#E65C00",
        "pause":"#C62828","alert":"#1877F2","no_action":"#606770"
    }
    ACTION_ICONS = {
        "budget_increase":"📈","budget_decrease":"📉",
        "pause":"⏸️","alert":"🔔","no_action":"✅"
    }
    recent = log_df.head(6)
    for _, r in recent.iterrows():
        act   = r.get("action","")
        color = ACTION_COLORS.get(act,"#1877F2")
        icon  = ACTION_ICONS.get(act,"⚙️")
        ts    = str(r.get("executed_at",""))[:16]
        dry   = " · Dry Run" if r.get("dry_run") else ""
        reason= str(r.get("reason",""))[:50]
        st.markdown(f"""
        <div style="padding:10px 12px;border-radius:10px;margin:5px 0;
                    background:#fff;border-left:3px solid {color};
                    box-shadow:0 1px 6px rgba(0,0,0,0.06);animation:slideLeft .3s ease">
          <div style="font-size:12px;font-weight:800;color:{color}">{icon} {act.replace('_',' ').upper()}{dry}</div>
          <div style="font-size:11px;color:#555;margin:3px 0">{reason}</div>
          <div style="font-size:10px;color:#90949C">{ts}</div>
        </div>
        """, unsafe_allow_html=True)

with right:
    display_cols = ["executed_at","entity_type","entity_id","action","old_value","new_value","reason","dry_run"]
    disp = log_df[[c for c in display_cols if c in log_df.columns]].copy()
    if "old_value" in disp.columns:
        disp["old_value"] = disp["old_value"].apply(
            lambda x: f"₹{float(x)/100:,.0f}" if x and str(x).replace(".","").isdigit() else (str(x) if x else "N/A")
        )
    if "new_value" in disp.columns:
        disp["new_value"] = disp["new_value"].apply(
            lambda x: f"₹{float(x)/100:,.0f}" if x and str(x).replace(".","").isdigit() else (str(x) if x else "N/A")
        )
    if "dry_run" in disp.columns:
        disp["dry_run"] = disp["dry_run"].apply(lambda x: "🔍 Dry Run" if x else "⚡ Live")
    st.dataframe(disp, width="stretch", hide_index=True, height=480)

st.download_button("⬇️ Download CSV", data=disp.to_csv(index=False), file_name="optimization_log.csv", mime="text/csv")
