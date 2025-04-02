@echo off
title Maya Virus Scanner Tool

echo Starting Maya Virus Scanner...
echo.

:: Set working directory to script location
cd /d "%~dp0"

:: Try to find mayapy.exe, checking multiple Maya versions
set MAYAPY_FOUND=0
set MAYAPY_PATH=

:: First check for Maya 2024
if exist "C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe" (
    set MAYAPY_PATH=C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe
    set MAYAPY_FOUND=1
    goto run_mayapy
)

:: Then try Maya 2023, 2022, etc.
for %%y in (2023 2022 2021 2020 2019 2018) do (
    if exist "C:\Program Files\Autodesk\Maya%%y\bin\mayapy.exe" (
        set MAYAPY_PATH=C:\Program Files\Autodesk\Maya%%y\bin\mayapy.exe
        set MAYAPY_FOUND=1
        goto run_mayapy
    )
)

:: If mayapy not found, try system Python
echo Warning: mayapy.exe not found, trying system Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Using system Python...
    python main.py --gui
) else (
    echo Error: Python or mayapy not found. Please ensure Maya or Python is installed.
    pause
    exit /b 1
)
goto end

:run_mayapy
echo Using Maya Python: %MAYAPY_PATH%
echo.
echo Note: If problems persist, try running as administrator.
echo.
"%MAYAPY_PATH%" main.py --gui
if %errorlevel% neq 0 (
    echo.
    echo Execution failed, error code: %errorlevel%
    if exist logs (
        echo Please check latest log file for details:
        dir /b /od logs\*.log | findstr /v /i "\.old" | sort /r | more +0
    )
)

:end
echo.
echo Program exited.
pause 