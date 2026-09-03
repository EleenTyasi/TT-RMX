@echo off
title Toontown Online - Developer Mini-Server Launcher
cd /d "%~dp0\.."

rem Resolve 64-bit Python executable:
if exist "dependencies\panda3d\python\ppython.exe" (
    set "PPYTHON_PATH=dependencies\panda3d\python\ppython.exe"
) else if exist "C:\Panda3D-1.11.0-x64\python\ppython.exe" (
    set "PPYTHON_PATH=C:\Panda3D-1.11.0-x64\python\ppython.exe"
) else (
    set /P PPYTHON_PATH=<PPYTHON_PATH
)

echo Toontown Online Developer Mini-Server Launcher
echo.
echo NOTE: Make sure that "mini-server" is enabled in your settings.json!
echo.

set /P TTOFF_LOGIN_TOKEN="Username (default: dev): " || ^
set TTOFF_LOGIN_TOKEN=dev

set /P TTOFF_GAME_SERVER="Game Server (default: 127.0.0.1): " || ^
set TTOFF_GAME_SERVER=127.0.0.1

%PPYTHON_PATH% -m toontown.launcher.TTOffQuickStartLauncher
pause
