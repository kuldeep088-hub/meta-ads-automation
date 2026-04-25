import time
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adreportrun import AdReportRun

from api.client import get_account, init_api
import config
from utils.logger import get_logger
from utils.helpers import parse_date_range

log = get_logger("api.insights")

INSIGHTS_FIELDS = [
    "impressions", "reach", "clicks", "spend",
    "ctr", "cpc", "cpm", "cpp", "frequency",
    "actions", "cost_per_action_type",
    "date_start", "date_stop",
]


def _extract_action_value(actions: list, action_type: str) -> float:
    if not actions:
        return 0.0
    for a in actions:
        if a.get("action_type") == action_type:
            return float(a.get("value", 0))
    return 0.0


def _extract_cost_per_action(cost_per_action: list, action_type: str) -> float:
    if not cost_per_action:
        return 0.0
    for a in cost_per_action:
        if a.get("action_type") == action_type:
            return float(a.get("value", 0))
    return 0.0


def _normalise(row: dict) -> dict:
    actions = row.get("actions", [])
    cost_per_action = row.get("cost_per_action_type", [])

    purchases = _extract_action_value(actions, "purchase")
    leads = _extract_action_value(actions, "lead")
    spend = float(row.get("spend", 0))

    roas = 0.0
    purchase_value_actions = [a for a in actions if a.get("action_type") == "offsite_conversion.fb_pixel_purchase"]
    if purchase_value_actions:
        revenue = float(purchase_value_actions[0].get("value", 0))
        roas = revenue / spend if spend > 0 else 0.0

    return {
        "date_start":           row.get("date_start", ""),
        "date_stop":            row.get("date_stop", ""),
        "impressions":          int(row.get("impressions", 0)),
        "reach":                int(row.get("reach", 0)),
        "clicks":               int(row.get("clicks", 0)),
        "spend":                spend,
        "ctr":                  float(row.get("ctr", 0)),
        "cpc":                  float(row.get("cpc", 0)),
        "cpm":                  float(row.get("cpm", 0)),
        "cpp":                  float(row.get("cpp", 0)),
        "frequency":            float(row.get("frequency", 0)),
        "roas":                 roas,
        "leads":                int(leads),
        "purchases":            int(purchases),
        "cost_per_lead":        _extract_cost_per_action(cost_per_action, "lead"),
        "cost_per_purchase":    _extract_cost_per_action(cost_per_action, "purchase"),
    }


def get_campaign_insights(campaign_id: str, date_range: str = "last_7d") -> list:
    init_api()
    params = {"level": "campaign", **parse_date_range(date_range)}
    try:
        campaign = Campaign(campaign_id)
        insights = campaign.get_insights(fields=INSIGHTS_FIELDS, params=params)
        return [_normalise(dict(i)) for i in insights]
    except Exception as e:
        log.error(f"Failed to fetch campaign insights for {campaign_id}: {e}")
        return []


def get_adset_insights(campaign_id: str, date_range: str = "last_7d") -> list:
    init_api()
    params = {"level": "adset", **parse_date_range(date_range)}
    try:
        campaign = Campaign(campaign_id)
        insights = campaign.get_insights(fields=INSIGHTS_FIELDS + ["adset_id", "adset_name"], params=params)
        return [_normalise(dict(i)) for i in insights]
    except Exception as e:
        log.error(f"Failed to fetch adset insights for campaign {campaign_id}: {e}")
        return []


def get_ad_insights(campaign_id: str, date_range: str = "last_7d") -> list:
    init_api()
    params = {"level": "ad", **parse_date_range(date_range)}
    try:
        campaign = Campaign(campaign_id)
        insights = campaign.get_insights(fields=INSIGHTS_FIELDS + ["ad_id", "ad_name"], params=params)
        return [_normalise(dict(i)) for i in insights]
    except Exception as e:
        log.error(f"Failed to fetch ad insights for campaign {campaign_id}: {e}")
        return []


def get_account_insights(date_range: str = "last_30d") -> list:
    init_api()
    params = {"level": "campaign", **parse_date_range(date_range)}
    try:
        account = get_account()
        insights = account.get_insights(
            fields=INSIGHTS_FIELDS + ["campaign_id", "campaign_name"], params=params
        )
        return [_normalise(dict(i)) for i in insights]
    except Exception as e:
        log.error(f"Failed to fetch account insights: {e}")
        return []


def get_adset_insights_direct(adset_id: str, date_range: str = "last_7d") -> list:
    """Get insights for a single adset directly."""
    init_api()
    params = parse_date_range(date_range)
    try:
        adset = AdSet(adset_id)
        insights = adset.get_insights(fields=INSIGHTS_FIELDS, params=params)
        return [_normalise(dict(i)) for i in insights]
    except Exception as e:
        log.error(f"Failed to fetch insights for adset {adset_id}: {e}")
        return []
