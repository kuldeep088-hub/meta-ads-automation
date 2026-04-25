import csv
import json
from utils.logger import get_logger

log = get_logger("reporting.exporter")


def export_csv(ctx: dict, output_path: str):
    rows = []
    campaign = ctx.get("campaign", {})
    date_range = ctx.get("date_range", "")
    base = {
        "campaign_id": campaign.get("id", ""),
        "campaign_name": campaign.get("name", ""),
        "date_range": date_range,
    }

    for row in ctx.get("daily_rows", []):
        rows.append({**base, **row})

    if not rows:
        totals = ctx.get("totals", {})
        rows = [{**base, **totals}]

    if not rows:
        log.warning("No data to export.")
        return

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    log.info(f"Report exported to CSV: {output_path}")
    print(f"Exported to: {output_path}")


def export_json(ctx: dict, output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ctx, f, indent=2, default=str)
    log.info(f"Report exported to JSON: {output_path}")
    print(f"Exported to: {output_path}")


def export_account_csv(ctx: dict, output_path: str):
    campaigns = ctx.get("campaigns", [])
    if not campaigns:
        log.warning("No campaign data to export.")
        return

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campaigns[0].keys())
        writer.writeheader()
        writer.writerows(campaigns)

    log.info(f"Account report exported to: {output_path}")
    print(f"Exported to: {output_path}")
