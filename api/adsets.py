from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.campaign import Campaign

from api.client import get_account
from utils.logger import get_logger
from utils.helpers import usd_to_cents

log = get_logger("api.adsets")

ADSET_FIELDS = [
    "id", "name", "status", "campaign_id",
    "daily_budget", "lifetime_budget", "budget_remaining",
    "bid_strategy", "optimization_goal", "billing_event",
    "targeting", "start_time", "end_time",
    "created_time", "updated_time",
]


def list_adsets(campaign_id: str) -> list:
    campaign = Campaign(campaign_id)
    adsets = campaign.get_ad_sets(fields=ADSET_FIELDS)
    return [dict(a) for a in adsets]


def create_adset(
    campaign_id: str,
    name: str,
    daily_budget_usd: float,
    optimization_goal: str = "LINK_CLICKS",
    billing_event: str = "IMPRESSIONS",
    bid_strategy: str = "LOWEST_COST_WITHOUT_CAP",
    targeting: dict = None,
    start_time: str = None,
    end_time: str = None,
    status: str = "PAUSED",
) -> dict:
    account = get_account()
    params = {
        AdSet.Field.name: name,
        AdSet.Field.campaign_id: campaign_id,
        AdSet.Field.daily_budget: usd_to_cents(daily_budget_usd),
        AdSet.Field.optimization_goal: optimization_goal,
        AdSet.Field.billing_event: billing_event,
        AdSet.Field.bid_strategy: bid_strategy,
        AdSet.Field.status: status,
        AdSet.Field.targeting: targeting or {
            "geo_locations": {"countries": ["US"]},
            "age_min": 18,
            "age_max": 65,
        },
    }
    if start_time:
        params[AdSet.Field.start_time] = start_time
    if end_time:
        params[AdSet.Field.end_time] = end_time

    adset = account.create_ad_set(params=params)
    log.info(f"AdSet created: {adset['id']}  -  {name}")
    return dict(adset)


def pause_adset(adset_id: str) -> bool:
    AdSet(adset_id).api_update(params={AdSet.Field.status: "PAUSED"})
    log.info(f"AdSet paused: {adset_id}")
    return True


def resume_adset(adset_id: str) -> bool:
    AdSet(adset_id).api_update(params={AdSet.Field.status: "ACTIVE"})
    log.info(f"AdSet resumed: {adset_id}")
    return True


def update_adset_budget(adset_id: str, daily_budget_usd: float) -> bool:
    AdSet(adset_id).api_update(params={
        AdSet.Field.daily_budget: usd_to_cents(daily_budget_usd)
    })
    log.info(f"AdSet {adset_id} budget updated to ${daily_budget_usd:.2f}")
    return True


def get_adset(adset_id: str) -> dict:
    adset = AdSet(adset_id).api_get(fields=ADSET_FIELDS)
    return dict(adset)
