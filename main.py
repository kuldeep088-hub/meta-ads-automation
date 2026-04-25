#!/usr/bin/env python3
"""
Meta Ads Automation  -  CLI

Usage:
  python main.py campaign create --name "..." --objective OUTCOME_TRAFFIC --budget 50
  python main.py campaign list
  python main.py campaign pause --id <campaign_id>
  python main.py adset list --campaign-id <id>
  python main.py ad create --adset-id <id> --campaign-id <id> --headline "..." --body "..." --cta LEARN_MORE --link https://...
  python main.py optimize --dry-run
  python main.py report --campaign-id <id> --date-range last_7d --format table
  python main.py report account --date-range last_30d
  python main.py monitor start --interval 60
  python main.py monitor check
  python main.py copy generate --product "..." --audience "..." --tone professional --count 3
  python main.py stats
  python main.py setup verify
"""

import argparse
import sys
from colorama import Fore, Style, init
from dotenv import load_dotenv

load_dotenv()
init(autoreset=True)

from database.db import init_db
from utils.logger import get_logger

log = get_logger("main")


def banner():
    print(f"""
{Fore.CYAN}============================================================
        META ADS AUTOMATION  v1.0
        Meta Marketing API + Claude AI
============================================================{Style.RESET_ALL}""")


# ── Parser builders ───────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Meta Ads Automation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    subs = parser.add_subparsers(dest="command", required=True)

    _add_campaign_commands(subs)
    _add_adset_commands(subs)
    _add_ad_commands(subs)
    _add_optimize_command(subs)
    _add_report_commands(subs)
    _add_monitor_commands(subs)
    _add_copy_commands(subs)
    _add_stats_command(subs)
    _add_setup_commands(subs)

    return parser


def _add_campaign_commands(subs):
    cp = subs.add_parser("campaign", help="Manage campaigns")
    cp_sub = cp.add_subparsers(dest="action", required=True)

    # create
    p = cp_sub.add_parser("create", help="Create a new campaign")
    p.add_argument("--name", required=True)
    p.add_argument("--objective", required=True,
                   choices=["OUTCOME_TRAFFIC","OUTCOME_LEADS","OUTCOME_SALES",
                            "OUTCOME_AWARENESS","OUTCOME_ENGAGEMENT","OUTCOME_APP_PROMOTION"])
    p.add_argument("--budget", type=float, required=True, help="Daily budget in USD")
    p.add_argument("--start", help="Start date YYYY-MM-DD (default: today)")
    p.add_argument("--end", help="End date YYYY-MM-DD (optional)")
    p.add_argument("--audience-id", help="Saved audience ID")
    p.add_argument("--placement", default="automatic",
                   choices=["automatic","facebook_feed","instagram_feed","stories","reels"])
    p.add_argument("--dry-run", action="store_true", help="Preview without creating")

    # list
    p = cp_sub.add_parser("list", help="List campaigns")
    p.add_argument("--status", default=None, help="Filter by status: ACTIVE, PAUSED, ARCHIVED")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--sync", action="store_true", help="Sync from Meta API first")

    # pause
    p = cp_sub.add_parser("pause", help="Pause a campaign")
    p.add_argument("--id", required=True, dest="campaign_id")

    # resume
    p = cp_sub.add_parser("resume", help="Resume a campaign")
    p.add_argument("--id", required=True, dest="campaign_id")

    # delete
    p = cp_sub.add_parser("delete", help="Delete a campaign")
    p.add_argument("--id", required=True, dest="campaign_id")
    p.add_argument("--confirm", action="store_true", help="Required to confirm deletion")


