from datetime import date
import config
from utils.logger import get_logger

log = get_logger("campaigns.validator")


def validate_campaign_params(
    name: str,
    objective: str,
    daily_budget_usd: float = None,
    lifetime_budget_usd: float = None,
    start_time: str = None,
    stop_time: str = None,
) -> list:
    errors = []

    if not name or len(name.strip()) < 2:
        errors.append("Campaign name must be at least 2 characters.")

    if objective not in config.OBJECTIVES:
        errors.append(f"Invalid objective '{objective}'. Choose from: {', '.join(config.OBJECTIVES)}")

    if daily_budget_usd is None and lifetime_budget_usd is None:
        errors.append("Either daily_budget or lifetime_budget is required.")

    if daily_budget_usd is not None and daily_budget_usd < 1.0:
        errors.append("Daily budget must be at least $1.00.")

    if start_time and stop_time:
        try:
            s = date.fromisoformat(start_time)
            e = date.fromisoformat(stop_time)
            if e <= s:
                errors.append("End date must be after start date.")
        except ValueError:
            errors.append("Dates must be in YYYY-MM-DD format.")

    return errors


def validate_adset_params(campaign_id: str, name: str, daily_budget_usd: float) -> list:
    errors = []
    if not campaign_id:
        errors.append("campaign_id is required.")
    if not name or len(name.strip()) < 2:
        errors.append("AdSet name must be at least 2 characters.")
    if daily_budget_usd < 1.0:
        errors.append("AdSet daily budget must be at least $1.00.")
    return errors


def validate_ad_params(adset_id: str, headline: str, body: str, cta: str, link: str) -> list:
    errors = []
    if not adset_id:
        errors.append("adset_id is required.")
    if not headline or len(headline) > 40:
        errors.append("Headline is required and must be 40 characters or fewer.")
    if not body or len(body) > 125:
        errors.append("Body text is required and must be 125 characters or fewer.")
    if cta not in config.CTA_OPTIONS:
        errors.append(f"Invalid CTA '{cta}'. Choose from: {', '.join(config.CTA_OPTIONS)}")
    if not link or not link.startswith("http"):
        errors.append("A valid destination URL (starting with http) is required.")
    return errors
