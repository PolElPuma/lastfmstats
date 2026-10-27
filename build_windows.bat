@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"

python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 exit /b 1

python -m PyInstaller --noconfirm --clean --onefile --windowed --name LastFMStats --paths "%ROOT%src" "%ROOT%src\gui.py"
if errorlevel 1 exit /b 1

echo Ejecutable creado en: %ROOT%dist\LastFMStats.exe
endlocal