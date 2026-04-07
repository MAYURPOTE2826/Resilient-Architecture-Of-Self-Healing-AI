import random
import time

import psutil

from logger import logger

# Prime with current counter so the first call doesn't produce a misleading huge spike
_initial_disk = psutil.disk_io_counters()
_last_disk_bytes: int = _initial_disk.read_bytes + _initial_disk.write_bytes


def collect_metrics() -> dict:
    global _last_disk_bytes
    counters = psutil.disk_io_counters()
    current_bytes = counters.read_bytes + counters.write_bytes
    delta_mb = max(0.0, (current_bytes - _last_disk_bytes) / (1024 * 1024))
    _last_disk_bytes = current_bytes

    return {
        "cpu_usage":    psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent,
        "latency":      random.uniform(1, 100),
        "disk_io":      round(delta_mb, 3),
    }


if __name__ == "__main__":
    while True:
        try:
            logger.info(collect_metrics())
        except Exception as e:
            logger.error(f"Metrics collection error: {e}")
        finally:
            time.sleep(2)
