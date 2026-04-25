import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

BLUE   = "#1877F2"
GREEN  = "#2E7D32"
RED    = "#C62828"
ORANGE = "#E65C00"
GRAY   = "#606770"
BG     = "#F0F2F5"

# Shared layout defaults
_LAYOUT = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(family="Inter, sans-serif", size=12, color="#1C1E21"),
    margin=dict(l=44, r=16, t=44, b=40),
    height=320,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
_XGRID = dict(showgrid=False, showline=False, tickfont=dict(size=11))
_YGRID = dict(showgrid=True, gridcolor="#EAEBEE", zeroline=False, tickfont=dict(size=11))


def spend_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty or "date" not in df.columns:
        return _empty("No spend data available")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["date"], y=df["spend"],
        name="Daily Spend",
        marker=dict(color=BLUE, opacity=0.88, line=dict(width=0)),
    ))
    fig.update_layout(**_LAYOUT, title=dict(text="Daily Spend", font=dict(size=13, color="#1C1E21")))
    fig.update_xaxes(**_XGRID, title_text="")
    fig.update_yaxes(**_YGRID, title_text="Spend (₹)")
    return fig


def roas_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty or "date" not in df.columns:
        return _empty("No ROAS data available")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["roas"],
        mode="lines+markers", name="ROAS",
        line=dict(color=GREEN, width=2.5),
        marker=dict(size=5, color=GREEN),
        fill="tozeroy", fillcolor="rgba(46,125,50,0.08)",
    ))
    fig.add_hline(y=1.5, line_dash="dot", line_color=ORANGE, line_width=1.5,
                  annotation_text="Min 1.5x", annotation_font_size=10,
                  annotation_position="top right")
    fig.add_hline(y=3.0, line_dash="dot", line_color=GREEN, line_width=1.5,
                  annotation_text="Scale 3.0x", annotation_font_size=10,
                  annotation_position="top right")
    fig.update_layout(**_LAYOUT, title=dict(text="ROAS Over Time", font=dict(size=13, color="#1C1E21")))
    fig.update_xaxes(**_XGRID, title_text="")
    fig.update_yaxes(**_YGRID, title_text="ROAS")
    return fig


def ctr_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty or "date" not in df.columns:
        return _empty("No CTR data available")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["ctr"],
        mode="lines+markers", name="CTR %",
        line=dict(color=BLUE, width=2.5),
        marker=dict(size=5, color=BLUE),
        fill="tozeroy", fillcolor="rgba(24,119,242,0.07)",
    ))
    fig.add_hline(y=0.5, line_dash="dot", line_color=RED, line_width=1.5,
                  annotation_text="Min 0.5%", annotation_font_size=10,
                  annotation_position="top right")
    fig.add_hline(y=1.5, line_dash="dot", line_color=GREEN, line_width=1.5,
                  annotation_text="Good 1.5%", annotation_font_size=10,
                  annotation_position="top right")
    fig.update_layout(**_LAYOUT, title=dict(text="CTR Over Time", font=dict(size=13, color="#1C1E21")))
    fig.update_xaxes(**_XGRID, title_text="")
    fig.update_yaxes(**_YGRID, title_text="CTR (%)")
    return fig


def campaign_status_pie(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No campaign data")
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    colors = {"ACTIVE": GREEN, "PAUSED": ORANGE, "DELETED": RED, "ARCHIVED": GRAY}
    color_seq = [colors.get(s, BLUE) for s in status_counts["status"]]
    fig = px.pie(
        status_counts, names="status", values="count",
        color_discrete_sequence=color_seq, hole=0.48,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label",
                      textfont_size=11, pull=[0.03]*len(status_counts))
    layout = dict(**_LAYOUT)
    layout["margin"] = dict(l=16, r=16, t=44, b=16)
    fig.update_layout(**layout, title=dict(text="Campaigns by Status", font=dict(size=13, color="#1C1E21")))
    return fig


def top_campaigns_bar(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No campaign data")
    top = df.nlargest(8, "total_spend")
    colors = [GREEN if r >= 3.0 else ORANGE if r >= 1.5 else RED
              for r in top["avg_roas"]]
    fig = go.Figure(go.Bar(
        x=top["total_spend"],
        y=top["name"].str[:26],
        orientation="h",
        marker=dict(color=colors, opacity=0.9, line=dict(width=0)),
        text=top["total_spend"].apply(lambda x: f"₹{x:,.0f}"),
        textposition="outside",
        textfont=dict(size=10),
    ))
    layout = dict(**_LAYOUT)
    layout["margin"] = dict(l=8, r=60, t=44, b=40)
    fig.update_layout(**layout,
                      title=dict(text="Top Campaigns by Spend", font=dict(size=13, color="#1C1E21")),
                      xaxis_title="", yaxis=dict(autorange="reversed"))
    fig.update_xaxes(showgrid=True, gridcolor="#EAEBEE", tickfont=dict(size=11), title_text="")
    fig.update_yaxes(showgrid=False, tickfont=dict(size=11))
    return fig


def alerts_by_type(counts: dict) -> go.Figure:
    if not counts:
        return _empty("No alerts triggered yet")
    color_map = {
        "spend_spike": RED, "budget_depleted": RED,
        "low_roas": ORANGE, "high_cpa": ORANGE,
        "low_ctr": BLUE, "frequency_fatigue": GRAY,
    }
    labels = list(counts.keys())
    values = list(counts.values())
    bar_colors = [color_map.get(l, BLUE) for l in labels]
    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker=dict(color=bar_colors, opacity=0.9, line=dict(width=0)),
        text=values, textposition="outside", textfont=dict(size=11),
    ))
    layout = dict(**_LAYOUT)
    layout["height"] = 300
    layout["margin"] = dict(l=20, r=20, t=44, b=56)
    fig.update_layout(**layout,
                      title=dict(text="Alerts by Type", font=dict(size=13, color="#1C1E21")),
                      xaxis_tickangle=-28)
    fig.update_yaxes(**_YGRID)
    fig.update_xaxes(**_XGRID, tickfont=dict(size=10))
    return fig


def optimization_actions_pie(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("No optimization actions yet")
    counts = df["action"].value_counts().reset_index()
    counts.columns = ["action", "count"]
    color_map = {
        "budget_increase": GREEN, "budget_decrease": ORANGE,
        "pause": RED, "alert": BLUE, "no_action": GRAY,
    }
    colors = [color_map.get(a, BLUE) for a in counts["action"]]
    fig = px.pie(
        counts, names="action", values="count",
        color_discrete_sequence=colors, hole=0.45,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label",
                      textfont_size=10, pull=[0.03]*len(counts))
    layout = dict(**_LAYOUT)
    layout["height"] = 300
    layout["margin"] = dict(l=16, r=16, t=44, b=16)
    fig.update_layout(**layout, title=dict(text="Optimization Actions", font=dict(size=13, color="#1C1E21")))
    return fig


def _empty(msg: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=msg, xref="paper", yref="paper",
                       x=0.5, y=0.5, showarrow=False,
                       font=dict(size=13, color=GRAY))
    fig.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        height=320, margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig
