import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

DB_PATH = os.getenv("DB_PATH", "meta_ads.db")
DB_FULL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), DB_PATH)


def get_conn():
    conn = sqlite3.connect(DB_FULL_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def q(sql: str, params=()) -> pd.DataFrame:
    try:
        conn = get_conn()
        df = pd.read_sql_query(sql, conn, params=params)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()


# ── Campaigns ─────────────────────────────────────────────────

def get_campaigns(status=None) -> pd.DataFrame:
    if status:
        return q("SELECT * FROM campaigns WHERE status=? ORDER BY created_at DESC", (status,))
    return q("SELECT * FROM campaigns ORDER BY created_at DESC")


def get_campaign(campaign_id: str) -> pd.DataFrame:
    return q("SELECT * FROM campaigns WHERE id=?", (campaign_id,))


# ── AdSets ────────────────────────────────────────────────────

def get_adsets(campaign_id=None) -> pd.DataFrame:
    if campaign_id:
        return q("SELECT * FROM adsets WHERE campaign_id=? ORDER BY created_at DESC", (campaign_id,))
    return q("SELECT * FROM adsets ORDER BY created_at DESC")


# ── Ads ───────────────────────────────────────────────────────

def get_ads(adset_id=None, campaign_id=None) -> pd.DataFrame:
    if adset_id:
        return q("SELECT * FROM ads WHERE adset_id=?", (adset_id,))
    if campaign_id:
        return q("SELECT * FROM ads WHERE campaign_id=?", (campaign_id,))
    return q("SELECT * FROM ads ORDER BY created_at DESC")


# ── Insights ──────────────────────────────────────────────────

def get_insights(entity_type="campaign", entity_id=None, days=30) -> pd.DataFrame:
    if entity_id:
        return q("""
            SELECT * FROM insights
            WHERE entity_type=? AND entity_id=?
            ORDER BY date_start DESC LIMIT ?
        """, (entity_type, entity_id, days))
    return q("""
        SELECT * FROM insights WHERE entity_type=?
        ORDER BY date_start DESC LIMIT ?
    """, (entity_type, days))


def get_account_totals() -> dict:
    df = q("SELECT SUM(spend) as spend, SUM(impressions) as impressions, SUM(clicks) as clicks, SUM(leads) as leads, SUM(purchases) as purchases FROM insights WHERE entity_type='campaign'")
    if df.empty:
        return {}
    row = df.iloc[0]
    spend   = float(row.get("spend", 0) or 0)
    clicks  = int(row.get("clicks", 0) or 0)
    impr    = int(row.get("impressions", 0) or 0)
    return {
        "total_spend":       round(spend, 2),
        "total_impressions": impr,
        "total_clicks":      clicks,
        "total_leads":       int(row.get("leads", 0) or 0),
        "total_purchases":   int(row.get("purchases", 0) or 0),
        "avg_ctr":           round(clicks / impr * 100, 2) if impr else 0,
    }


def get_spend_over_time(campaign_id=None) -> pd.DataFrame:
    if campaign_id:
        return q("""
            SELECT date_start as date, SUM(spend) as spend, SUM(clicks) as clicks,
                   SUM(impressions) as impressions, AVG(roas) as roas, AVG(ctr) as ctr
            FROM insights WHERE entity_type='campaign' AND entity_id=?
            GROUP BY date_start ORDER BY date_start
        """, (campaign_id,))
    return q("""
        SELECT date_start as date, SUM(spend) as spend, SUM(clicks) as clicks,
               SUM(impressions) as impressions, AVG(roas) as roas, AVG(ctr) as ctr
        FROM insights WHERE entity_type='campaign'
        GROUP BY date_start ORDER BY date_start
    """)


def get_campaign_performance() -> pd.DataFrame:
    return q("""
        SELECT c.id, c.name, c.status, c.objective,
               c.daily_budget,
               COALESCE(SUM(i.spend), 0) as total_spend,
               COALESCE(SUM(i.impressions), 0) as impressions,
               COALESCE(SUM(i.clicks), 0) as clicks,
               COALESCE(SUM(i.leads), 0) as leads,
               COALESCE(AVG(i.roas), 0) as avg_roas,
               COALESCE(AVG(i.ctr), 0) as avg_ctr,
               COALESCE(AVG(i.cpc), 0) as avg_cpc
        FROM campaigns c
        LEFT JOIN insights i ON i.entity_id = c.id AND i.entity_type='campaign'
        GROUP BY c.id ORDER BY total_spend DESC
    """)


# ── Alerts ────────────────────────────────────────────────────

def get_alerts(limit=50) -> pd.DataFrame:
    return q("SELECT * FROM alerts ORDER BY created_at DESC LIMIT ?", (limit,))


def get_alert_counts() -> dict:
    df = q("SELECT alert_type, COUNT(*) as cnt FROM alerts GROUP BY alert_type")
    if df.empty:
        return {}
    return dict(zip(df["alert_type"], df["cnt"]))


# ── Optimization Log ──────────────────────────────────────────

def get_optimization_log(limit=100) -> pd.DataFrame:
    return q("SELECT * FROM optimization_log ORDER BY executed_at DESC LIMIT ?", (limit,))


# ── Copy ──────────────────────────────────────────────────────

def get_copy(limit=50) -> pd.DataFrame:
    return q("SELECT * FROM generated_copy ORDER BY created_at DESC LIMIT ?", (limit,))


# ── Stats ─────────────────────────────────────────────────────

def get_stats() -> dict:
    conn = get_conn()
    stats = {}
    tables = ["campaigns", "adsets", "ads", "insights", "generated_copy", "alerts", "optimization_log"]
    for t in tables:
        try:
            stats[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except Exception:
            stats[t] = 0
    try:
        stats["active_campaigns"] = conn.execute("SELECT COUNT(*) FROM campaigns WHERE status='ACTIVE'").fetchone()[0]
    except Exception:
        stats["active_campaigns"] = 0
    conn.close()
    return stats


# ── Settings ──────────────────────────────────────────────────

def get_setting(key: str, default=None):
    try:
        df = q("SELECT value FROM settings WHERE key=?", (key,))
        return df.iloc[0]["value"] if not df.empty else default
    except Exception:
        return default


def set_setting(key: str, value: str):
    try:
        conn = get_conn()
        conn.execute("""
            INSERT INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        """, (key, str(value)))
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_all_settings() -> dict:
    try:
        df = q("SELECT key, value FROM settings")
        return dict(zip(df["key"], df["value"])) if not df.empty else {}
    except Exception:
        return {}


# ── Report Schedules ──────────────────────────────────────────

def get_schedules() -> pd.DataFrame:
    return q("SELECT * FROM report_schedules WHERE active=1 ORDER BY created_at DESC")


def save_schedule(email: str, frequency: str):
    try:
        conn = get_conn()
        conn.execute("INSERT INTO report_schedules (email, frequency) VALUES (?,?)", (email, frequency))
        conn.commit()
        conn.close()
    except Exception:
        pass


def delete_schedule(schedule_id: int):
    try:
        conn = get_conn()
        conn.execute("UPDATE report_schedules SET active=0 WHERE id=?", (schedule_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass


# ── Accounts ──────────────────────────────────────────────────

def get_accounts() -> pd.DataFrame:
    return q("SELECT * FROM accounts ORDER BY is_active DESC, name")


def save_account(name: str, account_id: str, access_token: str = ""):
    try:
        conn = get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO accounts (name, account_id, access_token) VALUES (?,?,?)",
            (name, account_id, access_token)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def set_active_account(account_id: str):
    try:
        conn = get_conn()
        conn.execute("UPDATE accounts SET is_active=0")
        conn.execute("UPDATE accounts SET is_active=1 WHERE account_id=?", (account_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass


def delete_account(account_id: str):
    try:
        conn = get_conn()
        conn.execute("DELETE FROM accounts WHERE account_id=?", (account_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass


# ── Ad-level performance ──────────────────────────────────────

def get_ad_performance() -> pd.DataFrame:
    return q("""
        SELECT a.id, a.name, a.status, a.headline, a.body, a.cta,
               a.campaign_id, a.adset_id,
               COALESCE(SUM(i.spend),0)       as total_spend,
               COALESCE(SUM(i.impressions),0) as impressions,
               COALESCE(SUM(i.clicks),0)      as clicks,
               COALESCE(SUM(i.leads),0)       as leads,
               COALESCE(AVG(i.ctr),0)         as avg_ctr,
               COALESCE(AVG(i.cpc),0)         as avg_cpc,
               COALESCE(AVG(i.roas),0)        as avg_roas,
               COALESCE(AVG(i.frequency),0)   as avg_frequency
        FROM ads a
        LEFT JOIN insights i ON i.entity_id = a.id AND i.entity_type='ad'
        GROUP BY a.id ORDER BY total_spend DESC
    """)
