"""
Seed test data into local DB without making any Meta API calls.
Run: python scripts/seed_test_data.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db, upsert_campaign, upsert_adset, upsert_ad, save_insights, save_copy
from utils.helpers import usd_to_cents

init_db()

# Campaigns
upsert_campaign({"id": "123456789", "name": "Summer Sale 2025", "objective": "OUTCOME_TRAFFIC",
                  "status": "ACTIVE", "daily_budget": usd_to_cents(50.0)})
upsert_campaign({"id": "987654321", "name": "Lead Gen - Q2", "objective": "OUTCOME_LEADS",
                  "status": "ACTIVE", "daily_budget": usd_to_cents(100.0)})

# AdSets
upsert_adset({"id": "adset_001", "campaign_id": "123456789", "name": "Summer Sale  -  US 25-45",
               "status": "ACTIVE", "daily_budget": usd_to_cents(50.0), "optimization_goal": "LINK_CLICKS"})
upsert_adset({"id": "adset_002", "campaign_id": "987654321", "name": "Lead Gen  -  Lookalike 2%",
               "status": "ACTIVE", "daily_budget": usd_to_cents(100.0), "optimization_goal": "LEAD_GENERATION"})

# Ads
upsert_ad({"id": "ad_001", "adset_id": "adset_001", "campaign_id": "123456789",
            "name": "Summer Ad 1", "status": "ACTIVE", "headline": "Summer Sale  -  Up to 50% Off",
            "body": "Don't miss our biggest sale of the year. Shop now!", "cta": "SHOP_NOW",
            "destination_url": "https://example.com/sale"})

# Insights (7 days of data)
for day in range(1, 8):
    save_insights("campaign", "123456789", {
        "date_start": f"2025-04-{day:02d}", "date_stop": f"2025-04-{day:02d}",
        "impressions": 5000 + day * 200, "reach": 4500 + day * 180,
        "clicks": 150 + day * 10, "spend": 45.0 + day * 1.5,
        "ctr": 2.8 + day * 0.1, "cpc": 0.30, "cpm": 9.0, "cpp": 10.0,
        "roas": 2.5 + day * 0.2, "frequency": 1.1 + day * 0.05,
        "leads": day * 3, "purchases": day,
        "cost_per_lead": 5.0, "cost_per_purchase": 45.0,
    })
    save_insights("adset", "adset_001", {
        "date_start": f"2025-04-{day:02d}", "date_stop": f"2025-04-{day:02d}",
        "impressions": 5000 + day * 200, "reach": 4500, "clicks": 150 + day * 10,
        "spend": 45.0 + day * 1.5, "ctr": 2.8, "cpc": 0.30,
        "cpm": 9.0, "cpp": 10.0, "roas": 2.5, "frequency": 1.1,
        "leads": day * 3, "purchases": day, "cost_per_lead": 5.0, "cost_per_purchase": 45.0,
    })

# Sample copy
save_copy({"product": "Running Shoes", "audience": "Fitness enthusiasts 25-40",
            "tone": "energetic", "objective": "sales",
            "headline": "Run Faster. Feel Better.", "body": "Pro-grade running shoes for serious athletes. Free shipping on orders over $50.",
            "cta": "SHOP_NOW", "hook": "Run Faster.", "compliance_note": ""})

print("Test data seeded successfully.")
print("Run: python main.py stats")
print("Run: python main.py campaign list")
print("Run: python main.py report --campaign-id 123456789 --format table")
