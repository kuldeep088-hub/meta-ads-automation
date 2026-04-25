# Meta Ads Automation

A Python CLI tool and Streamlit dashboard for automating Facebook/Instagram ad management via the Meta Marketing API. Includes AI-powered ad copy generation, budget optimization, performance reporting, and real-time alerts.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red) ![Meta API](https://img.shields.io/badge/Meta%20Marketing%20API-v20-blue) ![Claude AI](https://img.shields.io/badge/Claude%20AI-Sonnet-purple)

---

## Features

- **Campaign Management** — Create, pause, resume, and delete campaigns, ad sets, and ads from the terminal
- **Budget Optimizer** — Rules-based engine that automatically increases, decreases, or pauses ad sets based on ROAS, CPA, CTR, and frequency thresholds
- **AI Ad Copy** — Generate headline, body, hook, and CTA variations using Claude AI (Anthropic)
- **Performance Reports** — Pull insights from Meta API, view colored tables in terminal, export to CSV / JSON / PDF / Excel
- **Alert System** — Detects spend spikes, budget depletion, low ROAS, high CPA, and frequency fatigue — sends email alerts for critical events
- **Streamlit Dashboard** — 8-page client reporting portal with charts, anomaly detection, health scores, and white-label branding
- **Multi-Account** — Manage and switch between multiple Meta ad accounts
- **Email Scheduler** — Automated report delivery (daily / weekly / monthly) via SMTP

---

## Project Structure

```
meta-ads-automation/
├── main.py                     # CLI entry point
├── config.py                   # Constants and thresholds
├── requirements.txt
├── .env.example                # Credential template
├── setup.bat                   # Windows quick-start installer
├── run_dashboard.bat           # Launch dashboard
│
├── api/                        # Meta Marketing API wrappers
│   ├── client.py               # API init singleton
│   ├── campaigns.py
│   ├── adsets.py
│   ├── ads.py
│   └── insights.py
│
├── campaigns/
│   ├── creator.py              # Campaign → AdSet → Ad orchestration
│   ├── optimizer.py            # BudgetOptimizer rules engine
│   └── validator.py
│
├── creative/
│   ├── copy_generator.py       # Claude AI copy generation
│   └── prompts/                # System prompt templates
│
├── monitor/
│   ├── alert_engine.py         # Threshold evaluator
│   └── scheduler.py            # Polling loop (schedule library)
│
├── reporting/
│   ├── collector.py            # Fetch & save insights
│   ├── formatter.py            # Colored terminal output
│   ├── exporter.py             # CSV / JSON
│   ├── pdf_exporter.py         # PDF reports (fpdf2)
│   └── excel_exporter.py       # Excel workbooks (openpyxl)
│
├── database/
│   └── db.py                   # SQLite schema + CRUD helpers
│
├── utils/
│   ├── logger.py
│   ├── helpers.py
│   └── mailer.py               # SMTP email alerts
│
├── dashboard/                  # Streamlit app
│   ├── app.py                  # Home page
│   ├── auth.py                 # Login
│   ├── data.py                 # DB query layer
│   ├── charts.py               # Plotly chart builders
│   ├── styles.py               # Global CSS + components
│   ├── health.py               # Campaign health score
│   ├── anomaly.py              # Anomaly detection
│   └── pages/
│       ├── 1_Overview.py
│       ├── 2_Campaigns.py
│       ├── 3_Reports.py
│       ├── 4_Alerts.py
│       ├── 5_Optimization.py
│       ├── 6_Ad_Copy.py
│       ├── 7_Creatives.py
│       └── 8_Settings.py
│
└── scripts/
    └── seed_test_data.py       # Populate DB with test data
```

---

## Setup

### 1. Clone & install

```bash
git clone https://github.com/kuldeep088-hub/meta-ads-automation.git
cd meta-ads-automation
pip install -r requirements.txt
```

Or on Windows, double-click `setup.bat`.

### 2. Configure credentials

```bash
cp .env.example .env
```

Edit `.env` with your keys:

```ini
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_ACCESS_TOKEN=your_long_lived_token
META_AD_ACCOUNT_ID=your_account_id_numeric
META_PAGE_ID=your_facebook_page_id

ANTHROPIC_API_KEY=sk-ant-your_key_here

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASS=your_app_password
ALERT_EMAIL=alerts@yourdomain.com
```

### 3. Verify connection

```bash
python main.py setup verify
```

---

## CLI Usage

```
python main.py <command> [action] [flags]
```

### Campaigns

```bash
python main.py campaign create --name "Summer Sale" --objective OUTCOME_TRAFFIC --budget 50 --dry-run
python main.py campaign list --status ACTIVE
python main.py campaign pause --id 123456789
python main.py campaign resume --id 123456789
```

### Ad Sets & Ads

```bash
python main.py adset create --campaign-id 123 --name "18-35 Women" --budget 20
python main.py ad create --adset-id 456 --headline "Save 40% Today" --body "..." --cta SHOP_NOW
```

### Optimizer

```bash
python main.py optimize --dry-run          # preview actions
python main.py optimize                    # execute live
```

### Reports

```bash
python main.py report --date-range last_7d --format table
python main.py report --date-range last_30d --format csv --output report.csv
python main.py report account --date-range this_month
```

### AI Copy Generation

```bash
python main.py copy generate \
  --product "Personal Loan" \
  --audience "Salaried professionals 25-40" \
  --tone casual \
  --count 3
```

### Monitor & Alerts

```bash
python main.py monitor start --interval 60 --alert-email you@example.com
python main.py monitor check --campaign-id 123456789
```

### Stats

```bash
python main.py stats
```

---

## Dashboard

```bash
streamlit run dashboard/app.py
# or double-click run_dashboard.bat
```

Open **http://localhost:8501** — default password: `admin123` (set `DASHBOARD_PASSWORD` in `.env` to change).

| Page | Description |
|---|---|
| Home | Account overview, KPIs, quick charts, alert feed |
| Overview | Date-filtered metrics, goal progress, anomaly callouts |
| Campaigns | Per-campaign health score, charts, ad set breakdown |
| Reports | PDF / Excel / CSV export with date range selector |
| Alerts | Alert feed with severity levels and filtering |
| Optimization | Budget action log with live vs dry-run toggle |
| Ad Copy | AI-generated copy cards with search and filter |
| Creatives | Ad-level CTR / ROAS comparison and scatter analysis |
| Settings | Branding, performance targets, email scheduler, accounts |

---

## Budget Optimization Rules

| Rule | Condition | Action |
|---|---|---|
| ROAS Guard | ROAS < 1.5 AND spend > $50 for 3 days | Pause ad set |
| CPA Guard | CPL > $25 AND leads ≥ 3 | Decrease budget 20% |
| High Performer | ROAS ≥ 3.0 AND CPA ≤ $10.50 | Increase budget 15% |
| Low CTR | CTR < 0.5% AND impressions > 5,000 | Alert |
| Frequency Fatigue | Frequency > 4.0 AND running > 7 days | Alert + optional pause |
| Budget Depleted | Remaining budget = 0 before 18:00 | Critical alert |
| Spend Spike | Today's spend > 7-day avg × 2.0 | Critical alert + email |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Meta API | `facebook-business` SDK v20 |
| AI Copy | Anthropic Claude (`claude-sonnet-4-6`) |
| Dashboard | Streamlit + Plotly |
| Database | SQLite via `database/db.py` |
| PDF Export | fpdf2 |
| Excel Export | openpyxl |
| Scheduling | `schedule` library |
| Email | smtplib + SSL |
| CLI | argparse + colorama + rich |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `META_APP_ID` | Yes | Meta App ID |
| `META_APP_SECRET` | Yes | Meta App Secret |
| `META_ACCESS_TOKEN` | Yes | Long-lived user access token |
| `META_AD_ACCOUNT_ID` | Yes | Ad account ID (numeric, no `act_` prefix) |
| `META_PAGE_ID` | Yes | Facebook Page ID |
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `DASHBOARD_PASSWORD` | No | Dashboard login password (default: `admin123`) |
| `SMTP_HOST` | No | SMTP server for email alerts |
| `SMTP_PORT` | No | SMTP port (default: 587) |
| `SMTP_USER` | No | SMTP username |
| `SMTP_PASS` | No | SMTP password / app password |
| `ALERT_EMAIL` | No | Recipient for critical alerts |
| `DB_PATH` | No | SQLite path (default: `meta_ads.db`) |

---

## License

MIT
