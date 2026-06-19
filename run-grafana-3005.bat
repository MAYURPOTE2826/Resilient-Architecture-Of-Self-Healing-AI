@echo off
echo ==============================================
echo  Starting Fresh Grafana on Port 3005
echo ==============================================
echo.
echo Please wait a few seconds for the server to start...
echo Leave this black window open! If you close it, Grafana will stop.
echo.
echo Once it says "HTTP Server Listen", open your browser to:
echo http://localhost:3005
echo.
echo Default Login:
echo Username: admin
echo Password: admin
echo.

cd /d "%~dp0grafana-bin\grafana-v11.1.0\bin"
grafana-server.exe -config "..\conf\custom.ini"
pause
