import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dashboard.auth import check_login, login_page
from dashboard import data, styles

if not check_login():
    login_page()
    st.stop()

st.set_page_config(page_title="Ad Copy", page_icon="✍️", layout="wide")
settings    = data.get_all_settings()
brand_color = settings.get("brand_color", "#1877F2")
styles.inject(brand_color=brand_color)

styles.hero(
    "AI-Generated Ad Copy",
    "Copy variations crafted by Claude AI — headline, body, hook & CTA in one place",
    badges=["&#x270D; Headlines","&#x1F4AC; Body Copy","&#x1F3AF; CTAs","&#x1F4A1; Hooks"]
)

# ── Filters ───────────────────────────────────────────────────
f1, f2, f3 = st.columns([3, 2, 2])
with f1:
    search = st.text_input("Search by product, audience or tone", placeholder="e.g. loan, casual, 25-35...")
with f2:
    show_used = st.selectbox("Filter", ["All","Used in Ads","Unused"])
with f3:
    limit = st.selectbox("Show", [24, 48, 96], index=0)

copy_df = data.get_copy(limit=limit)

if copy_df.empty:
    st.info("No AI-generated copy. Run: `python main.py copy generate --product \"Your Product\" --audience \"Target Audience\" --tone casual`")
    st.stop()

if search:
    mask = copy_df.apply(lambda row: search.lower() in str(row).lower(), axis=1)
    copy_df = copy_df[mask]
if show_used == "Used in Ads" and "used_in_ad_id" in copy_df.columns:
    copy_df = copy_df[copy_df["used_in_ad_id"].notna()]
elif show_used == "Unused" and "used_in_ad_id" in copy_df.columns:
    copy_df = copy_df[copy_df["used_in_ad_id"].isna()]

if copy_df.empty:
    st.warning("No copy matching your filters.")
    st.stop()

# ── Stats ──────────────────────────────────────────────────────
total  = len(copy_df)
used   = int(copy_df["used_in_ad_id"].notna().sum()) if "used_in_ad_id" in copy_df.columns else 0
unused = total - used
tones  = copy_df["tone"].nunique() if "tone" in copy_df.columns else 0

styles.kpi_grid([
    ("&#x270D;", "Variations",   str(total),  "Generated",  "#1877F2"),
    ("&#x2705;", "Used in Ads",  str(used),   "Live",       "#2E7D32"),
    ("&#x1F4C2;", "Unused",      str(unused), "Available",  "#E65C00"),
    ("&#x1F3A8;", "Tone Styles", str(tones),  "Variants",   "#9C27B0"),
])

styles.sec("🃏", f"Copy Cards ({total} variations)")

# ── 3-column card grid ────────────────────────────────────────
COLS = 3
rows_data = [copy_df.iloc[i:i+COLS] for i in range(0, len(copy_df), COLS)]

for ri, row_group in enumerate(rows_data):
    cols = st.columns(COLS)
    for col, (_, row) in zip(cols, row_group.iterrows()):
        headline = row.get("headline","")
        body_txt = row.get("body","")
        cta      = str(row.get("cta","")).replace("_"," ")
        hook     = row.get("hook","")
        product  = row.get("product","")
        audience = row.get("audience","")
        tone     = row.get("tone","")
        note     = row.get("compliance_note","")
        created  = str(row.get("created_at",""))[:16]
        used_in  = row.get("used_in_ad_id",None)

        top_color = "#2E7D32" if used_in else "#1877F2"
        tags = ""
        if product:  tags += f'<span class="tag">&#128247; {product[:22]}</span>'
        if audience: tags += f'<span class="tag">&#128101; {audience[:22]}</span>'
        if tone:     tags += f'<span class="tag">&#127908; {tone}</span>'

        used_badge = ""
        if used_in:
            used_badge = f'<div style="display:inline-flex;align-items:center;gap:4px;background:#E8F5E9;color:#2E7D32;padding:2px 10px;border-radius:12px;font-size:10px;font-weight:800;margin-top:6px">&#x2705; Used in Ad {used_in}</div>'

        note_html = f'<div class="copy-note">&#9888; {note}</div>' if note else ""
        hook_html = f'<div class="copy-hook">&#128161; Hook: {hook}</div>' if hook else ""

        # stagger animation delay
        delay = f"{(ri * COLS) * 0.06:.2f}s"

        with col:
            st.markdown(f"""
            <div class="copy-card {'copy-card-used' if used_in else ''}" style="border-top-color:{top_color};animation-delay:{delay}">
              <div class="copy-hl">{headline}</div>
              <div class="copy-bod">{body_txt}</div>
              {hook_html}
              <span class="copy-cta">{cta}</span>
              {note_html}
              <div style="margin-top:10px">{tags}</div>
              {used_badge}
              <div class="copy-meta">Created {created}</div>
            </div>
            """, unsafe_allow_html=True)

# ── Raw table ─────────────────────────────────────────────────
with st.expander("📋 Raw data & Export"):
    st.dataframe(copy_df, width="stretch", hide_index=True)
    st.download_button("⬇️ Download CSV", data=copy_df.to_csv(index=False), file_name="ad_copy.csv", mime="text/csv")
