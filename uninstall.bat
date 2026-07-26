@echo off
setlocal
cd /d "%~dp0"

echo ============================================
echo   Word Capture Bot - Uninstaller
echo ============================================
echo.

echo [1/3] Removing desktop shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$path = [System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'Word Capture Bot.lnk'); if (Test-Path $path) { Remove-Item $path -Force }"

echo [2/3] Removing virtual environment...
if exist ".venv" rd /s /q ".venv"

set /p CLEARDB="Delete learned words database (learned_words.json)? [y/N]: "
if /i "%CLEARDB%"=="y" (
    if exist "learned_words.json" del /q "learned_words.json"
    echo Learned words database removed.
) else (
    echo Learned words database kept.
)

echo.
echo ============================================
echo   Uninstall complete.
echo   You can now delete this folder manually.
echo ============================================
pause
