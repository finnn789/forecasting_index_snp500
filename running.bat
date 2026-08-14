@echo off
REM running.bat — Wrapper agar running.sh bisa dijalankan sekali klik di Windows Explorer.
REM Membutuhkan Git for Windows (bash.exe) terinstall.

setlocal
set "SCRIPT_DIR=%~dp0"

where bash >nul 2>nul
if errorlevel 1 (
    echo [ERROR] 'bash' tidak ditemukan di PATH. Install Git for Windows: https://git-scm.com/download/win
    pause
    exit /b 1
)

bash "%SCRIPT_DIR%running.sh"
pause
