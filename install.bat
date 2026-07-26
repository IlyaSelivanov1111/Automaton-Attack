@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   Word Capture Bot - Installer
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    echo Install Python 3.10+ from https://www.python.org/downloads/
    echo and check "Add python.exe to PATH" during setup.
    pause
    exit /b 1
)

echo [1/4] Creating virtual environment...
python -m venv ".venv"
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

echo [2/4] Installing dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo [3/4] Creating desktop shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$sc = $ws.CreateShortcut([System.IO.Path]::Combine($ws.SpecialFolders('Desktop'), 'Word Capture Bot.lnk')); " ^
    "$sc.TargetPath = '%~dp0run.bat'; " ^
    "$sc.WorkingDirectory = '%~dp0'; " ^
    "$sc.IconLocation = '%~dp0.venv\Scripts\pythonw.exe'; " ^
    "$sc.WindowStyle = 7; " ^
    "$sc.Description = 'Word Capture Bot'; " ^
    "$sc.Save()"

echo [4/4] Checking Tesseract OCR engine...
if not exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo.
    echo [!] Tesseract OCR engine was not found at:
    echo     C:\Program Files\Tesseract-OCR\tesseract.exe
    echo.
    echo     This program needs the Tesseract OCR engine itself
    echo     ^(a separate program, not just the Python package^).
    echo     Download and install it from:
    echo     https://github.com/UB-Mannheim/tesseract/wiki
    echo     Use the default install location so the bot can find it.
)

echo.
echo ============================================
echo   Installation complete!
echo   A shortcut "Word Capture Bot" was added to your Desktop.
echo ============================================
pause
