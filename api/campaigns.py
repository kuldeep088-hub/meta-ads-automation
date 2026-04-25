from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adaccount import AdAccount

from api.client import get_account
from utils.logger import get_logger
from utils.helpers import usd_to_cents

log = get_logger("api.campaigns")

CAMPAIGN_FIELDS = [
    "id", "name", "status", "objective",
    "daily_budget", "lifetime_budget",
    "start_time", "stop_time",
    "created_time", "updated_time",
    "budget_remaining",
]


def list_campaigns(status: str = None, limit: int = 100) -> list:
    account = get_account()
    params = {"limit": limit}
    if status:
        params["effective_status"] = [status.upper()]
    campaigns = account.get_campaigns(fields=CAMPAIGN_FIELDS, params=params)
    return [dict(c) for c in campaigns]


def create_campaign(
    name: str,
    objective: str,
    daily_budget_usd: float = None,
    lifetime_budget_usd: float = None,
    start_time: str = None,
    stop_time: str = None,
    status: str = "PAUSED",
) -> dict:
    account = get_account()
    params = {
        Campaign.Field.name: name,
        Campaign.Field.objective: objective,
        Campaign.Field.status: status,
        Campaign.Field.special_ad_categories: [],
    }
    if daily_budget_usd:
        params[Campaign.Field.daily_budget] = usd_to_cents(daily_budget_usd)
    if lifetime_budget_usd:
        params[Campaign.Field.lifetime_budget] = usd_to_cents(lifetime_budget_usd)
    if start_time:
        params[Campaign.Field.start_time] = start_time
    if stop_time:
        params[Campaign.Field.stop_time] = stop_time

    campaign = account.create_campaign(params=params)
    log.info(f"Campaign created: {campaign['id']}  -  {name}")
    return dict(campaign)


def pause_campaign(campaign_id: str) -> bool:
    campaign = Campaign(campaign_id)
    campaign.api_update(params={Campaign.Field.status: "PAUSED"})
    log.info(f"Campaign paused: {campaign_id}")
    return True


def resume_campaign(campaign_id: str) -> bool:
    campaign = Campaign(campaign_id)
    campaign.api_update(params={Campaign.Field.status: "ACTIVE"})
    log.info(f"Campaign resumed: {campaign_id}")
    return True


def delete_campaign(campaign_id: str) -> bool:
    campaign = Campaign(campaign_id)
    campaign.api_delete()
    log.info(f"Campaign deleted: {campaign_id}")
    return True


def update_campaign_budget(campaign_id: str, daily_budget_usd: float) -> bool:
    campaign = Campaign(campaign_id)
    campaign.api_update(params={
        Campaign.Field.daily_budget: usd_to_cents(daily_budget_usd)
    })
    log.info(f"Campaign {campaign_id} budget updated to ${daily_budget_usd:.2f}")
    return True
