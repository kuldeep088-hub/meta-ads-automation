import schedule
import time
from utils.logger import get_logger
import config

log = get_logger("monitor.scheduler")


def run_optimization_check(alert_email: str = None):
    log.info("Running scheduled optimization check...")
    from campaigns.optimizer import BudgetOptimizer
    from reporting.formatter import print_optimization_results
    optimizer = BudgetOptimizer(dry_run=False)
    actions = optimizer.run_all()
    print_optimization_results(actions)


def run_insights_sync():
    log.info("Running scheduled insights sync...")
    from api.insights import get_account_insights
    from database import db
    rows = get_account_insights("today")
    for row in rows:
        cid = row.get("campaign_id", "")
        if cid:
            db.save_insights("campaign", cid, row)
    log.info(f"Synced {len(rows)} insight rows.")


def run_alerts_check(alert_email: str = None):
    log.info("Running scheduled alert check...")
    from monitor.alert_engine import check_all_alerts
    check_all_alerts(alert_email=alert_email)


def start_monitor(interval_minutes: int = None, alert_email: str = None):
    interval = interval_minutes or config.DEFAULT_MONITOR_INTERVAL_MINUTES
    log.info(f"Starting monitor  -  optimization every {interval} min, sync every {config.INSIGHTS_SYNC_INTERVAL_HOURS}h")

    schedule.every(interval).minutes.do(run_optimization_check, alert_email=alert_email)
    schedule.every(interval).minutes.do(run_alerts_check, alert_email=alert_email)
    schedule.every(config.INSIGHTS_SYNC_INTERVAL_HOURS).hours.do(run_insights_sync)

    # Run once immediately
    run_insights_sync()
    run_alerts_check(alert_email=alert_email)

    print(f"Monitor running. Press Ctrl+C to stop.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        log.info("Monitor stopped.")
        print("\nMonitor stopped.")
