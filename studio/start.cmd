@echo off
setlocal
set "ROOT=%~dp0.."
cd /d "%ROOT%"
if "%STUDIO_PORT%"=="" set "STUDIO_PORT=4780"
set "PYTHON=%ROOT%\.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=%ROOT%\OpenMontage\.venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=python"
echo Starting Story Studio on http://127.0.0.1:%STUDIO_PORT%
if not defined STUDIO_NO_BROWSER start "" /b cmd /c "timeout /t 3 >nul & start http://127.0.0.1:%STUDIO_PORT%"
"%PYTHON%" -m studio.server
endlocal
