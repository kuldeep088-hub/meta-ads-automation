import sqlite3
import json
from datetime import datetime
from typing import Optional

import config

_conn: Optional[sqlite3.Connection] = None


def get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA foreign_keys=ON")
    return _conn


def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS campaigns (
        id              TEXT PRIMARY KEY,
        name            TEXT NOT NULL,
        objective       TEXT,
        status          TEXT DEFAULT 'ACTIVE',
        daily_budget    INTEGER,
        lifetime_budget INTEGER,
        start_time      TEXT,
        stop_time       TEXT,
        created_at      TEXT DEFAULT (datetime('now')),
        updated_at      TEXT DEFAULT (datetime('now')),
        synced_at       TEXT
    );

    CREATE TABLE IF NOT EXISTS adsets (
        id              TEXT PRIMARY KEY,
        campaign_id     TEXT REFERENCES campaigns(id),
        name            TEXT NOT NULL,
        status          TEXT DEFAULT 'ACTIVE',
        daily_budget    INTEGER,
        bid_strategy    TEXT,
        optimization_goal TEXT,
        targeting       TEXT,
        created_at      TEXT DEFAULT (datetime('now')),
        updated_at      TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS ads (
        id              TEXT PRIMARY KEY,
        adset_id        TEXT REFERENCES adsets(id),
        campaign_id     TEXT REFERENCES campaigns(id),
        name            TEXT NOT NULL,
        status          TEXT DEFAULT 'ACTIVE',
        headline        TEXT,
        body            TEXT,
        cta             TEXT,
        image_url       TEXT,
        destination_url TEXT,
        created_at      TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS insights (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type         TEXT NOT NULL,
        entity_id           TEXT NOT NULL,
        date_start          TEXT NOT NULL,
        date_stop           TEXT NOT NULL,
        impressions         INTEGER DEFAULT 0,
        reach               INTEGER DEFAULT 0,
        clicks              INTEGER DEFAULT 0,
        spend               REAL DEFAULT 0.0,
        ctr                 REAL DEFAULT 0.0,
        cpc                 REAL DEFAULT 0.0,
        cpm                 REAL DEFAULT 0.0,
        cpp                 REAL DEFAULT 0.0,
        roas                REAL DEFAULT 0.0,
        frequency           REAL DEFAULT 0.0,
        leads               INTEGER DEFAULT 0,
        purchases           INTEGER DEFAULT 0,
        cost_per_lead       REAL DEFAULT 0.0,
        cost_per_purchase   REAL DEFAULT 0.0,
        fetched_at          TEXT DEFAULT (datetime('now')),
        UNIQUE(entity_type, entity_id, date_start, date_stop)
    );

    CREATE TABLE IF NOT EXISTS generated_copy (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        product         TEXT,
        audience        TEXT,
        tone            TEXT,
        objective       TEXT,
        headline        TEXT NOT NULL,
        body            TEXT NOT NULL,
        cta             TEXT NOT NULL,
        hook            TEXT,
        compliance_note TEXT,
        model           TEXT DEFAULT 'claude-sonnet-4-6',
        used_in_ad_id   TEXT,
        created_at      TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS alerts (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        campaign_id     TEXT,
        adset_id        TEXT,
        alert_type      TEXT NOT NULL,
        threshold_value REAL,
        actual_value    REAL,
        message         TEXT,
        email_sent      INTEGER DEFAULT 0,
        created_at      TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS optimization_log (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type     TEXT,
        entity_id       TEXT,
        action          TEXT NOT NULL,
        old_value       REAL,
        new_value       REAL,
        reason          TEXT,
        rule_triggered  TEXT,
        dry_run         INTEGER DEFAULT 0,
        executed_at     TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS settings (
        key         TEXT PRIMARY KEY,
        value       TEXT,
        updated_at  TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS report_schedules (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        email        TEXT NOT NULL,
        frequency    TEXT NOT NULL DEFAULT 'weekly',
        active       INTEGER DEFAULT 1,
        last_sent_at TEXT,
        created_at   TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS accounts (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        name         TEXT NOT NULL,
        account_id   TEXT NOT NULL UNIQUE,
        access_token TEXT,
        is_active    INTEGER DEFAULT 0,
        created_at   TEXT DEFAULT (datetime('now'))
    );
    """)
    conn.commit()


# ── Campaigns ─────────────────────────────────────────────────

def upsert_campaign(data: dict) -> str:
    conn = get_conn()
    now = datetime.utcnow().isoformat()
    conn.execute("""
        INSERT INTO campaigns (id, name, objective, status, daily_budget, lifetime_budget,
                               start_time, stop_time, updated_at, synced_at)
        VALUES (:id, :name, :objective, :status, :daily_budget, :lifetime_budget,
                :start_time, :stop_time, :updated_at, :synced_at)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name, objective=excluded.objective, status=excluded.status,
            daily_budget=excluded.daily_budget, lifetime_budget=excluded.lifetime_budget,
            start_time=excluded.start_time, stop_time=excluded.stop_time,
            updated_at=excluded.updated_at, synced_at=excluded.synced_at
    """, {**data, "updated_at": now, "synced_at": now,
          "objective": data.get("objective"), "daily_budget": data.get("daily_budget"),
          "lifetime_budget": data.get("lifetime_budget"), "start_time": data.get("start_time"),
          "stop_time": data.get("stop_time")})
    conn.commit()
    return data["id"]


def get_campaign(campaign_id: str) -> Optional[dict]:
    row = get_conn().execute("SELECT * FROM campaigns WHERE id=?", (campaign_id,)).fetchone()
    return dict(row) if row else None


def get_campaigns(status: str = None, limit: int = 100) -> list:
    if status:
        rows = get_conn().execute(
            "SELECT * FROM campaigns WHERE status=? ORDER BY created_at DESC LIMIT ?",
            (status.upper(), limit)
        ).fetchall()
    else:
        rows = get_conn().execute(
            "SELECT * FROM campaigns ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def update_campaign(campaign_id: str, **kwargs):
    kwargs["updated_at"] = datetime.utcnow().isoformat()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [campaign_id]
    get_conn().execute(f"UPDATE campaigns SET {sets} WHERE id=?", vals)
    get_conn().commit()


# ── AdSets ────────────────────────────────────────────────────

def upsert_adset(data: dict) -> str:
    conn = get_conn()
    now = datetime.utcnow().isoformat()
    targeting = json.dumps(data.get("targeting", {})) if isinstance(data.get("targeting"), dict) else data.get("targeting", "")
    conn.execute("""
        INSERT INTO adsets (id, campaign_id, name, status, daily_budget,
                            bid_strategy, optimization_goal, targeting, updated_at)
        VALUES (:id, :campaign_id, :name, :status, :daily_budget,
                :bid_strategy, :optimization_goal, :targeting, :updated_at)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name, status=excluded.status,
            daily_budget=excluded.daily_budget, bid_strategy=excluded.bid_strategy,
            optimization_goal=excluded.optimization_goal, targeting=excluded.targeting,
            updated_at=excluded.updated_at
    """, {**data, "targeting": targeting, "updated_at": now,
          "bid_strategy": data.get("bid_strategy"),
          "optimization_goal": data.get("optimization_goal")})
    conn.commit()
    return data["id"]


def get_adsets(campaign_id: str = None) -> list:
    if campaign_id:
        rows = get_conn().execute(
            "SELECT * FROM adsets WHERE campaign_id=? ORDER BY created_at DESC", (campaign_id,)
        ).fetchall()
    else:
        rows = get_conn().execute("SELECT * FROM adsets ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def update_adset(adset_id: str, **kwargs):
    kwargs["updated_at"] = datetime.utcnow().isoformat()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [adset_id]
    get_conn().execute(f"UPDATE adsets SET {sets} WHERE id=?", vals)
    get_conn().commit()


# ── Ads ───────────────────────────────────────────────────────

def upsert_ad(data: dict) -> str:
    conn = get_conn()
    conn.execute("""
        INSERT INTO ads (id, adset_id, campaign_id, name, status, headline,
                         body, cta, image_url, destination_url)
        VALUES (:id, :adset_id, :campaign_id, :name, :status, :headline,
                :body, :cta, :image_url, :destination_url)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name, status=excluded.status,
            headline=excluded.headline, body=excluded.body, cta=excluded.cta,
            image_url=excluded.image_url, destination_url=excluded.destination_url
    """, {**data, "adset_id": data.get("adset_id"), "campaign_id": data.get("campaign_id"),
          "headline": data.get("headline"), "body": data.get("body"),
          "cta": data.get("cta"), "image_url": data.get("image_url"),
          "destination_url": data.get("destination_url")})
    conn.commit()
    return data["id"]


def get_ads(adset_id: str = None, campaign_id: str = None) -> list:
    if adset_id:
        rows = get_conn().execute(
            "SELECT * FROM ads WHERE adset_id=? ORDER BY created_at DESC", (adset_id,)
        ).fetchall()
    elif campaign_id:
        rows = get_conn().execute(
            "SELECT * FROM ads WHERE campaign_id=? ORDER BY created_at DESC", (campaign_id,)
        ).fetchall()
    else:
        rows = get_conn().execute("SELECT * FROM ads ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


# ── Insights ──────────────────────────────────────────────────

def save_insights(entity_type: str, entity_id: str, data: dict):
    conn = get_conn()
    conn.execute("""
        INSERT INTO insights (entity_type, entity_id, date_start, date_stop,
            impressions, reach, clicks, spend, ctr, cpc, cpm, cpp,
            roas, frequency, leads, purchases, cost_per_lead, cost_per_purchase)
        VALUES (:entity_type, :entity_id, :date_start, :date_stop,
            :impressions, :reach, :clicks, :spend, :ctr, :cpc, :cpm, :cpp,
            :roas, :frequency, :leads, :purchases, :cost_per_lead, :cost_per_purchase)
        ON CONFLICT(entity_type, entity_id, date_start, date_stop) DO UPDATE SET
            impressions=excluded.impressions, reach=excluded.reach,
            clicks=excluded.clicks, spend=excluded.spend, ctr=excluded.ctr,
            cpc=excluded.cpc, cpm=excluded.cpm, cpp=excluded.cpp,
            roas=excluded.roas, frequency=excluded.frequency,
            leads=excluded.leads, purchases=excluded.purchases,
            cost_per_lead=excluded.cost_per_lead,
            cost_per_purchase=excluded.cost_per_purchase,
            fetched_at=datetime('now')
    """, {"entity_type": entity_type, "entity_id": entity_id, **data})
    conn.commit()


def get_insights(entity_type: str, entity_id: str,
                 date_start: str = None, date_stop: str = None) -> list:
    if date_start and date_stop:
        rows = get_conn().execute(
            "SELECT * FROM insights WHERE entity_type=? AND entity_id=? "
            "AND date_start>=? AND date_stop<=? ORDER BY date_start",
            (entity_type, entity_id, date_start, date_stop)
        ).fetchall()
    else:
        rows = get_conn().execute(
            "SELECT * FROM insights WHERE entity_type=? AND entity_id=? ORDER BY date_start DESC LIMIT 30",
            (entity_type, entity_id)
        ).fetchall()
    return [dict(r) for r in rows]


# ── Generated Copy ────────────────────────────────────────────

def save_copy(data: dict) -> int:
    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO generated_copy (product, audience, tone, objective,
            headline, body, cta, hook, compliance_note, model)
        VALUES (:product, :audience, :tone, :objective,
            :headline, :body, :cta, :hook, :compliance_note, :model)
    """, {**data, "product": data.get("product"), "audience": data.get("audience"),
          "tone": data.get("tone"), "objective": data.get("objective"),
          "hook": data.get("hook", ""), "compliance_note": data.get("compliance_note", ""),
          "model": data.get("model", "claude-sonnet-4-6")})
    conn.commit()
    return cur.lastrowid


def get_copy(limit: int = 20) -> list:
    rows = get_conn().execute(
        "SELECT * FROM generated_copy ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


def link_copy_to_ad(copy_id: int, ad_id: str):
    get_conn().execute("UPDATE generated_copy SET used_in_ad_id=? WHERE id=?", (ad_id, copy_id))
    get_conn().commit()


# ── Alerts ────────────────────────────────────────────────────

def save_alert(data: dict) -> int:
    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO alerts (campaign_id, adset_id, alert_type, threshold_value,
                            actual_value, message)
        VALUES (:campaign_id, :adset_id, :alert_type, :threshold_value,
                :actual_value, :message)
    """, {**data, "campaign_id": data.get("campaign_id"), "adset_id": data.get("adset_id"),
          "threshold_value": data.get("threshold_value", 0),
          "actual_value": data.get("actual_value", 0)})
    conn.commit()
    return cur.lastrowid


def get_unresolved_alerts(campaign_id: str = None) -> list:
    if campaign_id:
        rows = get_conn().execute(
            "SELECT * FROM alerts WHERE campaign_id=? ORDER BY created_at DESC LIMIT 50",
            (campaign_id,)
        ).fetchall()
    else:
        rows = get_conn().execute(
            "SELECT * FROM alerts ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
    return [dict(r) for r in rows]


def mark_alert_emailed(alert_id: int):
    get_conn().execute("UPDATE alerts SET email_sent=1 WHERE id=?", (alert_id,))
    get_conn().commit()


# ── Optimization Log ──────────────────────────────────────────

def log_optimization(data: dict) -> int:
    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO optimization_log (entity_type, entity_id, action,
            old_value, new_value, reason, rule_triggered, dry_run)
        VALUES (:entity_type, :entity_id, :action,
            :old_value, :new_value, :reason, :rule_triggered, :dry_run)
    """, {**data, "old_value": data.get("old_value"), "new_value": data.get("new_value"),
          "reason": data.get("reason", ""), "rule_triggered": data.get("rule_triggered", ""),
          "dry_run": int(data.get("dry_run", False))})
    conn.commit()
    return cur.lastrowid


def get_optimization_log(entity_id: str = None, limit: int = 50) -> list:
    if entity_id:
        rows = get_conn().execute(
            "SELECT * FROM optimization_log WHERE entity_id=? ORDER BY executed_at DESC LIMIT ?",
            (entity_id, limit)
        ).fetchall()
    else:
        rows = get_conn().execute(
            "SELECT * FROM optimization_log ORDER BY executed_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── Settings ──────────────────────────────────────────────────

def get_setting(key: str, default=None):
    row = get_conn().execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row[0] if row else default


def set_setting(key: str, value: str):
    get_conn().execute("""
        INSERT INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
    """, (key, str(value)))
    get_conn().commit()


def get_all_settings() -> dict:
    rows = get_conn().execute("SELECT key, value FROM settings").fetchall()
    return {r[0]: r[1] for r in rows}


# ── Report Schedules ──────────────────────────────────────────

def get_schedules() -> list:
    rows = get_conn().execute("SELECT * FROM report_schedules WHERE active=1 ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]


def save_schedule(email: str, frequency: str) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO report_schedules (email, frequency) VALUES (?,?)", (email, frequency)
    )
    conn.commit()
    return cur.lastrowid


def delete_schedule(schedule_id: int):
    get_conn().execute("UPDATE report_schedules SET active=0 WHERE id=?", (schedule_id,))
    get_conn().commit()


def update_schedule_sent(schedule_id: int):
    get_conn().execute(
        "UPDATE report_schedules SET last_sent_at=datetime('now') WHERE id=?", (schedule_id,)
    )
    get_conn().commit()


# ── Accounts ──────────────────────────────────────────────────

def get_accounts() -> list:
    rows = get_conn().execute("SELECT * FROM accounts ORDER BY is_active DESC, name").fetchall()
    return [dict(r) for r in rows]


def save_account(name: str, account_id: str, access_token: str = "") -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT OR REPLACE INTO accounts (name, account_id, access_token) VALUES (?,?,?)",
        (name, account_id, access_token)
    )
    conn.commit()
    return cur.lastrowid


def set_active_account(account_id: str):
    conn = get_conn()
    conn.execute("UPDATE accounts SET is_active=0")
    conn.execute("UPDATE accounts SET is_active=1 WHERE account_id=?", (account_id,))
    conn.commit()


def delete_account(account_id: str):
    get_conn().execute("DELETE FROM accounts WHERE account_id=?", (account_id,))
    get_conn().commit()


# ── Stats ─────────────────────────────────────────────────────

def get_stats() -> dict:
    conn = get_conn()
    return {
        "campaigns":        conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0],
        "active_campaigns": conn.execute("SELECT COUNT(*) FROM campaigns WHERE status='ACTIVE'").fetchone()[0],
        "adsets":           conn.execute("SELECT COUNT(*) FROM adsets").fetchone()[0],
        "ads":              conn.execute("SELECT COUNT(*) FROM ads").fetchone()[0],
        "insights_rows":    conn.execute("SELECT COUNT(*) FROM insights").fetchone()[0],
        "generated_copies": conn.execute("SELECT COUNT(*) FROM generated_copy").fetchone()[0],
        "alerts":           conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0],
        "opt_log_entries":  conn.execute("SELECT COUNT(*) FROM optimization_log").fetchone()[0],
    }
