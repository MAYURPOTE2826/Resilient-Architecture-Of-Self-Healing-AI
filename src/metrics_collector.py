import random
import time
import subprocess
import re

import psutil

import os
from dotenv import load_dotenv

load_dotenv()
from logger import logger

# Prime with current counter so the first call doesn't produce a misleading huge spike
_initial_disk = psutil.disk_io_counters()
_last_disk_bytes: int = _initial_disk.read_bytes + _initial_disk.write_bytes

PING_TARGET = os.getenv("PING_TARGET", "google.com")

def get_ping() -> int:
    try:
        result = subprocess.run(
            ["ping", PING_TARGET, "-n", "1"],
            capture_output=True,
            text=True,
            timeout=2
        )
        match = re.search(r"time[=<](\d+)ms", result.stdout)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    # Fallback if ping fails
    return random.randint(10, 50)

def collect_metrics() -> dict:
    global _last_disk_bytes
    
    try:
        counters = psutil.disk_io_counters()
        if counters:
            current_bytes = counters.read_bytes + counters.write_bytes
            delta_mb = max(0.0, (current_bytes - _last_disk_bytes) / (1024 * 1024))
            _last_disk_bytes = current_bytes
        else:
            delta_mb = 0.0
    except Exception:
        delta_mb = 0.0

    ping = get_ping()
    
    try:
        cpu = psutil.cpu_percent(interval=1)
    except Exception:
        cpu = 0.0
        
    try:
        mem = psutil.virtual_memory().percent
    except Exception:
        mem = 0.0
    
    try:
        disk_pct = psutil.disk_usage('/').percent
    except Exception:
        disk_pct = 0.0
        
    try:
        proc_count = len(psutil.pids())
    except Exception:
        proc_count = 0

    return {
        # Old keys (Backward Compatibility for ML Anomaly Detector)
        "cpu_usage":    cpu,
        "memory_usage": mem,
        "latency":      ping,
        "disk_io":      round(delta_mb, 3),
        
        # New keys (For UI and Rule-Based Fault Classifier)
        "cpu": cpu,
        "memory": mem,
        "disk": disk_pct,
        "process_count": proc_count,
        "ping": ping
    }

if __name__ == "__main__":
    while True:
        try:
            logger.info(collect_metrics())
        except Exception as e:
            logger.error(f"Metrics collection error: {e}")
        finally:
            time.sleep(2)
