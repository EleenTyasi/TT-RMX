@echo off
cd /d "%~dp0"

taskkill /f /im astrond.exe >nul 2>&1
taskkill /f /im ppython.exe >nul 2>&1
taskkill /f /fi "windowtitle eq Toontown Online - UberDOG Server" >nul 2>&1
taskkill /f /fi "windowtitle eq Toontown Online - Astron Server" >nul 2>&1
taskkill /f /fi "windowtitle eq Toontown Online - AI (District) Server" >nul 2>&1
taskkill /f /fi "windowtitle eq Toontown Online - Game Client" >nul 2>&1

start start_astron_server.bat

ping 127.0.0.1 -n 1 > nul
start start_uberdog_server.bat

ping 127.0.0.1 -n 1 > nul
start start_ai_server.bat

ping 127.0.0.1 -n 3 > nul
start start_game.bat
