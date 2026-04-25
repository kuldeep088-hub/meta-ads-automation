from database import db
from utils.logger import get_logger

log = get_logger("reporting.collector")


def collect_campaign_report(campaign_id: str, date_range: str = "last_7d") -> dict:
    log.info(f"Collecting report for campaign {campaign_id}  -  {date_range}")

    campaign_data = db.get_campaign(campaign_id)
    if not campaign_data:
        # Try to fetch from API
        try:
            from api.client import init_api
            from facebook_business.adobjects.campaign import Campaign as FBCampaign
            init_api()
            fb_campaign = FBCampaign(campaign_id).api_get(
                fields=["id", "name", "status", "objective", "daily_budget"]
            )
            campaign_data = dict(fb_campaign)
        except Exception as e:
            log.error(f"Could not fetch campaign {campaign_id}: {e}")
            campaign_data = {"id": campaign_id, "name": "Unknown", "status": "UNKNOWN"}

    from api.insights import get_campaign_insights, get_adset_insights, get_ad_insights
    campaign_insights = get_campaign_insights(campaign_id, date_range)
    adset_insights = get_adset_insights(campaign_id, date_range)
    ad_insights = get_ad_insights(campaign_id, date_range)

    # Save to DB
    for row in campaign_insights:
        db.save_insights("campaign", campaign_id, row)
    for row in adset_insights:
        entity_id = row.get("adset_id", campaign_id)
        db.save_insights("adset", entity_id, row)

    # Aggregate campaign totals
    totals = _aggregate(campaign_insights)

    return {
        "campaign": campaign_data,
        "date_range": date_range,
        "totals": totals,
        "adset_breakdown": adset_insights,
        "ad_breakdown": ad_insights,
        "daily_rows": campaign_insights,
    }


def collect_account_report(date_range: str = "last_30d") -> dict:
    log.info(f"Collecting account report  -  {date_range}")
    from api.insights import get_account_insights
    rows = get_account_insights(date_range)

    # Group by campaign
    campaigns: dict = {}
    for row in rows:
        cid = row.get("campaign_id", "unknown")
        if cid not in campaigns:
            campaigns[cid] = {
                "campaign_id": cid,
                "campaign_name": row.get("campaign_name", "Unknown"),
                "rows": [],
            }
        campaigns[cid]["rows"].append(row)

    summary = []
    for cid, data in campaigns.items():
        totals = _aggregate(data["rows"])
        summary.append({
            "campaign_id": cid,
            "campaign_name": data["campaign_name"],
            **totals,
        })

    summary.sort(key=lambda x: x.get("spend", 0), reverse=True)
    return {
        "date_range": date_range,
        "campaigns": summary,
        "account_totals": _aggregate(rows),
    }


def _aggregate(rows: list) -> dict:
    if not rows:
        return {k: 0.0 for k in
                ["impressions", "reach", "clicks", "spend", "ctr", "cpc",
                 "cpm", "roas", "frequency", "leads", "purchases",
                 "cost_per_lead", "cost_per_purchase"]}

    total_impressions = sum(r.get("impressions", 0) for r in rows)
    total_clicks = sum(r.get("clicks", 0) for r in rows)
    total_spend = sum(r.get("spend", 0) for r in rows)
    total_leads = sum(r.get("leads", 0) for r in rows)
    total_purchases = sum(r.get("purchases", 0) for r in rows)

    return {
        "impressions":      total_impressions,
        "reach":            sum(r.get("reach", 0) for r in rows),
        "clicks":           total_clicks,
        "spend":            round(total_spend, 2),
        "ctr":              round((total_clicks / total_impressions * 100) if total_impressions else 0, 2),
        "cpc":              round(total_spend / total_clicks if total_clicks else 0, 2),
        "cpm":              round(total_spend / total_impressions * 1000 if total_impressions else 0, 2),
        "roas":             round(sum(r.get("roas", 0) for r in rows) / len(rows), 2),
        "frequency":        round(sum(r.get("frequency", 0) for r in rows) / len(rows), 2),
        "leads":            total_leads,
        "purchases":        total_purchases,
        "cost_per_lead":    round(total_spend / total_leads if total_leads else 0, 2),
        "cost_per_purchase": round(total_spend / total_purchases if total_purchases else 0, 2),
    }
