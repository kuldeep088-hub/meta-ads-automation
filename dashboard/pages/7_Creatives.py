import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dashboard.auth import check_login, login_page
from dashboard import data, styles
import plotly.graph_objects as go
import plotly.express as px

if not check_login():
    login_page()
    st.stop()

st.set_page_config(page_title="Creatives", page_icon="🖼️", layout="wide")
settings    = data.get_all_settings()
brand_color = settings.get("brand_color", "#1877F2")
brand_name  = settings.get("brand_name", "Meta Ads")
styles.inject(brand_color=brand_color)

styles.hero(
    "Creative Insights",
    "Side-by-side ad performance — identify winners and underperformers at a glance",
    badges=["🏆 Top Performers","⚠️ Low CTR","💸 High Spend"]
)

# ── Load ad-level data ────────────────────────────────────────
ads_df = data.get_ad_performance()

if ads_df.empty:
    st.info("No ad-level data. Run `python main.py report --format table` to sync ad insights, or create ads via `python main.py ad create`.")
    st.stop()

# Filter: only ads that have any spend
active_ads = ads_df[ads_df["total_spend"] > 0].copy()

if active_ads.empty:
    st.warning("Ads exist in the database but none have spend data yet. Sync insights to populate.")
    # Still show the full table
    styles.sec("📋","All Ads")
    st.dataframe(ads_df[["id","name","status","campaign_id","adset_id"]], width="stretch", hide_index=True)
    st.stop()

# ── KPI Summary ───────────────────────────────────────────────
styles.kpi_grid([
    ("🖼️","Total Ads",      str(len(ads_df)),                            "In database",      brand_color),
    ("📊","With Spend",     str(len(active_ads)),                        "Active",           "#E65C00"),
    ("🏆","Best CTR",       f"{active_ads['avg_ctr'].max():.2f}%",       "Top ad",           "#2E7D32"),
    ("💸","Highest Spend",  f"₹{active_ads['total_spend'].max():,.0f}",  "Single ad",        "#9C27B0"),
    ("🎯","Best ROAS",      f"{active_ads['avg_roas'].max():.2f}x",      "Top ad",           "#00BCD4"),
    ("👆","Total Clicks",   f"{int(active_ads['clicks'].sum()):,}",      "All ads",          "#FF5722"),
])

# ── Top Performers vs Underperformers ─────────────────────────
styles.sec("🏆","Top vs Bottom Performers")

top3    = active_ads.nlargest(3, "avg_ctr")
bottom3 = active_ads.nsmallest(3, "avg_ctr")

col_top, col_bot = st.columns(2)

