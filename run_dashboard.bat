@echo off
title Meta Ads Dashboard
echo ============================================================
echo  Meta Ads - Client Reporting Portal
echo ============================================================
echo.
cd /d "%~dp0"
streamlit run dashboard\app.py --server.port 8501 --server.headless false
pause
