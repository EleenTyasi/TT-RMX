@echo off
title Toontown Remix - Start Fusion
cd /d "%~dp0"

echo ======================================================
echo           Toontown Remix - Start Fusion (64-bit)
echo ======================================================

rem Clean up any lingering processes first
taskkill /f /im astrond.exe >nul 2>&1
taskkill /f /im ppython.exe >nul 2>&1

rem Resolve 64-bit Python executable
if exist "dependencies\panda3d\python\ppython.exe" (
    set "PPYTHON_PATH=dependencies\panda3d\python\ppython.exe"
) else if exist "C:\Panda3D-1.11.0-x64\python\ppython.exe" (
    set "PPYTHON_PATH=C:\Panda3D-1.11.0-x64\python\ppython.exe"
) else if exist "PPYTHON_PATH" (
    set /P PPYTHON_PATH=<PPYTHON_PATH
)

if not exist "%PPYTHON_PATH%" (
    echo [ERROR] 64-bit Panda3D runtime not found!
    echo Looked at: %PPYTHON_PATH%
    echo.
    echo If Start Fusion fails, please use 'win32\start_all.bat'
    echo ======================================================
    pause
    exit /b 1
)

"%PPYTHON_PATH%" tools\fusion.py %*

if errorlevel 1 (
    echo.
    echo [NOTICE] If Start Fusion fails, please use 'win32\start_all.bat'
    pause
)
