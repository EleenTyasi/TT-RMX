@echo off
title Toontown Online - Astron Server
cd /d "%~dp0\..\astron"
astrond --loglevel info config/astrond.yml
pause
