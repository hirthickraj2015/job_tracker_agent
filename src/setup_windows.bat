@echo off
echo 🚀 Setting up Job Tracker Agent for Windows...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

REM Get the directory where the script is located
set SCRIPT_DIR=%~dp0
set PROJECT_DIR=%SCRIPT_DIR%..

cd /d "%PROJECT_DIR%"

echo 📁 Project directory: %PROJECT_DIR%

REM Create virtual environment
if not exist "venv" (
    python -m venv venv
    echo ✅ Created virtual environment
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat
echo ✅ Activated virtual environment

REM Upgrade pip
python -m pip install --upgrade pip

REM Install dependencies
if exist "requirements.txt" (
    pip install -r requirements.txt
    echo ✅ Installed Python dependencies
) else (
    echo ❌ requirements.txt not found
    pause
    exit /b 1
)

REM Create run batch file
echo @echo off > run.bat
echo cd /d "%PROJECT_DIR%" >> run.bat
echo call venv\Scripts\activate.bat >> run.bat
echo python src\job_tracker.py %%* >> run.bat

echo ✅ Created run.bat file

echo.
echo 🎉 Setup completed successfully!
echo.
echo 📋 Next steps:
echo 1. Edit config\job_config.json with your preferences
echo 2. Add your email credentials to the config file
echo 3. Test with: run.bat --run-once
echo 4. For continuous operation: run.bat --schedule
echo.
echo 📁 Project files are in: %PROJECT_DIR%
echo.
echo 🔧 For support, check the README.md file.
pause