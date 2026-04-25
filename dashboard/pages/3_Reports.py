import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dashboard.auth import check_login, login_page
from dashboard import data, charts, styles
import pandas as pd
import plotly.graph_objects as go

if not check_login():
    login_page()
    st.stop()

st.set_page_config(page_title="Reports", page_icon="📈", layout="wide")
settings    = data.get_all_settings()
brand_color = settings.get("brand_color", "#1877F2")
brand_name  = settings.get("brand_name",  "Meta Ads")
styles.inject(brand_color=brand_color)

styles.hero("Performance Reports", "Date-range analytics — export to PDF, Excel, CSV or JSON")

# ── Filters ───────────────────────────────────────────────────
f1, f2, f3 = st.columns([3, 2, 2])
with f1:
    camps_df = data.get_campaigns()
    opts = {"All Campaigns": None}
    if not camps_df.empty:
        for _, r in camps_df.iterrows():
            opts[r["name"]] = str(r["id"])
    sel   = st.selectbox("Campaign", list(opts.keys()))
    cid   = opts[sel]
with f2:
    preset = st.selectbox("Date Range", ["All Time","Last 7 Days","Last 14 Days","Last 30 Days","Last 90 Days"])
with f3:
    export = st.selectbox("Export Format", ["None","PDF","Excel","CSV","JSON"])

# ── Filter data ───────────────────────────────────────────────
time_df = data.get_spend_over_time(campaign_id=cid)
if preset != "All Time" and not time_df.empty:
    dm = {"Last 7 Days":7,"Last 14 Days":14,"Last 30 Days":30,"Last 90 Days":90}
    time_df["date"] = pd.to_datetime(time_df["date"])
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=dm[preset])
    time_df = time_df[time_df["date"] >= cutoff]

if time_df.empty:
    st.info("No data. Run `python main.py campaign list --sync` to sync from Meta API.")
    st.stop()

total_spend  = time_df["spend"].sum()
total_clicks = int(time_df["clicks"].sum())
total_impr   = int(time_df["impressions"].sum()) if "impressions" in time_df.columns else 0
avg_roas     = float(time_df["roas"].mean())     if "roas" in time_df.columns else 0
avg_ctr      = float(time_df["ctr"].mean())      if "ctr"  in time_df.columns else 0
days_n       = time_df["date"].nunique()          if "date" in time_df.columns else len(time_df)
avg_daily    = total_spend / days_n              if days_n else 0

styles.kpi_grid([
    ("&#x1F4B8;","Total Spend",     f"&#8377;{total_spend:,.2f}",  preset,              brand_color),
    ("&#x1F4C5;","Avg Daily Spend", f"&#8377;{avg_daily:,.2f}",    f"{days_n} days",    "#E65C00"),
    ("&#x1F4A5;","Total Clicks",    f"{total_clicks:,}",           "Period",            "#2E7D32"),
    ("&#x1F4E3;","Impressions",     f"{total_impr:,}",             "Period",            "#9C27B0"),
    ("&#x1F4B9;","Avg ROAS",        f"{avg_roas:.2f}",             f"Target {settings.get('target_roas',3.0)}x","#00BCD4"),
    ("&#x1F4CA;","Avg CTR",         f"{avg_ctr:.2f}%",             "Target 1.5%",       "#FF5722"),
])

# ── Charts ────────────────────────────────────────────────────
styles.sec("📊","Spend & ROAS")
c1,c2 = st.columns(2)
with c1: st.plotly_chart(charts.spend_chart(time_df), width="stretch")
with c2: st.plotly_chart(charts.roas_chart(time_df),  width="stretch")

styles.sec("🖱️","CTR & Clicks")
c3,c4 = st.columns(2)
with c3: st.plotly_chart(charts.ctr_chart(time_df), width="stretch")
with c4:
    fig = go.Figure(go.Bar(x=time_df["date"], y=time_df["clicks"],
                           marker_color="#E65C00", opacity=0.85))
    fig.update_layout(title="Daily Clicks", plot_bgcolor="white", paper_bgcolor="white",
                      font=dict(size=12), margin=dict(l=40,r=20,t=40,b=40), height=320)
    fig.update_xaxes(showgrid=False); fig.update_yaxes(showgrid=True, gridcolor="#E9EBEE")
    st.plotly_chart(fig, width="stretch")

if total_impr > 0:
    styles.sec("👁️","Impressions")
    fig2 = go.Figure(go.Scatter(x=time_df["date"], y=time_df["impressions"],
                                mode="lines+markers", line=dict(color="#9C27B0",width=2),
                                fill="tozeroy", fillcolor="rgba(156,39,176,0.08)"))
    fig2.update_layout(title="Daily Impressions", plot_bgcolor="white", paper_bgcolor="white",
                       font=dict(size=12), margin=dict(l=40,r=20,t=40,b=40), height=240)
    fig2.update_xaxes(showgrid=False); fig2.update_yaxes(showgrid=True, gridcolor="#E9EBEE")
    st.plotly_chart(fig2, width="stretch")

# ── Table ─────────────────────────────────────────────────────
styles.sec("📋","Daily Breakdown")
disp = time_df.copy()
disp["spend"] = disp["spend"].apply(lambda x: f"₹{x:,.2f}")
if "roas" in disp.columns: disp["roas"] = disp["roas"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
if "ctr"  in disp.columns: disp["ctr"]  = disp["ctr"].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
st.dataframe(disp, width="stretch", hide_index=True)

# ── Export ────────────────────────────────────────────────────
if export == "PDF":
    with st.spinner("Generating PDF..."):
        try:
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from reporting.pdf_exporter import generate_report
            totals = data.get_account_totals()
            perf   = data.get_campaign_performance()

            def _parse_hex(h):
                h = h.lstrip("#")
                return (int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))

            pdf_bytes = generate_report(
                totals=totals, perf_df=perf, time_df=time_df,
                brand_name=brand_name,
                brand_color=_parse_hex(brand_color),
            )
            st.download_button("⬇️ Download PDF", data=pdf_bytes,
                               file_name="meta_ads_report.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"PDF error: {e}")

elif export == "Excel":
    with st.spinner("Generating Excel..."):
        try:
            from reporting.excel_exporter import generate_excel
            totals    = data.get_account_totals()
            perf      = data.get_campaign_performance()
            alerts_df = data.get_alerts(limit=200)
            xlsx = generate_excel(totals=totals, perf_df=perf, time_df=time_df,
                                  alerts_df=alerts_df, brand_name=brand_name)
            st.download_button("⬇️ Download Excel", data=xlsx,
                               file_name="meta_ads_report.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e:
            st.error(f"Excel error: {e}")

elif export == "CSV":
    st.download_button("⬇️ Download CSV", data=time_df.to_csv(index=False),
                       file_name="report.csv", mime="text/csv")
elif export == "JSON":
    st.download_button("⬇️ Download JSON",
                       data=time_df.to_json(orient="records", date_format="iso"),
                       file_name="report.json", mime="application/json")
