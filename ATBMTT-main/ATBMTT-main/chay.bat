@echo off
cd /d "%~dp0"
if not exist "%~dp0giao_dien.html" (
    echo Missing giao_dien.html. Please keep this file in the project folder.
    pause
    exit /b 1
)
start "" "%~dp0giao_dien.html"
if errorlevel 1 pause