def _add_adset_commands(subs):
    asp = subs.add_parser("adset", help="Manage ad sets")
    asp_sub = asp.add_subparsers(dest="action", required=True)

    # create
    p = asp_sub.add_parser("create", help="Create an ad set")
    p.add_argument("--campaign-id", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--budget", type=float, required=True, help="Daily budget in USD")
    p.add_argument("--bid-strategy", default="LOWEST_COST_WITHOUT_CAP",
                   choices=["LOWEST_COST_WITHOUT_CAP","COST_CAP","MINIMUM_ROAS"])
    p.add_argument("--optimization-goal", default="LINK_CLICKS")
    p.add_argument("--targeting-json", help="Path to targeting JSON file")
    p.add_argument("--dry-run", action="store_true")

    # list
    p = asp_sub.add_parser("list", help="List ad sets")
    p.add_argument("--campaign-id", required=True)

    # pause / resume
    for action in ("pause", "resume"):
        p = asp_sub.add_parser(action, help=f"{action.capitalize()} an ad set")
        p.add_argument("--id", required=True, dest="adset_id")


def _add_ad_commands(subs):
    adp = subs.add_parser("ad", help="Manage ads")
    adp_sub = adp.add_subparsers(dest="action", required=True)

    # create
    p = adp_sub.add_parser("create", help="Create an ad")
    p.add_argument("--adset-id", required=True)
    p.add_argument("--campaign-id", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--headline", required=True, help="Max 40 characters")
    p.add_argument("--body", required=True, help="Max 125 characters")
    p.add_argument("--cta", required=True,
                   choices=["LEARN_MORE","SHOP_NOW","SIGN_UP","GET_QUOTE",
                            "BOOK_TRAVEL","DOWNLOAD","CONTACT_US","APPLY_NOW","SUBSCRIBE","WATCH_MORE"])
    p.add_argument("--image-url", help="Image URL for the ad creative")
    p.add_argument("--link", required=True, help="Destination URL")
    p.add_argument("--use-copy-id", type=int, help="Link a generated copy record to this ad")
    p.add_argument("--dry-run", action="store_true")

    # list
    p = adp_sub.add_parser("list", help="List ads")
    p.add_argument("--adset-id", required=True)


def _add_optimize_command(subs):
    p = subs.add_parser("optimize", help="Run budget optimization rules")
    p.add_argument("--account-id", help="Ad account ID (uses .env default if not set)")
    p.add_argument("--dry-run", action="store_true", help="Preview actions without applying")
    p.add_argument("--min-roas", type=float, help="Override MIN_ROAS_THRESHOLD")
    p.add_argument("--max-cpa", type=float, help="Override MAX_CPA_THRESHOLD")


def _add_report_commands(subs):
    rp = subs.add_parser("report", help="Generate performance reports")
    rp_sub = rp.add_subparsers(dest="action")

    # campaign report (default action)
    rp.add_argument("--campaign-id", help="Campaign ID")
    rp.add_argument("--date-range", default="last_7d",
                    help="Date range: last_7d, last_30d, YYYY-MM-DD:YYYY-MM-DD")
    rp.add_argument("--format", default="table", choices=["table","csv","json"])
    rp.add_argument("--output", help="Output file path (for csv/json formats)")

    # account report
    p = rp_sub.add_parser("account", help="Account-level report")
    p.add_argument("--date-range", default="last_30d")
    p.add_argument("--format", default="table", choices=["table","csv","json"])
    p.add_argument("--output", help="Output file path")


def _add_monitor_commands(subs):
    mp = subs.add_parser("monitor", help="Monitor campaigns")
    mp_sub = mp.add_subparsers(dest="action", required=True)

    p = mp_sub.add_parser("start", help="Start continuous monitoring")
    p.add_argument("--interval", type=int, default=60, help="Check interval in minutes")
    p.add_argument("--alert-email", help="Email for critical alerts (overrides .env)")

    p = mp_sub.add_parser("check", help="Run one-shot alert check")
    p.add_argument("--campaign-id", help="Check specific campaign only")
    p.add_argument("--alert-email", help="Email for critical alerts")


def _add_copy_commands(subs):
    cp = subs.add_parser("copy", help="AI ad copy generation")
    cp_sub = cp.add_subparsers(dest="action", required=True)

    p = cp_sub.add_parser("generate", help="Generate AI ad copy variations")
    p.add_argument("--product", required=True, help="Product or service description")
    p.add_argument("--audience", required=True, help="Target audience description")
    p.add_argument("--tone", default="professional",
                   choices=["professional","casual","urgent","emotional","humorous"])
    p.add_argument("--objective", default="traffic",
                   choices=["traffic","leads","sales","awareness","engagement"])
    p.add_argument("--count", type=int, default=3, help="Number of variations (default: 3)")

    p = cp_sub.add_parser("list", help="List saved copy variations")
    p.add_argument("--limit", type=int, default=10)


def _add_stats_command(subs):
    subs.add_parser("stats", help="Show database statistics")


def _add_setup_commands(subs):
    sp = subs.add_parser("setup", help="Setup and verification")
    sp_sub = sp.add_subparsers(dest="action", required=True)
    sp_sub.add_parser("verify", help="Verify Meta API credentials")


# ── Command handlers ──────────────────────────────────────────

def handle_campaign(args):
    from tabulate import tabulate

    if args.action == "create":
        from campaigns.creator import create_full_campaign
        try:
            result = create_full_campaign(
                name=args.name,
                objective=args.objective,
                daily_budget_usd=args.budget,
                start_time=args.start,
                stop_time=args.end,
                audience_id=args.audience_id,
                placement=args.placement,
                dry_run=args.dry_run,
            )
            prefix = "[DRY RUN] " if args.dry_run else ""
            print(f"\n{Fore.GREEN}{prefix}Campaign created successfully!{Style.RESET_ALL}")
            camp = result["campaign"]
            adset = result["adset"]
            rows = [
                ["Campaign ID", camp.get("id", "N/A")],
                ["Name", args.name],
                ["Objective", args.objective],
                ["Daily Budget", f"${args.budget:.2f}"],
                ["AdSet ID", adset.get("id", "N/A")],
                ["Status", "PAUSED (activate in Meta Ads Manager when ready)"],
            ]
            print(tabulate(rows, tablefmt="grid"))
        except ValueError as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
            sys.exit(1)

    elif args.action == "list":
        if args.sync:
            _sync_campaigns()
        from database.db import get_campaigns
        campaigns = get_campaigns(status=args.status, limit=args.limit)
        if not campaigns:
            print("No campaigns found. Try --sync to fetch from Meta API.")
            return
        rows = [[c["id"], c["name"][:30], c["status"],
                 c.get("objective","N/A"), f"${(c.get('daily_budget') or 0)/100:.2f}",
                 c.get("created_at","")[:10]] for c in campaigns]
        print(tabulate(rows, headers=["ID","Name","Status","Objective","Daily Budget","Created"],
                       tablefmt="grid"))

    elif args.action == "pause":
        from api.campaigns import pause_campaign
        from database.db import update_campaign
        pause_campaign(args.campaign_id)
        update_campaign(args.campaign_id, status="PAUSED")
        print(f"{Fore.YELLOW}Campaign {args.campaign_id} paused.{Style.RESET_ALL}")

    elif args.action == "resume":
        from api.campaigns import resume_campaign
        from database.db import update_campaign
        resume_campaign(args.campaign_id)
        update_campaign(args.campaign_id, status="ACTIVE")
        print(f"{Fore.GREEN}Campaign {args.campaign_id} resumed.{Style.RESET_ALL}")

    elif args.action == "delete":
        if not args.confirm:
            print(f"{Fore.RED}Add --confirm to delete campaign {args.campaign_id}{Style.RESET_ALL}")
            sys.exit(1)
        from api.campaigns import delete_campaign
        from database.db import update_campaign
        delete_campaign(args.campaign_id)
        update_campaign(args.campaign_id, status="DELETED")
        print(f"{Fore.RED}Campaign {args.campaign_id} deleted.{Style.RESET_ALL}")


def _sync_campaigns():
    from api.campaigns import list_campaigns
    from database.db import upsert_campaign
    from utils.helpers import usd_to_cents
    log.info("Syncing campaigns from Meta API...")
    campaigns = list_campaigns(limit=100)
    for c in campaigns:
        upsert_campaign({
            "id": c["id"],
            "name": c.get("name", ""),
            "objective": c.get("objective", ""),
            "status": c.get("status", "UNKNOWN"),
            "daily_budget": int(c["daily_budget"]) if c.get("daily_budget") else None,
            "lifetime_budget": int(c["lifetime_budget"]) if c.get("lifetime_budget") else None,
            "start_time": c.get("start_time"),
            "stop_time": c.get("stop_time"),
        })
    log.info(f"Synced {len(campaigns)} campaigns.")


def handle_adset(args):
    from tabulate import tabulate

    if args.action == "create":
        import json as _json
        targeting = None
        if args.targeting_json:
            with open(args.targeting_json) as f:
                targeting = _json.load(f)

        if args.dry_run:
            print(f"[DRY RUN] Would create AdSet '{args.name}' in campaign {args.campaign_id}")
            return

        from api.adsets import create_adset
        from database.db import upsert_adset
        from utils.helpers import usd_to_cents
        adset = create_adset(
            campaign_id=args.campaign_id,
            name=args.name,
            daily_budget_usd=args.budget,
            bid_strategy=args.bid_strategy,
            optimization_goal=args.optimization_goal,
            targeting=targeting,
        )
        upsert_adset({
            "id": adset["id"], "campaign_id": args.campaign_id,
            "name": args.name, "status": "PAUSED",
            "daily_budget": usd_to_cents(args.budget),
            "bid_strategy": args.bid_strategy,
            "optimization_goal": args.optimization_goal,
        })
        print(f"{Fore.GREEN}AdSet created: {adset['id']}{Style.RESET_ALL}")

    elif args.action == "list":
        from api.adsets import list_adsets
        adsets = list_adsets(args.campaign_id)
        if not adsets:
            print("No ad sets found for this campaign.")
            return
        rows = [[a["id"], a.get("name","")[:30], a.get("status",""),
                 f"${int(a.get('daily_budget',0))/100:.2f}" if a.get("daily_budget") else "N/A"]
                for a in adsets]
        print(tabulate(rows, headers=["ID","Name","Status","Daily Budget"], tablefmt="grid"))

    elif args.action == "pause":
        from api.adsets import pause_adset
        pause_adset(args.adset_id)
        print(f"{Fore.YELLOW}AdSet {args.adset_id} paused.{Style.RESET_ALL}")

    elif args.action == "resume":
        from api.adsets import resume_adset
        resume_adset(args.adset_id)
        print(f"{Fore.GREEN}AdSet {args.adset_id} resumed.{Style.RESET_ALL}")


def handle_ad(args):
    from tabulate import tabulate

    if args.action == "create":
        from campaigns.creator import create_ad_with_creative
        from database.db import link_copy_to_ad
        try:
            ad = create_ad_with_creative(
                adset_id=args.adset_id,
                campaign_id=args.campaign_id,
                name=args.name,
                headline=args.headline,
                body=args.body,
                cta=args.cta,
                image_url=args.image_url or "",
                link=args.link,
                dry_run=args.dry_run,
            )
            if args.use_copy_id and not args.dry_run:
                link_copy_to_ad(args.use_copy_id, ad["id"])
            prefix = "[DRY RUN] " if args.dry_run else ""
            print(f"\n{Fore.GREEN}{prefix}Ad created: {ad.get('id','N/A')}{Style.RESET_ALL}")
        except ValueError as e:
            print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
            sys.exit(1)

    elif args.action == "list":
        from api.ads import list_ads
        ads = list_ads(args.adset_id)
        if not ads:
            print("No ads found for this ad set.")
            return
        rows = [[a["id"], a.get("name","")[:30], a.get("status","")] for a in ads]
        print(tabulate(rows, headers=["ID","Name","Status"], tablefmt="grid"))


def handle_optimize(args):
    from campaigns.optimizer import BudgetOptimizer
    from reporting.formatter import print_optimization_results

    print(f"\n{Fore.CYAN}Running optimization rules...{Style.RESET_ALL}")
    optimizer = BudgetOptimizer(
        dry_run=args.dry_run,
        min_roas=args.min_roas,
        max_cpa=args.max_cpa,
    )
    actions = optimizer.run_all(account_id=args.account_id)
    print_optimization_results(actions)

    real = [a for a in actions if a.action not in ("no_action", "alert")]
    if args.dry_run and real:
        print(f"{Fore.YELLOW}Dry run  -  {len(real)} action(s) would be applied. Remove --dry-run to execute.{Style.RESET_ALL}")


def handle_report(args):
    # Account report
    if hasattr(args, "action") and args.action == "account":
        from reporting.collector import collect_account_report
        from reporting.formatter import print_account_report
        from reporting.exporter import export_csv, export_json
        ctx = collect_account_report(date_range=args.date_range)
        if args.format == "table":
            print_account_report(ctx)
        elif args.format == "csv":
            out = args.output or "account_report.csv"
            from reporting.exporter import export_account_csv
            export_account_csv(ctx, out)
        elif args.format == "json":
            out = args.output or "account_report.json"
            export_json(ctx, out)
        return

    # Campaign report
    if not args.campaign_id:
        print(f"{Fore.RED}--campaign-id is required (or use 'report account' for account-level){Style.RESET_ALL}")
        sys.exit(1)

    from reporting.collector import collect_campaign_report
    from reporting.formatter import print_campaign_report
    from reporting.exporter import export_csv, export_json

    ctx = collect_campaign_report(args.campaign_id, date_range=args.date_range)

    if args.format == "table":
        print_campaign_report(ctx)
    elif args.format == "csv":
        out = args.output or f"report_{args.campaign_id}.csv"
        export_csv(ctx, out)
    elif args.format == "json":
        out = args.output or f"report_{args.campaign_id}.json"
        export_json(ctx, out)


def handle_monitor(args):
    import config as cfg
    alert_email = getattr(args, "alert_email", None) or cfg.ALERT_EMAIL

    if args.action == "start":
        from monitor.scheduler import start_monitor
        start_monitor(interval_minutes=args.interval, alert_email=alert_email)

    elif args.action == "check":
        from monitor.alert_engine import check_all_alerts
        check_all_alerts(alert_email=alert_email)


def handle_copy(args):
    from tabulate import tabulate

    if args.action == "generate":
        from creative.copy_generator import generate_copy
        print(f"\n{Fore.CYAN}Generating {args.count} ad copy variations...{Style.RESET_ALL}\n")
        variations = generate_copy(
            product=args.product,
            audience=args.audience,
            tone=args.tone,
            objective=args.objective,
            count=args.count,
        )
        if not variations:
            return
        rows = [[i+1, v.headline, v.body[:60]+"..." if len(v.body)>60 else v.body,
                 v.cta, v.hook] for i, v in enumerate(variations)]
        print(tabulate(rows, headers=["#","Headline","Body","CTA","Hook"], tablefmt="grid"))
        print(f"\n{Fore.GREEN}{len(variations)} variation(s) saved. Use --use-copy-id N with 'ad create'.{Style.RESET_ALL}")

    elif args.action == "list":
        from database.db import get_copy
        copies = get_copy(limit=args.limit)
        if not copies:
            print("No generated copy found.")
            return
        rows = [[c["id"], c.get("product","")[:20], c["headline"], c["cta"],
                 c.get("created_at","")[:10], c.get("used_in_ad_id"," - ") or " - "]
                for c in copies]
        print(tabulate(rows, headers=["ID","Product","Headline","CTA","Date","Used In Ad"],
                       tablefmt="grid"))


def handle_stats(args):
    from tabulate import tabulate
    from database.db import get_stats
    stats = get_stats()
    rows = [[k.replace("_", " ").title(), v] for k, v in stats.items()]
    print(f"\n{Fore.CYAN}  DATABASE STATISTICS{Style.RESET_ALL}")
    print(tabulate(rows, headers=["Table", "Count"], tablefmt="grid"))
    print()


def handle_setup(args):
    if args.action == "verify":
        print(f"\n{Fore.CYAN}Verifying Meta API credentials...{Style.RESET_ALL}")
        try:
            from api.client import init_api, get_account
            init_api()
            account = get_account()
            info = account.api_get(fields=["id", "name", "currency", "timezone_name", "account_status"])
            status_map = {1: "ACTIVE", 2: "DISABLED", 3: "UNSETTLED", 7: "PENDING_RISK_REVIEW", 9: "IN_GRACE_PERIOD"}
            status = status_map.get(info.get("account_status"), str(info.get("account_status")))
            print(f"\n{Fore.GREEN}API connection OK!{Style.RESET_ALL}")
            from tabulate import tabulate
            rows = [
                ["Account ID",   info.get("id","N/A")],
                ["Account Name", info.get("name","N/A")],
                ["Currency",     info.get("currency","N/A")],
                ["Timezone",     info.get("timezone_name","N/A")],
                ["Status",       status],
            ]
            print(tabulate(rows, tablefmt="grid"))
        except EnvironmentError as e:
            print(f"{Fore.RED}Configuration error: {e}{Style.RESET_ALL}")
            sys.exit(1)
        except Exception as e:
            print(f"{Fore.RED}API connection failed: {e}{Style.RESET_ALL}")
            print("Check your META_APP_ID, META_APP_SECRET, META_ACCESS_TOKEN, META_AD_ACCOUNT_ID in .env")
            sys.exit(1)


# ── Dispatch ──────────────────────────────────────────────────

def dispatch(args):
    handlers = {
        "campaign": handle_campaign,
        "adset":    handle_adset,
        "ad":       handle_ad,
        "optimize": handle_optimize,
        "report":   handle_report,
        "monitor":  handle_monitor,
        "copy":     handle_copy,
        "stats":    handle_stats,
        "setup":    handle_setup,
    }
    handler = handlers.get(args.command)
    if handler:
        handler(args)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


def main():
    banner()
    init_db()
    parser = build_parser()
    args = parser.parse_args()
    dispatch(args)


if __name__ == "__main__":
    main()
