import psutil
import random
import time

def collect_metrics():
    return {
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent,
        "latency": random.uniform(1, 100),
        "disk_io": psutil.disk_io_counters().read_bytes / (1024 * 1024)
    }

if __name__ == "__main__":
    while True:
        print(collect_metrics())
        time.sleep(2)
