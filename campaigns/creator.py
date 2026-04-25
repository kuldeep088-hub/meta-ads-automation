import json
from datetime import date

from api import campaigns as campaigns_api
from api import adsets as adsets_api
from api import ads as ads_api
from campaigns.validator import validate_campaign_params, validate_adset_params, validate_ad_params
from database import db
from utils.logger import get_logger
from utils.helpers import usd_to_cents, today_str
import config

log = get_logger("campaigns.creator")


def create_full_campaign(
    name: str,
    objective: str,
    daily_budget_usd: float,
    start_time: str = None,
    stop_time: str = None,
    audience_id: str = None,
    placement: str = "automatic",
    dry_run: bool = False,
) -> dict:
    start_time = start_time or today_str()

    errors = validate_campaign_params(name, objective, daily_budget_usd, start_time=start_time, stop_time=stop_time)
    if errors:
        for e in errors:
            log.error(f"Validation: {e}")
        raise ValueError(f"Validation failed: {'; '.join(errors)}")

    result = {
        "campaign": None,
        "adset": None,
        "dry_run": dry_run,
    }

    if dry_run:
        log.info(f"[DRY RUN] Would create campaign: '{name}' | {objective} | ${daily_budget_usd:.2f}/day")
        result["campaign"] = {"id": "DRY_RUN_CAMPAIGN_ID", "name": name, "status": "PAUSED"}
        result["adset"] = {"id": "DRY_RUN_ADSET_ID", "name": f"{name}  -  AdSet 1", "status": "PAUSED"}
        return result

    # Create Campaign
    campaign = campaigns_api.create_campaign(
        name=name,
        objective=objective,
        daily_budget_usd=daily_budget_usd,
        start_time=start_time,
        stop_time=stop_time,
        status="PAUSED",
    )
    db.upsert_campaign({
        "id": campaign["id"],
        "name": name,
        "objective": objective,
        "status": "PAUSED",
        "daily_budget": usd_to_cents(daily_budget_usd),
        "start_time": start_time,
        "stop_time": stop_time,
    })
    result["campaign"] = campaign

    # Build targeting
    targeting = {"geo_locations": {"countries": ["US"]}, "age_min": 18, "age_max": 65}
    if audience_id:
        targeting["custom_audiences"] = [{"id": audience_id}]

    # Determine optimization goal from objective
    goal_map = {
        "OUTCOME_TRAFFIC":    "LINK_CLICKS",
        "OUTCOME_LEADS":      "LEAD_GENERATION",
        "OUTCOME_SALES":      "OFFSITE_CONVERSIONS",
        "OUTCOME_AWARENESS":  "REACH",
        "OUTCOME_ENGAGEMENT": "POST_ENGAGEMENT",
        "OUTCOME_APP_PROMOTION": "APP_INSTALLS",
    }
    optimization_goal = goal_map.get(objective, "LINK_CLICKS")

    # Create AdSet
    adset = adsets_api.create_adset(
        campaign_id=campaign["id"],
        name=f"{name}  -  AdSet 1",
        daily_budget_usd=daily_budget_usd,
        optimization_goal=optimization_goal,
        targeting=targeting,
        start_time=start_time,
        end_time=stop_time,
        status="PAUSED",
    )
    db.upsert_adset({
        "id": adset["id"],
        "campaign_id": campaign["id"],
        "name": f"{name}  -  AdSet 1",
        "status": "PAUSED",
        "daily_budget": usd_to_cents(daily_budget_usd),
        "optimization_goal": optimization_goal,
        "targeting": json.dumps(targeting),
    })
    result["adset"] = adset

    log.info(f"Campaign + AdSet created successfully. Campaign ID: {campaign['id']}")
    return result


def create_ad_with_creative(
    adset_id: str,
    campaign_id: str,
    name: str,
    headline: str,
    body: str,
    cta: str,
    image_url: str,
    link: str,
    page_id: str = None,
    dry_run: bool = False,
) -> dict:
    errors = validate_ad_params(adset_id, headline, body, cta, link)
    if errors:
        for e in errors:
            log.error(f"Validation: {e}")
        raise ValueError(f"Validation failed: {'; '.join(errors)}")

    if dry_run:
        log.info(f"[DRY RUN] Would create ad: '{name}' | Headline: {headline}")
        return {"id": "DRY_RUN_AD_ID", "name": name, "dry_run": True}

    creative = ads_api.create_ad_creative(
        name=f"{name}  -  Creative",
        headline=headline,
        body=body,
        cta=cta,
        image_url=image_url,
        link=link,
        page_id=page_id,
    )

    ad = ads_api.create_ad(
        name=name,
        adset_id=adset_id,
        creative_id=creative["id"],
        status="PAUSED",
    )

    db.upsert_ad({
        "id": ad["id"],
        "adset_id": adset_id,
        "campaign_id": campaign_id,
        "name": name,
        "status": "PAUSED",
        "headline": headline,
        "body": body,
        "cta": cta,
        "image_url": image_url,
        "destination_url": link,
    })

    log.info(f"Ad created: {ad['id']}")
    return dict(ad)