def perf_card(col, rows, title, top=True):
    with col:
        st.markdown(f"""
        <div style="background:#fff;border-radius:14px;padding:16px 18px;
                    box-shadow:0 2px 12px rgba(0,0,0,0.07);
                    border-top:4px solid {'#2E7D32' if top else '#C62828'}">
          <div style="font-size:13px;font-weight:800;color:#1C1E21;margin-bottom:12px">
            {'🏆' if top else '⚠️'} {title}
          </div>
        """, unsafe_allow_html=True)
        for _, r in rows.iterrows():
            ctr   = float(r.get("avg_ctr", 0))
            roas  = float(r.get("avg_roas", 0))
            spend = float(r.get("total_spend", 0))
            name  = str(r.get("name",""))[:30]
            color = "#2E7D32" if top else "#C62828"
            st.markdown(f"""
            <div style="padding:10px 12px;border-radius:10px;margin:5px 0;
                        background:#F8F9FA;border-left:3px solid {color}">
              <div style="font-size:13px;font-weight:700;color:#1C1E21">{name}</div>
              <div style="display:flex;gap:16px;margin-top:5px;font-size:12px;color:#606770">
                <span>CTR <b style="color:{color}">{ctr:.2f}%</b></span>
                <span>ROAS <b>{roas:.2f}x</b></span>
                <span>Spend <b>₹{spend:,.0f}</b></span>
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

perf_card(col_top, top3,    "Top 3 by CTR",    top=True)
perf_card(col_bot, bottom3, "Bottom 3 by CTR", top=False)

# ── CTR Comparison Chart ──────────────────────────────────────
styles.sec("📊","CTR & ROAS Comparison")
ch1, ch2 = st.columns(2)

with ch1:
    top10 = active_ads.nlargest(10, "avg_ctr")
    colors = ["#2E7D32" if c >= 1.5 else "#E65C00" if c >= 0.5 else "#C62828" for c in top10["avg_ctr"]]
    fig = go.Figure(go.Bar(
        y=top10["name"].str[:22],
        x=top10["avg_ctr"],
        orientation="h",
        marker_color=colors,
        text=top10["avg_ctr"].apply(lambda x: f"{x:.2f}%"),
        textposition="outside",
    ))
    fig.add_vline(x=1.5, line_dash="dash", line_color="#2E7D32", annotation_text="Good (1.5%)")
    fig.add_vline(x=0.5, line_dash="dash", line_color="#C62828", annotation_text="Min (0.5%)")
    fig.update_layout(
        title="Top 10 Ads by CTR", xaxis_title="CTR (%)",
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(size=11), margin=dict(l=10,r=60,t=40,b=40),
        height=340, yaxis=dict(autorange="reversed"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#E9EBEE")
    fig.update_yaxes(showgrid=False)
    st.plotly_chart(fig, width="stretch")

with ch2:
    top10r = active_ads.nlargest(10, "avg_roas")
    rcolors = ["#2E7D32" if r >= 3.0 else "#E65C00" if r >= 1.5 else "#C62828" for r in top10r["avg_roas"]]
    fig2 = go.Figure(go.Bar(
        y=top10r["name"].str[:22],
        x=top10r["avg_roas"],
        orientation="h",
        marker_color=rcolors,
        text=top10r["avg_roas"].apply(lambda x: f"{x:.2f}x"),
        textposition="outside",
    ))
    fig2.add_vline(x=3.0, line_dash="dash", line_color="#2E7D32", annotation_text="Scale (3x)")
    fig2.add_vline(x=1.5, line_dash="dash", line_color="#E65C00", annotation_text="Min (1.5x)")
    fig2.update_layout(
        title="Top 10 Ads by ROAS", xaxis_title="ROAS",
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(size=11), margin=dict(l=10,r=60,t=40,b=40),
        height=340, yaxis=dict(autorange="reversed"),
    )
    fig2.update_xaxes(showgrid=True, gridcolor="#E9EBEE")
    fig2.update_yaxes(showgrid=False)
    st.plotly_chart(fig2, width="stretch")

# ── Spend vs CTR scatter ──────────────────────────────────────
styles.sec("🔬","Spend vs CTR — Find Hidden Winners")
fig3 = px.scatter(
    active_ads,
    x="total_spend", y="avg_ctr",
    size="clicks",
    color="avg_roas",
    color_continuous_scale="RdYlGn",
    hover_name="name",
    hover_data={"total_spend": ":.0f", "avg_ctr": ":.2f", "avg_roas": ":.2f", "clicks": True},
    labels={"total_spend":"Total Spend (₹)","avg_ctr":"Avg CTR (%)","avg_roas":"ROAS"},
    title="Spend vs CTR (bubble size = clicks, color = ROAS)",
    height=400,
)
fig3.update_layout(plot_bgcolor="white", paper_bgcolor="white", font=dict(size=12))
fig3.add_hline(y=1.5, line_dash="dash", line_color="#2E7D32", annotation_text="Good CTR")
fig3.add_hline(y=0.5, line_dash="dash", line_color="#C62828", annotation_text="Min CTR")
st.plotly_chart(fig3, width="stretch")

# ── Full table ────────────────────────────────────────────────
styles.sec("📋","All Ads Performance Table")
disp_cols = ["name","status","total_spend","avg_ctr","avg_roas","avg_cpc","clicks","leads","impressions"]
disp = active_ads[[c for c in disp_cols if c in active_ads.columns]].copy()
disp["total_spend"] = disp["total_spend"].apply(lambda x: f"₹{x:,.2f}")
disp["avg_ctr"]     = disp["avg_ctr"].apply(lambda x: f"{x:.2f}%")
disp["avg_roas"]    = disp["avg_roas"].apply(lambda x: f"{x:.2f}x")
disp["avg_cpc"]     = disp["avg_cpc"].apply(lambda x: f"₹{x:,.2f}")
st.dataframe(disp, width="stretch", hide_index=True)
st.download_button("⬇️ Download CSV", data=active_ads.to_csv(index=False),
                   file_name="creatives.csv", mime="text/csv")
