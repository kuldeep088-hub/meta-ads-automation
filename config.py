import os
from dotenv import load_dotenv

load_dotenv()

# ── Meta API ──────────────────────────────────────────────────
API_VERSION = "v21.0"
META_APP_ID = os.getenv("META_APP_ID", "")
META_APP_SECRET = os.getenv("META_APP_SECRET", "")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
META_AD_ACCOUNT_ID = os.getenv("META_AD_ACCOUNT_ID", "")
META_PAGE_ID = os.getenv("META_PAGE_ID", "")

# ── Claude AI (optional) ──────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_MAX_TOKENS_COPY = 1500

# ── Brand defaults ────────────────────────────────────────────
BRAND_NAME = os.getenv("BRAND_NAME", "My Brand")
DEFAULT_LANDING_URL = os.getenv("DEFAULT_LANDING_URL", "https://example.com")

# ── Database ──────────────────────────────────────────────────
DB_PATH = os.getenv("DB_PATH", "meta_ads.db")
LOG_FILE = os.getenv("LOG_FILE", "automation.log")

# ── Email Alerts ──────────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")

# ── Optimization Thresholds ───────────────────────────────────
MIN_ROAS_THRESHOLD = float(os.getenv("MIN_ROAS_THRESHOLD", "1.5"))
SCALE_ROAS_THRESHOLD = 3.0
MAX_CPA_THRESHOLD = float(os.getenv("MAX_CPA_THRESHOLD", "25.0"))
SCALE_CPA_THRESHOLD = 15.0
MIN_CTR_THRESHOLD = 0.5          # percent
MAX_FREQUENCY = float(os.getenv("MAX_FREQUENCY", "4.0"))
SPEND_SPIKE_MULTIPLIER = 2.0
MIN_SPEND_FOR_ROAS_EVAL = 50.0   # USD
MIN_ADSET_BUDGET_CENTS = 500     # $5.00 floor
MAX_ADSET_BUDGET_MULTIPLIER = 5.0
BUDGET_INCREASE_PCT = 15
BUDGET_DECREASE_PCT = 20
ROAS_EVAL_CONSECUTIVE_DAYS = 3

# ── Reporting ─────────────────────────────────────────────────
DEFAULT_DATE_RANGE = "last_7d"
REPORT_FORMATS = ["table", "csv", "json"]

# ── Monitoring ────────────────────────────────────────────────
DEFAULT_MONITOR_INTERVAL_MINUTES = 60
INSIGHTS_SYNC_INTERVAL_HOURS = 6

# ── Meta Campaign Objectives ──────────────────────────────────
OBJECTIVES = [
    "OUTCOME_TRAFFIC",
    "OUTCOME_LEADS",
    "OUTCOME_SALES",
    "OUTCOME_AWARENESS",
    "OUTCOME_ENGAGEMENT",
    "OUTCOME_APP_PROMOTION",
]

# ── CTA Options ───────────────────────────────────────────────
CTA_OPTIONS = [
    "LEARN_MORE", "SHOP_NOW", "SIGN_UP", "GET_QUOTE",
    "BOOK_TRAVEL", "DOWNLOAD", "CONTACT_US", "APPLY_NOW",
    "SUBSCRIBE", "WATCH_MORE",
]

# ── Ad Copy Tones ─────────────────────────────────────────────
COPY_TONES = ["professional", "casual", "urgent", "emotional", "humorous"]

# ── Insights Fields ───────────────────────────────────────────
INSIGHTS_FIELDS = [
    "impressions", "reach", "clicks", "spend", "ctr", "cpc",
    "cpm", "cpp", "frequency", "actions", "cost_per_action_type",
    "date_start", "date_stop",
]

DATE_PRESETS = [
    "today", "yesterday", "last_7d", "last_30d",
    "last_90d", "this_month", "last_month",
]
