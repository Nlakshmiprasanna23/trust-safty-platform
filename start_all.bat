@echo off
start cmd /k start_backend.bat
timeout /t 12
start cmd /k start_frontend.bat
start http://localhost:5173
