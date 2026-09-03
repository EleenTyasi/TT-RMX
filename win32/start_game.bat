@echo off
title Toontown Online - Game Client
cd /d "%~dp0\.."

rem Resolve 64-bit Python executable:
if exist "dependencies\panda3d\python\ppython.exe" (
    set "PPYTHON_PATH=dependencies\panda3d\python\ppython.exe"
) else if exist "C:\Panda3D-1.11.0-x64\python\ppython.exe" (
    set "PPYTHON_PATH=C:\Panda3D-1.11.0-x64\python\ppython.exe"
) else (
    set /P PPYTHON_PATH=<PPYTHON_PATH
)

set TTOFF_LOGIN_TOKEN=dev

%PPYTHON_PATH% -m toontown.launcher.TTOffQuickStartLauncher
pause
