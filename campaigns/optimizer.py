from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from api import adsets as adsets_api
from api.insights import get_adset_insights_direct
from database import db
from utils.logger import get_logger
from utils.helpers import cents_to_usd, usd_to_cents
import config

log = get_logger("campaigns.optimizer")


@dataclass
class OptimizationAction:
    entity_type: str
    entity_id: str
    entity_name: str
    action: str          # budget_increase | budget_decrease | pause | alert | no_action
    old_value: Optional[float]
    new_value: Optional[float]
    reason: str
    rule_triggered: str
    severity: str = "info"   # info | warning | critical
    dry_run: bool = False


class BudgetOptimizer:
    def __init__(self, dry_run: bool = False, min_roas: float = None, max_cpa: float = None):
        self.dry_run = dry_run
        self.min_roas = min_roas or config.MIN_ROAS_THRESHOLD
        self.max_cpa = max_cpa or config.MAX_CPA_THRESHOLD
        self.actions: list[OptimizationAction] = []

    def run_all(self, account_id: str = None) -> list[OptimizationAction]:
        campaigns = db.get_campaigns(status="ACTIVE")
        if not campaigns:
            log.info("No active campaigns found in local DB. Run 'python main.py campaign list' first to sync.")
            return []

        for campaign in campaigns:
            adsets = db.get_adsets(campaign_id=campaign["id"])
            for adset in adsets:
                if adset.get("status") != "ACTIVE":
                    continue
                try:
                    action = self._evaluate_adset(adset)
                    if action:
                        self.actions.append(action)
                        self._apply_action(action)
                except Exception as e:
                    log.error(f"Error evaluating adset {adset['id']}: {e}")

        return self.actions

    def _evaluate_adset(self, adset: dict) -> Optional[OptimizationAction]:
        adset_id = adset["id"]
        adset_name = adset.get("name", adset_id)
        daily_budget_cents = adset.get("daily_budget", 0)
        daily_budget_usd = cents_to_usd(daily_budget_cents) if daily_budget_cents else 0

        insights = get_adset_insights_direct(adset_id, date_range="last_7d")
        if not insights:
            log.debug(f"No insights for adset {adset_id}, skipping.")
            return None

        # Aggregate across date range
        total_spend = sum(i["spend"] for i in insights)
        total_impressions = sum(i["impressions"] for i in insights)
        total_clicks = sum(i["clicks"] for i in insights)
        total_leads = sum(i["leads"] for i in insights)
        avg_roas = sum(i["roas"] for i in insights) / len(insights) if insights else 0
        avg_ctr = sum(i["ctr"] for i in insights) / len(insights) if insights else 0
        avg_frequency = sum(i["frequency"] for i in insights) / len(insights) if insights else 0
        avg_cpl = (total_spend / total_leads) if total_leads > 0 else 0

        # Rule 1: ROAS Guard  -  pause low ROAS with enough spend
        if avg_roas > 0 and avg_roas < self.min_roas and total_spend >= config.MIN_SPEND_FOR_ROAS_EVAL:
            consecutive = sum(1 for i in insights if i["roas"] < self.min_roas and i["roas"] > 0)
            if consecutive >= config.ROAS_EVAL_CONSECUTIVE_DAYS:
                return OptimizationAction(
                    entity_type="adset", entity_id=adset_id, entity_name=adset_name,
                    action="pause", old_value=daily_budget_usd, new_value=0,
                    reason=f"ROAS {avg_roas:.2f} < {self.min_roas} for {consecutive} days. Spend: ${total_spend:.2f}",
                    rule_triggered="roas_guard", severity="warning", dry_run=self.dry_run,
                )

        # Rule 2: CPA Guard  -  decrease budget for high CPA
        if total_leads >= 3 and avg_cpl > self.max_cpa:
            new_budget = max(
                config.MIN_ADSET_BUDGET_CENTS / 100,
                daily_budget_usd * (1 - config.BUDGET_DECREASE_PCT / 100)
            )
            return OptimizationAction(
                entity_type="adset", entity_id=adset_id, entity_name=adset_name,
                action="budget_decrease", old_value=daily_budget_usd, new_value=round(new_budget, 2),
                reason=f"CPL ${avg_cpl:.2f} > ${self.max_cpa:.2f} with {total_leads} leads",
                rule_triggered="cpa_guard", severity="warning", dry_run=self.dry_run,
            )

        # Rule 3: High Performer  -  increase budget
        if (avg_roas >= config.SCALE_ROAS_THRESHOLD and
                avg_cpl <= config.SCALE_CPA_THRESHOLD and
                total_spend > 0):
            max_budget = (daily_budget_usd * config.MAX_ADSET_BUDGET_MULTIPLIER)
            new_budget = min(max_budget, daily_budget_usd * (1 + config.BUDGET_INCREASE_PCT / 100))
            if new_budget > daily_budget_usd:
                return OptimizationAction(
                    entity_type="adset", entity_id=adset_id, entity_name=adset_name,
                    action="budget_increase", old_value=daily_budget_usd, new_value=round(new_budget, 2),
                    reason=f"ROAS {avg_roas:.2f} >= {config.SCALE_ROAS_THRESHOLD}  -  scaling up",
                    rule_triggered="high_performer", severity="info", dry_run=self.dry_run,
                )

        # Rule 4: Low CTR alert
        if avg_ctr < config.MIN_CTR_THRESHOLD and total_impressions > 5000:
            return OptimizationAction(
                entity_type="adset", entity_id=adset_id, entity_name=adset_name,
                action="alert", old_value=avg_ctr, new_value=None,
                reason=f"CTR {avg_ctr:.2f}% < {config.MIN_CTR_THRESHOLD}%  -  consider refreshing creative",
                rule_triggered="low_ctr", severity="warning", dry_run=self.dry_run,
            )

        # Rule 5: Frequency fatigue
        if avg_frequency > config.MAX_FREQUENCY:
            return OptimizationAction(
                entity_type="adset", entity_id=adset_id, entity_name=adset_name,
                action="alert", old_value=avg_frequency, new_value=None,
                reason=f"Frequency {avg_frequency:.1f} > {config.MAX_FREQUENCY}  -  audience fatigue risk",
                rule_triggered="frequency_fatigue", severity="info", dry_run=self.dry_run,
            )

        return OptimizationAction(
            entity_type="adset", entity_id=adset_id, entity_name=adset_name,
            action="no_action", old_value=daily_budget_usd, new_value=daily_budget_usd,
            reason="All metrics within thresholds.",
            rule_triggered="none", severity="info", dry_run=self.dry_run,
        )

    def _apply_action(self, action: OptimizationAction):
        db.log_optimization({
            "entity_type": action.entity_type,
            "entity_id": action.entity_id,
            "action": action.action,
            "old_value": action.old_value,
            "new_value": action.new_value,
            "reason": action.reason,
            "rule_triggered": action.rule_triggered,
            "dry_run": action.dry_run,
        })

        if action.dry_run:
            return

        if action.action == "pause":
            adsets_api.pause_adset(action.entity_id)
            db.update_adset(action.entity_id, status="PAUSED")

        elif action.action in ("budget_increase", "budget_decrease"):
            adsets_api.update_adset_budget(action.entity_id, action.new_value)
            db.update_adset(action.entity_id, daily_budget=usd_to_cents(action.new_value))

        elif action.action == "alert":
            db.save_alert({
                "adset_id": action.entity_id,
                "alert_type": action.rule_triggered,
                "actual_value": action.old_value or 0,
                "threshold_value": 0,
                "message": action.reason,
            })
