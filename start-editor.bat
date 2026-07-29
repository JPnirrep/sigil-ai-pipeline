@echo off
REM KLEIA-UP Book Editor — Démarrage rapide Windows
REM Usage : double-clic ou lancer depuis terminal

echo ========================================
echo   KLEIA-UP Book Editor
echo ========================================
echo.

set "SCRIPT_DIR=%~dp0"
set "BACKEND_PORT=8589"
set "FRONTEND_PORT=5174"

REM Kill any existing processes on our ports
echo [Nettoyage] Arret des processus existants...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%BACKEND_PORT%"') do (
    taskkill /F /PID %%a 2>nul
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%FRONTEND_PORT%"') do (
    taskkill /F /PID %%a 2>nul
)
timeout /t 2 /nobreak >nul

REM Start backend
echo [Backend] Demarrage sur :%BACKEND_PORT%...
start "KLEIA-Backend" /B python -m uvicorn editor.api.main:app --port %BACKEND_PORT% --host 0.0.0.0
timeout /t 3 /nobreak >nul

REM Wait for backend to be ready
:wait_backend
curl -sf http://localhost:%BACKEND_PORT%/api/health >nul 2>&1
if errorlevel 1 (
    timeout /t 1 /nobreak >nul
    goto wait_backend
)
echo   Backend OK

REM Start frontend
echo [Frontend] Demarrage sur :%FRONTEND_PORT%...
cd /d "%SCRIPT_DIR%editor\frontend"
start "KLEIA-Frontend" /B npx vite --port %FRONTEND_PORT% --host 0.0.0.0
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   Editeur pret !
echo.
echo   Frontend : http://localhost:%FRONTEND_PORT%
echo   Backend  : http://localhost:%BACKEND_PORT%
echo ========================================
echo.
echo Appuyez sur une touche pour fermer les serveurs...
pause >nul

REM Cleanup
echo.
echo Arret des serveurs...
taskkill /F /FI "WINDOWTITLE eq KLEIA-Backend*" 2>nul
taskkill /F /FI "WINDOWTITLE eq KLEIA-Frontend*" 2>nul
echo Termine.
timeout /t 2 /nobreak >nul
