from colorama import Fore, Style, init
from datetime import datetime

from api.insights import get_adset_insights_direct, get_campaign_insights
from database import db
from utils.logger import get_logger
from utils.mailer import send_email_alert
import config

init(autoreset=True)
log = get_logger("monitor.alert_engine")


def check_all_alerts(account_id: str = None, alert_email: str = None) -> list:
    campaigns = db.get_campaigns(status="ACTIVE")
    if not campaigns:
        log.info("No active campaigns to check.")
        return []

    triggered = []
    for campaign in campaigns:
        campaign_id = campaign["id"]
        campaign_name = campaign.get("name", campaign_id)

        # Campaign-level insights
        insights = get_campaign_insights(campaign_id, "today")
        insights_7d = get_campaign_insights(campaign_id, "last_7d")

        for check_fn in [check_spend_spike, check_budget_depletion_campaign]:
            alert = check_fn(campaign, insights, insights_7d)
            if alert:
                alert["campaign_id"] = campaign_id
                _trigger_alert(alert, campaign_name, alert_email)
                triggered.append(alert)

        # AdSet-level checks
        adsets = db.get_adsets(campaign_id=campaign_id)
        for adset in adsets:
            if adset.get("status") != "ACTIVE":
                continue
            adset_insights = get_adset_insights_direct(adset["id"], "last_7d")
            if not adset_insights:
                continue

            for check_fn in [check_low_roas, check_high_cpa, check_low_ctr, check_frequency_fatigue]:
                alert = check_fn(adset, adset_insights)
                if alert:
                    alert["campaign_id"] = campaign_id
                    alert["adset_id"] = adset["id"]
                    _trigger_alert(alert, campaign_name, alert_email)
                    triggered.append(alert)

    if not triggered:
        print(f"{Fore.GREEN}All campaigns healthy  -  no alerts triggered.{Style.RESET_ALL}")

    return triggered


def _trigger_alert(alert: dict, campaign_name: str, alert_email: str = None):
    severity_color = {
        "critical": Fore.RED,
        "warning": Fore.YELLOW,
        "info": Fore.CYAN,
    }.get(alert.get("severity", "info"), Fore.WHITE)

    print(f"{severity_color}[ALERT][{alert['alert_type'].upper()}] {campaign_name}: {alert['message']}{Style.RESET_ALL}")
    alert_id = db.save_alert(alert)

    if alert.get("severity") == "critical" and alert_email:
        sent = send_email_alert(
            to_email=alert_email,
            alert_type=alert["alert_type"],
            campaign_name=campaign_name,
            message=alert["message"],
            actual_value=alert.get("actual_value", 0),
            threshold_value=alert.get("threshold_value", 0),
        )
        if sent:
            db.mark_alert_emailed(alert_id)


def check_low_roas(adset: dict, insights: list) -> dict | None:
    if not insights:
        return None
    avg_roas = sum(i.get("roas", 0) for i in insights if i.get("roas", 0) > 0)
    count = sum(1 for i in insights if i.get("roas", 0) > 0)
    if count == 0:
        return None
    avg_roas /= count
    total_spend = sum(i.get("spend", 0) for i in insights)

    if avg_roas < config.MIN_ROAS_THRESHOLD and total_spend >= config.MIN_SPEND_FOR_ROAS_EVAL:
        return {
            "alert_type": "low_roas",
            "actual_value": avg_roas,
            "threshold_value": config.MIN_ROAS_THRESHOLD,
            "message": f"AdSet '{adset.get('name')}': Avg ROAS {avg_roas:.2f} < {config.MIN_ROAS_THRESHOLD} (spend: ${total_spend:.2f})",
            "severity": "warning",
        }
    return None


def check_high_cpa(adset: dict, insights: list) -> dict | None:
    total_leads = sum(i.get("leads", 0) for i in insights)
    total_spend = sum(i.get("spend", 0) for i in insights)
    if total_leads < 3:
        return None
    cpl = total_spend / total_leads
    if cpl > config.MAX_CPA_THRESHOLD:
        return {
            "alert_type": "high_cpa",
            "actual_value": cpl,
            "threshold_value": config.MAX_CPA_THRESHOLD,
            "message": f"AdSet '{adset.get('name')}': CPL ${cpl:.2f} > ${config.MAX_CPA_THRESHOLD:.2f} ({total_leads} leads)",
            "severity": "warning",
        }
    return None


def check_low_ctr(adset: dict, insights: list) -> dict | None:
    total_impressions = sum(i.get("impressions", 0) for i in insights)
    if total_impressions < 5000:
        return None
    avg_ctr = sum(i.get("ctr", 0) for i in insights) / len(insights) if insights else 0
    if avg_ctr < config.MIN_CTR_THRESHOLD:
        return {
            "alert_type": "low_ctr",
            "actual_value": avg_ctr,
            "threshold_value": config.MIN_CTR_THRESHOLD,
            "message": f"AdSet '{adset.get('name')}': CTR {avg_ctr:.2f}% < {config.MIN_CTR_THRESHOLD}%  -  refresh creative",
            "severity": "warning",
        }
    return None


def check_frequency_fatigue(adset: dict, insights: list) -> dict | None:
    if not insights:
        return None
    avg_frequency = sum(i.get("frequency", 0) for i in insights) / len(insights)
    if avg_frequency > config.MAX_FREQUENCY:
        return {
            "alert_type": "frequency_fatigue",
            "actual_value": avg_frequency,
            "threshold_value": config.MAX_FREQUENCY,
            "message": f"AdSet '{adset.get('name')}': Frequency {avg_frequency:.1f} > {config.MAX_FREQUENCY}  -  audience fatigue",
            "severity": "info",
        }
    return None


def check_spend_spike(campaign: dict, insights_today: list, insights_7d: list) -> dict | None:
    today_spend = sum(i.get("spend", 0) for i in insights_today)
    total_7d = sum(i.get("spend", 0) for i in insights_7d)
    avg_daily = total_7d / 7 if total_7d else 0
    if avg_daily > 0 and today_spend > avg_daily * config.SPEND_SPIKE_MULTIPLIER:
        return {
            "alert_type": "spend_spike",
            "actual_value": today_spend,
            "threshold_value": avg_daily * config.SPEND_SPIKE_MULTIPLIER,
            "message": f"Campaign '{campaign.get('name')}': Today's spend ${today_spend:.2f} is {today_spend/avg_daily:.1f}x the 7-day avg ${avg_daily:.2f}",
            "severity": "critical",
        }
    return None


def check_budget_depletion_campaign(campaign: dict, insights_today: list, insights_7d: list) -> dict | None:
    now_hour = datetime.now().hour
    if now_hour >= 18:
        return None
    today_spend = sum(i.get("spend", 0) for i in insights_today)
    daily_budget_cents = campaign.get("daily_budget", 0)
    if not daily_budget_cents:
        return None
    daily_budget_usd = daily_budget_cents / 100
    if today_spend >= daily_budget_usd * 0.95:
        return {
            "alert_type": "budget_depleted",
            "actual_value": today_spend,
            "threshold_value": daily_budget_usd,
            "message": f"Campaign '{campaign.get('name')}': Budget nearly depleted (${today_spend:.2f} of ${daily_budget_usd:.2f}) before 6 PM",
            "severity": "critical",
        }
    return None
