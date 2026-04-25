import time
import random
from datetime import datetime, date


def fmt_currency(cents: int, symbol: str = "$") -> str:
    return f"{symbol}{cents / 100:,.2f}"


def usd_to_cents(usd: float) -> int:
    return int(round(usd * 100))


def cents_to_usd(cents: int) -> float:
    return round(cents / 100, 2)


def pct_change(old: float, new: float) -> float:
    if old == 0:
        return 0.0
    return round(((new - old) / old) * 100, 2)


def random_delay(min_s: float = 0.5, max_s: float = 2.0):
    time.sleep(random.uniform(min_s, max_s))


def parse_date_range(date_range: str) -> dict:
    """
    Accepts 'last_7d', 'last_30d', etc. OR 'YYYY-MM-DD:YYYY-MM-DD'.
    Returns dict with 'date_preset' OR 'time_range'.
    """
    presets = ["today", "yesterday", "last_7d", "last_30d", "last_90d", "this_month", "last_month"]
    if date_range in presets:
        return {"date_preset": date_range}
    if ":" in date_range:
        parts = date_range.split(":")
        if len(parts) == 2:
            return {"time_range": {"since": parts[0], "until": parts[1]}}
    return {"date_preset": "last_7d"}


def format_datetime(dt_str: str) -> str:
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return dt_str


def today_str() -> str:
    return date.today().isoformat()


def color_metric(value: float, green_threshold: float, red_threshold: float,
                 higher_is_better: bool = True) -> str:
    """Returns colorama-colored string for a metric value."""
    from colorama import Fore, Style
    if higher_is_better:
        if value >= green_threshold:
            color = Fore.GREEN
        elif value >= red_threshold:
            color = Fore.YELLOW
        else:
            color = Fore.RED
    else:
        if value <= green_threshold:
            color = Fore.GREEN
        elif value <= red_threshold:
            color = Fore.YELLOW
        else:
            color = Fore.RED
    return f"{color}{value:.2f}{Style.RESET_ALL}"
