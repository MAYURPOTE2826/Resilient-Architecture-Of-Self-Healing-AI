@echo off
echo Starting Self-Healing AI System...

:: Start Prometheus in background
start "Prometheus" "C:\prometheus\prometheus-2.48.1.windows-amd64\prometheus.exe" --config.file=d:\RSA\R\prometheus-local.yml

:: Start Flask API (in same window)
cd /d d:\RSA\R\src
python api.py
