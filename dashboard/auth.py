import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "admin123")
DASHBOARD_TITLE    = os.getenv("BRAND_NAME", "Meta Ads Dashboard")


def check_login() -> bool:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    return st.session_state.authenticated


def login_page():
    st.markdown("""
    <style>
    @keyframes fadeInUp {
      from { opacity:0; transform:translateY(30px); }
      to   { opacity:1; transform:translateY(0); }
    }
    @keyframes gradientFlow {
      0%   { background-position:0% 50%; }
      50%  { background-position:100% 50%; }
      100% { background-position:0% 50%; }
    }
    @keyframes floatLogo {
      0%,100% { transform:translateY(0); }
      50%      { transform:translateY(-8px); }
    }
    @keyframes pulseRing {
      0%   { box-shadow:0 0 0 0 rgba(24,119,242,0.5); }
      70%  { box-shadow:0 0 0 18px rgba(24,119,242,0); }
      100% { box-shadow:0 0 0 0 rgba(24,119,242,0); }
    }
    .stApp {
      background: linear-gradient(135deg,#0D1B2A 0%,#1A2840 50%,#0D1B2A 100%) !important;
      background-size: 300% 300% !important;
      animation: gradientFlow 12s ease infinite !important;
    }
    .block-container { padding-top:0 !important; }

    .login-wrap {
      display:flex; flex-direction:column; align-items:center;
      justify-content:center; min-height:90vh;
    }
    .login-box {
      background:rgba(255,255,255,0.97);
      border-radius:24px;
      padding:44px 40px 36px;
      max-width:400px; width:100%;
      box-shadow:0 24px 64px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.1);
      animation:fadeInUp .6s ease both;
    }
    .login-logo {
      width:72px; height:72px; border-radius:20px;
      background:linear-gradient(135deg,#1877F2,#0052CC);
      display:flex; align-items:center; justify-content:center;
      font-size:32px; margin:0 auto 20px;
      animation:floatLogo 3s ease-in-out infinite, pulseRing 2.5s ease infinite;
      box-shadow:0 8px 24px rgba(24,119,242,0.45);
    }
    .login-title {
      font-size:22px; font-weight:900; color:#1C1E21;
      text-align:center; margin-bottom:4px;
    }
    .login-sub {
      font-size:13px; color:#90949C; text-align:center; margin-bottom:28px;
    }
    .login-hint {
      font-size:11px; color:#B0B3B8; text-align:center;
      margin-top:16px; line-height:1.6;
    }
    /* Input & button overrides inside login */
    .stTextInput > label { font-size:12px !important; font-weight:700 !important; color:#606770 !important; text-transform:uppercase !important; letter-spacing:.6px !important; }
    .stTextInput > div > div > input {
      border-radius:10px !important; border:1.5px solid #E9EBEE !important;
      font-size:15px !important; padding:10px 14px !important;
      transition:border-color .2s, box-shadow .2s !important;
    }
    .stTextInput > div > div > input:focus {
      border-color:#1877F2 !important;
      box-shadow:0 0 0 3px rgba(24,119,242,0.2) !important;
    }
    .stButton > button[kind="primary"] {
      background:linear-gradient(135deg,#1877F2,#0052CC) !important;
      border:none !important; border-radius:12px !important;
      font-size:15px !important; font-weight:800 !important;
      height:48px !important; letter-spacing:.3px !important;
      box-shadow:0 6px 20px rgba(24,119,242,0.4) !important;
      transition:opacity .2s, transform .15s !important;
    }
    .stButton > button[kind="primary"]:hover {
      opacity:.9 !important; transform:translateY(-2px) !important;
      box-shadow:0 10px 28px rgba(24,119,242,0.5) !important;
    }
    @media (max-width:480px) {
      .login-box { padding:32px 20px 24px; border-radius:18px; }
      .login-logo { width:60px; height:60px; font-size:26px; }
    }
    </style>

    <div class="login-wrap">
      <div class="login-box">
        <div class="login-logo">&#128200;</div>
        <div class="login-title">Meta Ads Portal</div>
        <div class="login-sub">Client Reporting Dashboard</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        if st.button("Sign In", use_container_width=True, type="primary"):
            if password == DASHBOARD_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password. Please try again.")
        st.markdown('<div class="login-hint">Secured portal &nbsp;&#183;&nbsp; Default: admin123<br>Change via DASHBOARD_PASSWORD in .env</div>', unsafe_allow_html=True)


def logout():
    st.session_state.authenticated = False
    st.rerun()
