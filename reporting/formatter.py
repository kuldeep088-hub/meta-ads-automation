from colorama import Fore, Style, init
from tabulate import tabulate

init(autoreset=True)


def _c(value: float, green: float, red: float, higher_is_better: bool = True, fmt: str = ".2f") -> str:
    if higher_is_better:
        color = Fore.GREEN if value >= green else (Fore.YELLOW if value >= red else Fore.RED)
    else:
        color = Fore.GREEN if value <= green else (Fore.YELLOW if value <= red else Fore.RED)
    return f"{color}{value:{fmt}}{Style.RESET_ALL}"


def print_campaign_report(ctx: dict):
    campaign = ctx.get("campaign", {})
    totals = ctx.get("totals", {})
    adset_breakdown = ctx.get("adset_breakdown", [])
    ad_breakdown = ctx.get("ad_breakdown", [])
    date_range = ctx.get("date_range", "")

    print(f"\n{Fore.CYAN}{'='*65}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  CAMPAIGN REPORT{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*65}{Style.RESET_ALL}")
    print(f"  Campaign : {campaign.get('name', 'N/A')}")
    print(f"  ID       : {campaign.get('id', 'N/A')}")
    print(f"  Status   : {campaign.get('status', 'N/A')}")
    print(f"  Period   : {date_range}")
    print(f"{Fore.CYAN}{'-'*65}{Style.RESET_ALL}\n")

    # Summary
    summary_rows = [
        ["Impressions", f"{totals.get('impressions', 0):,}"],
        ["Reach",       f"{totals.get('reach', 0):,}"],
        ["Clicks",      f"{totals.get('clicks', 0):,}"],
        ["Spend",       f"${totals.get('spend', 0):,.2f}"],
        ["CTR",         _c(totals.get('ctr', 0), 1.5, 0.5) + "%"],
        ["CPC",         _c(totals.get('cpc', 0), 0.5, 2.0, higher_is_better=False, fmt=".2f")],
        ["CPM",         f"${totals.get('cpm', 0):,.2f}"],
        ["ROAS",        _c(totals.get('roas', 0), 2.0, 1.0)],
        ["Frequency",   _c(totals.get('frequency', 0), 2.0, 4.0, higher_is_better=False, fmt=".2f")],
        ["Leads",       str(totals.get('leads', 0))],
        ["Purchases",   str(totals.get('purchases', 0))],
        ["Cost/Lead",   _c(totals.get('cost_per_lead', 0), 10.0, 25.0, higher_is_better=False, fmt=".2f") if totals.get('leads') else "N/A"],
    ]
    print(tabulate(summary_rows, headers=["Metric", "Value"], tablefmt="grid"))
    print()

    # AdSet breakdown
    if adset_breakdown:
        print(f"\n{Fore.YELLOW}  AdSet Breakdown{Style.RESET_ALL}")
        rows = []
        for a in adset_breakdown:
            rows.append([
                a.get("adset_name", a.get("adset_id", "N/A"))[:30],
                f"${a.get('spend', 0):.2f}",
                f"{a.get('impressions', 0):,}",
                f"{a.get('clicks', 0):,}",
                _c(a.get('ctr', 0), 1.5, 0.5) + "%",
                _c(a.get('roas', 0), 2.0, 1.0),
            ])
        print(tabulate(rows,
                       headers=["AdSet", "Spend", "Impressions", "Clicks", "CTR", "ROAS"],
                       tablefmt="grid"))

    # Ad breakdown
    if ad_breakdown:
        print(f"\n{Fore.YELLOW}  Ad Performance{Style.RESET_ALL}")
        rows = []
        for a in ad_breakdown:
            rows.append([
                a.get("ad_name", a.get("ad_id", "N/A"))[:30],
                f"${a.get('spend', 0):.2f}",
                f"{a.get('clicks', 0):,}",
                _c(a.get('ctr', 0), 1.5, 0.5) + "%",
            ])
        print(tabulate(rows,
                       headers=["Ad", "Spend", "Clicks", "CTR"],
                       tablefmt="grid"))
    print()


def print_account_report(ctx: dict):
    date_range = ctx.get("date_range", "")
    campaigns = ctx.get("campaigns", [])
    account_totals = ctx.get("account_totals", {})

    print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  ACCOUNT REPORT  -  {date_range.upper()}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

    if campaigns:
        rows = []
        for c in campaigns:
            rows.append([
                c.get("campaign_name", "N/A")[:28],
                f"${c.get('spend', 0):.2f}",
                f"{c.get('impressions', 0):,}",
                f"{c.get('clicks', 0):,}",
                _c(c.get('ctr', 0), 1.5, 0.5) + "%",
                _c(c.get('roas', 0), 2.0, 1.0),
                str(c.get('leads', 0)),
            ])
        print(tabulate(rows,
                       headers=["Campaign", "Spend", "Impressions", "Clicks", "CTR", "ROAS", "Leads"],
                       tablefmt="grid"))

    print(f"\n{Fore.CYAN}  Account Totals{Style.RESET_ALL}")
    totals_rows = [
        ["Total Spend",      f"${account_totals.get('spend', 0):,.2f}"],
        ["Total Impressions", f"{account_totals.get('impressions', 0):,}"],
        ["Total Clicks",     f"{account_totals.get('clicks', 0):,}"],
        ["Avg CTR",          _c(account_totals.get('ctr', 0), 1.5, 0.5) + "%"],
        ["Avg ROAS",         _c(account_totals.get('roas', 0), 2.0, 1.0)],
        ["Total Leads",      str(account_totals.get('leads', 0))],
    ]
    print(tabulate(totals_rows, headers=["Metric", "Value"], tablefmt="grid"))
    print()


def print_optimization_results(actions: list):
    if not actions:
        print(f"\n{Fore.GREEN}No actions needed  -  all campaigns within thresholds.{Style.RESET_ALL}\n")
        return

    print(f"\n{Fore.CYAN}{'='*65}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  OPTIMIZATION RESULTS{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*65}{Style.RESET_ALL}\n")

    rows = []
    for a in actions:
        action_color = {
            "pause": Fore.RED,
            "budget_decrease": Fore.YELLOW,
            "budget_increase": Fore.GREEN,
            "alert": Fore.YELLOW,
            "no_action": Fore.WHITE,
        }.get(a.action, Fore.WHITE)

        old_val = f"${a.old_value:.2f}" if a.old_value is not None else "N/A"
        new_val = f"${a.new_value:.2f}" if a.new_value is not None else "N/A"
        rows.append([
            a.entity_name[:28],
            f"{action_color}{a.action.upper()}{Style.RESET_ALL}",
            old_val,
            new_val,
            a.reason[:45],
            "YES" if a.dry_run else "NO",
        ])

    print(tabulate(rows,
                   headers=["AdSet", "Action", "Old Budget", "New Budget", "Reason", "Dry Run"],
                   tablefmt="grid"))
    print()
