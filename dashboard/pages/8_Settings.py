import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dashboard.auth import check_login, login_page
from dashboard import data, styles

if not check_login():
    login_page()
    st.stop()

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
settings    = data.get_all_settings()
brand_color = settings.get("brand_color", "#1877F2")
styles.inject(brand_color=brand_color)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
LOGO_PATH  = os.path.join(STATIC_DIR, "logo.png")

styles.hero("Settings", "White-label branding, performance goals, accounts & report scheduling")

# ─────────────────────────────────────────────────────────────
# TAB LAYOUT
# ─────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🎨 Branding", "🎯 Goals & Targets", "📧 Report Scheduler", "🏢 Accounts"])

# ══════════════ TAB 1: BRANDING ══════════════════════════════
with tab1:
    styles.sec("🎨","White-Label Branding")
    b1, b2 = st.columns([2, 1])

    with b1:
        st.markdown("**Brand Name**")
        new_brand = st.text_input("Brand name shown in header & reports",
                                  value=settings.get("brand_name","Meta Ads"),
                                  placeholder="Your Company Name")

        st.markdown("**Brand Color**")
        st.caption("This color replaces Meta blue across the entire dashboard.")
        new_color = st.color_picker("Primary brand color", value=settings.get("brand_color","#1877F2"))

        st.markdown("**Logo**")
        st.caption("Upload PNG/JPG logo. Shown in the hero banner and PDF reports (recommended: 200×50px).")
        uploaded = st.file_uploader("Upload logo", type=["png","jpg","jpeg"], label_visibility="collapsed")
        if uploaded:
            with open(LOGO_PATH, "wb") as f:
                f.write(uploaded.read())
            st.success("Logo saved.")

        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=180, caption="Current logo")
            if st.button("Remove Logo", type="secondary"):
                os.remove(LOGO_PATH)
                st.success("Logo removed.")
                st.rerun()

        if st.button("💾 Save Branding", type="primary", use_container_width=True):
            data.set_setting("brand_name",  new_brand.strip() or "Meta Ads")
            data.set_setting("brand_color", new_color)
            st.success("Branding saved! Refresh the page to see changes.")
            st.rerun()

    with b2:
        st.markdown("**Live Preview**")
        preview_name  = new_brand or "Your Brand"
        preview_color = new_color
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,{preview_color},#0D47A1);
                    border-radius:14px;padding:22px 20px;color:#fff;text-align:center;
                    box-shadow:0 8px 24px rgba(0,0,0,0.25)">
          <div style="font-size:20px;font-weight:900">{preview_name}</div>
          <div style="font-size:12px;opacity:.8;margin-top:4px">Client Reporting Portal</div>
          <div style="display:flex;gap:8px;justify-content:center;margin-top:14px;flex-wrap:wrap">
            <span style="background:rgba(255,255,255,0.18);padding:3px 12px;border-radius:16px;font-size:11px;font-weight:700">🟢 5 Active</span>
            <span style="background:rgba(255,255,255,0.18);padding:3px 12px;border-radius:16px;font-size:11px;font-weight:700">₹1,24,000 Spent</span>
          </div>
        </div>
        <div style="margin-top:14px;display:grid;grid-template-columns:1fr 1fr;gap:10px">
          <div style="background:#fff;border-radius:12px;padding:14px;text-align:center;
                      border-top:4px solid {preview_color};box-shadow:0 2px 8px rgba(0,0,0,0.07)">
            <div style="font-size:10px;font-weight:700;color:#9EA3A9;text-transform:uppercase">Total Spend</div>
            <div style="font-size:18px;font-weight:900;color:#1C1E21">₹1,24,000</div>
          </div>
          <div style="background:#fff;border-radius:12px;padding:14px;text-align:center;
                      border-top:4px solid {preview_color};box-shadow:0 2px 8px rgba(0,0,0,0.07)">
            <div style="font-size:10px;font-weight:700;color:#9EA3A9;text-transform:uppercase">Avg ROAS</div>
            <div style="font-size:18px;font-weight:900;color:#1C1E21">2.8x</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════ TAB 2: GOALS ═════════════════════════════════
with tab2:
    styles.sec("🎯","Performance Targets")
    g1, g2, g3, g4, g5 = st.columns(5)

    with g1:
        t_roas = st.number_input("Target ROAS", min_value=0.0, max_value=20.0, step=0.1,
                                  value=float(settings.get("target_roas", 3.0)),
                                  help="Minimum acceptable Return on Ad Spend")
    with g2:
        t_cpl = st.number_input("Target CPL (₹)", min_value=0.0, max_value=10000.0, step=10.0,
                                  value=float(settings.get("target_cpl", 25.0)),
                                  help="Maximum acceptable cost per lead")
    with g3:
        t_budget = st.number_input("Monthly Budget (₹)", min_value=0.0, max_value=10000000.0, step=1000.0,
                                    value=float(settings.get("target_monthly_budget", 0) or 0),
                                    help="Total monthly budget shown on Overview")
    with g4:
        t_ctr = st.number_input("Min CTR (%)", min_value=0.0, max_value=10.0, step=0.1,
                                 value=float(settings.get("target_ctr", 1.5)),
                                 help="Alert threshold for CTR")
    with g5:
        t_freq = st.number_input("Max Frequency", min_value=1.0, max_value=10.0, step=0.5,
                                  value=float(settings.get("target_max_frequency", 4.0)),
                                  help="Alert when ad frequency exceeds this")

    st.markdown("")
    if st.button("💾 Save Targets", type="primary", use_container_width=False):
        data.set_setting("target_roas",             str(t_roas))
        data.set_setting("target_cpl",              str(t_cpl))
        data.set_setting("target_monthly_budget",   str(t_budget))
        data.set_setting("target_ctr",              str(t_ctr))
        data.set_setting("target_max_frequency",    str(t_freq))
        st.success("Targets saved! Overview page will reflect updated goals.")

    # Current target preview
    st.divider()
    styles.sec("📊","Current Targets Preview")
    p1,p2,p3,p4,p5 = st.columns(5)
    p1.metric("Target ROAS",       f"{t_roas:.1f}x")
    p2.metric("Target CPL",        f"₹{t_cpl:,.0f}")
    p3.metric("Monthly Budget",    f"₹{t_budget:,.0f}")
    p4.metric("Min CTR",           f"{t_ctr:.1f}%")
    p5.metric("Max Frequency",     f"{t_freq:.1f}x")

