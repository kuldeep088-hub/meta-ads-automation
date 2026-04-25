"""Plain-English anomaly detection for the Overview page."""
import pandas as pd


def detect_anomalies(time_df: pd.DataFrame) -> list[dict]:
    """
    Returns list of {type, text, severity} dicts.
    severity: 'positive' | 'warning' | 'critical'
    """
    if time_df.empty or len(time_df) < 3:
        return []

    df = time_df.copy()
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

    insights = []
    last   = df.iloc[-1]
    window = df.iloc[-8:-1]  # prior 7 days

    if window.empty:
        return []

    def pct(new, old):
        return (new - old) / old * 100 if old else 0

    # ── Spend anomaly ─────────────────────────────────────────
    avg_spend = window["spend"].mean()
    last_spend = float(last.get("spend", 0))
    if avg_spend > 0:
        chg = pct(last_spend, avg_spend)
        if chg > 60:
            insights.append({"type": "spend_spike", "severity": "critical",
                "text": f"Spend surged {chg:.0f}% above your 7-day average yesterday (₹{last_spend:,.0f} vs avg ₹{avg_spend:,.0f})."})
        elif chg < -50:
            insights.append({"type": "spend_drop", "severity": "warning",
                "text": f"Spend fell {abs(chg):.0f}% below your 7-day average — check budget caps or paused campaigns."})

    # ── ROAS anomaly ──────────────────────────────────────────
    if "roas" in df.columns:
        avg_roas  = window["roas"].mean()
        last_roas = float(last.get("roas", 0))
        if avg_roas > 0:
            if last_roas > avg_roas * 1.4:
                insights.append({"type": "roas_spike", "severity": "positive",
                    "text": f"ROAS hit {last_roas:.1f}x yesterday — {pct(last_roas,avg_roas):.0f}% above your {avg_roas:.1f}x average. Good time to scale budget."})
            elif last_roas < avg_roas * 0.65 and last_roas > 0:
                insights.append({"type": "roas_drop", "severity": "warning",
                    "text": f"ROAS dropped to {last_roas:.1f}x (average {avg_roas:.1f}x). Review targeting and creative performance."})

    # ── CTR anomaly ───────────────────────────────────────────
    if "ctr" in df.columns:
        avg_ctr  = window["ctr"].mean()
        last_ctr = float(last.get("ctr", 0))
        if avg_ctr > 0 and last_ctr < avg_ctr * 0.55 and last_ctr >= 0:
            insights.append({"type": "low_ctr", "severity": "warning",
                "text": f"CTR dropped to {last_ctr:.2f}% (average {avg_ctr:.2f}%) — creative fatigue may be building up."})
        elif avg_ctr > 0 and last_ctr > avg_ctr * 1.5:
            insights.append({"type": "high_ctr", "severity": "positive",
                "text": f"CTR jumped to {last_ctr:.2f}% yesterday, {pct(last_ctr,avg_ctr):.0f}% above average — your creatives are resonating."})

    # ── Best day in recent history ────────────────────────────
    if len(df) >= 7:
        best_day = df.nlargest(1, "spend").iloc[0]
        if "date" in best_day and str(best_day["date"])[:10] == str(last["date"])[:10]:
            insights.append({"type": "best_day", "severity": "positive",
                "text": f"Yesterday was your highest-spend day on record: ₹{float(best_day['spend']):,.0f}."})

    # ── 3-day declining trend ─────────────────────────────────
    if len(df) >= 4 and "roas" in df.columns:
        last3 = df["roas"].tail(3).tolist()
        if last3[0] > last3[1] > last3[2] and last3[0] > 0:
            insights.append({"type": "roas_trend", "severity": "warning",
                "text": f"ROAS has declined for 3 consecutive days ({last3[0]:.1f}x → {last3[1]:.1f}x → {last3[2]:.1f}x). Review ad fatigue."})

    return insights
