@echo off
title Toontown Online - UberDOG Server
cd /d "%~dp0\.."

rem Resolve 64-bit Python executable:
if exist "dependencies\panda3d\python\ppython.exe" (
    set "PPYTHON_PATH=dependencies\panda3d\python\ppython.exe"
) else if exist "C:\Panda3D-1.11.0-x64\python\ppython.exe" (
    set "PPYTHON_PATH=C:\Panda3D-1.11.0-x64\python\ppython.exe"
) else (
    set /P PPYTHON_PATH=<PPYTHON_PATH
)

%PPYTHON_PATH% -m toontown.uberdog.UDStart --base-channel 1000000 ^
               --max-channels 999999 --stateserver 4002 ^
               --astron-ip 127.0.0.1:7199 --eventlogger-ip 127.0.0.1:7197
pause
