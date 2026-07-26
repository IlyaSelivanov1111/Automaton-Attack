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

echo [1/5] Creating virtual environment...
python -m venv ".venv"
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)

echo [2/5] Installing Python dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo [3/5] Checking Tesseract OCR engine...
set "TESSERACT_EXE=C:\Program Files\Tesseract-OCR\tesseract.exe"
set "TESSERACT_URL=https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.4.0.20240606.exe"
set "TESSERACT_SETUP=%TEMP%\tesseract-ocr-setup.exe"

if exist "%TESSERACT_EXE%" (
    echo     Tesseract OCR is already installed.
) else (
    echo     Tesseract OCR not found. Downloading installer ^(~50 MB^)...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%TESSERACT_URL%' -OutFile '%TESSERACT_SETUP%'"

    if exist "%TESSERACT_SETUP%" (
        echo     Installing Tesseract OCR silently ^(an administrator prompt will appear^)...
        powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%TESSERACT_SETUP%' -ArgumentList '/S' -Verb RunAs -Wait"
        del /q "%TESSERACT_SETUP%" >nul 2>&1

        if exist "%TESSERACT_EXE%" (
            echo     Tesseract OCR installed successfully.
        ) else (
            echo     [WARNING] Could not confirm Tesseract installation.
            echo     If you cancelled the admin prompt, install it manually from:
            echo     https://github.com/UB-Mannheim/tesseract/releases/tag/v5.4.0.20240606
        )
    ) else (
        echo     [ERROR] Failed to download the Tesseract installer.
        echo     Install it manually from:
        echo     https://github.com/UB-Mannheim/tesseract/releases/tag/v5.4.0.20240606
    )
)

echo [4/5] Creating desktop shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$sc = $ws.CreateShortcut([System.IO.Path]::Combine($ws.SpecialFolders('Desktop'), 'Word Capture Bot.lnk')); " ^
    "$sc.TargetPath = '%~dp0run.bat'; " ^
    "$sc.WorkingDirectory = '%~dp0'; " ^
    "$sc.IconLocation = '%~dp0.venv\Scripts\pythonw.exe'; " ^
    "$sc.WindowStyle = 7; " ^
    "$sc.Description = 'Word Capture Bot'; " ^
    "$sc.Save()"

echo [5/5] Starting Word Capture Bot...
start "" ".venv\Scripts\pythonw.exe" "capture_bot.py"

echo.
echo ============================================
echo   Installation complete!
echo   A shortcut "Word Capture Bot" was added to your Desktop,
echo   and the program has been started.
echo ============================================
pause
