"""Campaign health score: 0-100 based on ROAS, CTR, CPL, activity."""


def campaign_health_score(row) -> int:
    roas  = float(row.get("avg_roas", 0) or 0)
    ctr   = float(row.get("avg_ctr",  0) or 0)
    spend = float(row.get("total_spend", 0) or 0)
    leads = float(row.get("leads", 0) or 0)

    # ROAS (40 pts)
    if   roas >= 4.0: r = 40
    elif roas >= 3.0: r = 32
    elif roas >= 2.0: r = 22
    elif roas >= 1.5: r = 14
    elif roas >= 1.0: r = 6
    else:             r = 0

    # CTR (25 pts)
    if   ctr >= 2.5: c = 25
    elif ctr >= 1.5: c = 20
    elif ctr >= 1.0: c = 14
    elif ctr >= 0.5: c = 7
    else:            c = 0

    # CPL (20 pts)
    if leads > 0 and spend > 0:
        cpl = spend / leads
        if   cpl <= 10:  lp = 20
        elif cpl <= 25:  lp = 15
        elif cpl <= 50:  lp = 8
        elif cpl <= 100: lp = 4
        else:            lp = 0
    else:
        lp = 10  # neutral when no lead data

    # Activity (15 pts)
    if   spend > 5000: a = 15
    elif spend > 1000: a = 12
    elif spend > 100:  a = 7
    elif spend > 0:    a = 3
    else:              a = 0

    return min(100, r + c + lp + a)


def score_color(score: int) -> str:
    if score >= 70: return "#2E7D32"
    if score >= 50: return "#1877F2"
    if score >= 30: return "#E65C00"
    return "#C62828"


def score_label(score: int) -> str:
    if score >= 70: return "Excellent"
    if score >= 50: return "Good"
    if score >= 30: return "Fair"
    return "Poor"


def score_badge_html(score: int) -> str:
    color = score_color(score)
    label = score_label(score)
    bg    = color + "18"
    return (
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'background:{bg};color:{color};border:1px solid {color}33;'
        f'padding:3px 11px;border-radius:20px;font-size:11px;font-weight:800">'
        f'<span style="font-size:14px">{"🟢" if score>=70 else "🔵" if score>=50 else "🟡" if score>=30 else "🔴"}</span>'
        f'{score}/100 &nbsp;{label}</span>'
    )