# ══════════════ TAB 3: SCHEDULER ═════════════════════════════
with tab3:
    styles.sec("📧","Email Report Scheduler")
    st.caption("Add email addresses to receive automated performance reports. The monitor scheduler sends reports on your chosen frequency.")

    e1, e2, e3 = st.columns([3, 2, 1])
    with e1:
        new_email = st.text_input("Email address", placeholder="client@example.com")
    with e2:
        new_freq  = st.selectbox("Frequency", ["daily","weekly","monthly"])
    with e3:
        st.markdown('<div style="height:1.75rem"></div>', unsafe_allow_html=True)
        if st.button("➕ Add", use_container_width=True, type="primary"):
            if new_email and "@" in new_email:
                data.save_schedule(new_email.strip(), new_freq)
                st.success(f"Added {new_email} ({new_freq})")
                st.rerun()
            else:
                st.error("Please enter a valid email address.")

    # Show existing schedules
    schedules_df = data.get_schedules()
    if not schedules_df.empty:
        st.markdown("")
        styles.sec("📋","Active Schedules")
        for _, row in schedules_df.iterrows():
            r1, r2, r3, r4 = st.columns([3, 2, 2, 1])
            r1.markdown(f"**{row.get('email','')}**")
            r2.markdown(f"🔄 {row.get('frequency','').title()}")
            last = str(row.get("last_sent_at",""))[:16] or "Never sent"
            r3.caption(f"Last sent: {last}")
            with r4:
                if st.button("🗑️", key=f"del_{row['id']}", help="Remove this schedule"):
                    data.delete_schedule(int(row["id"]))
                    st.rerun()
    else:
        st.info("No email schedules yet. Add one above.")

    st.divider()
    st.markdown("""
    **How it works:**
    - The monitor scheduler (`python main.py monitor start`) checks for pending reports every hour
    - Reports are sent via the SMTP settings in your `.env` file
    - Configure: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` in `.env`
    """)

# ══════════════ TAB 4: ACCOUNTS ══════════════════════════════
with tab4:
    styles.sec("🏢","Ad Account Manager")
    st.caption("Manage multiple Meta ad accounts. Switch between them using the sidebar dropdown.")

    a1, a2, a3, a4 = st.columns([2, 2, 2, 1])
    with a1:
        acct_name = st.text_input("Account Name", placeholder="Client Brand A")
    with a2:
        acct_id   = st.text_input("Account ID (numeric)", placeholder="1234567890")
    with a3:
        acct_token = st.text_input("Access Token (optional)", type="password", placeholder="Leave blank to use .env token")
    with a4:
        st.markdown('<div style="height:1.75rem"></div>', unsafe_allow_html=True)
        if st.button("➕ Add", use_container_width=True, type="primary", key="add_acct"):
            if acct_name and acct_id:
                data.save_account(acct_name.strip(), acct_id.strip(), acct_token.strip())
                st.success(f"Account '{acct_name}' added.")
                st.rerun()
            else:
                st.error("Name and Account ID are required.")

    accounts_df = data.get_accounts()
    if not accounts_df.empty:
        st.markdown("")
        styles.sec("📋","Saved Accounts")
        for _, row in accounts_df.iterrows():
            is_active = row.get("is_active", 0)
            rc1, rc2, rc3, rc4 = st.columns([3, 3, 1, 1])
            rc1.markdown(f"{'🟢 ' if is_active else ''} **{row.get('name','')}**")
            rc2.code(row.get("account_id",""), language=None)
            with rc3:
                if not is_active:
                    if st.button("Set Active", key=f"act_{row['id']}"):
                        data.set_active_account(str(row["account_id"]))
                        st.success(f"Switched to {row['name']}")
                        st.rerun()
                else:
                    st.markdown('<span style="color:#2E7D32;font-weight:700;font-size:12px">✓ Active</span>', unsafe_allow_html=True)
            with rc4:
                if not is_active:
                    if st.button("🗑️", key=f"delacc_{row['id']}", help="Remove account"):
                        data.delete_account(str(row["account_id"]))
                        st.rerun()
    else:
        st.info("No accounts saved yet. Your current `.env` account is always used by default.")
        env_id = os.getenv("META_AD_ACCOUNT_ID","")
        if env_id:
            st.markdown(f"**Active from .env:** `{env_id}`")
