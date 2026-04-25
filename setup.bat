@echo off
echo.
echo ============================================================
echo   META ADS AUTOMATION  -  Setup
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: pip install failed.
    pause
    exit /b 1
)

echo.
echo [2/3] Setting up .env file...
if not exist .env (
    copy .env.example .env
    echo Created .env from template.
    echo.
    echo IMPORTANT: Open .env and fill in your Meta API credentials:
    echo   - META_APP_ID
    echo   - META_APP_SECRET
    echo   - META_ACCESS_TOKEN
    echo   - META_AD_ACCOUNT_ID
    echo   - META_PAGE_ID
    echo.
    echo Get them from: https://developers.facebook.com/apps/
    echo.
) else (
    echo .env already exists, skipping.
)

echo [3/3] Initializing database...
python -c "from database.db import init_db; init_db(); print('Database ready.')"

echo.
echo ============================================================
echo   Setup complete!
echo.
echo   Next steps:
echo   1. Fill in your credentials in .env
echo   2. Run: python main.py setup verify
echo   3. Run: python main.py campaign list --sync
echo ============================================================
echo.
pause
