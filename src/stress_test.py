"""
stress_test.py — Simulate a CPU spike to trigger anomaly detection & healing.

Run from the project root:
    src\\venv\\Scripts\\python.exe src\\stress_test.py
"""
import multiprocessing
import os
import time

import psutil

_MAX_MEMORY_MB = 300   # cap allocation to avoid OOM-killing the machine


def _cpu_burn():
    """Burn 100% of one CPU core."""
    while True:
        _ = 99999 ** 9999


def _memory_pressure():
    """Allocate up to _MAX_MEMORY_MB to push memory above threshold."""
    data = []
    allocated_mb = 0
    try:
        while allocated_mb < _MAX_MEMORY_MB:
            data.append(b"x" * (10 * 1024 * 1024))  # 10 MB chunks
            allocated_mb += 10
            time.sleep(0.5)
        # Hold the allocation for the remainder of the stress window
        time.sleep(300)
    except Exception:
        pass


def main():
    baseline_cpu = psutil.cpu_percent(interval=2)
    cpu_count    = multiprocessing.cpu_count()

    # Spawn enough workers to spike CPU well above the 2.5-sigma threshold
    workers_needed = max(2, cpu_count - 1)

    print("=" * 55)
    print("  Self-Healing System — CPU Stress Test")
    print("=" * 55)
    print(f"  CPU cores     : {cpu_count}")
    print(f"  Baseline CPU  : {baseline_cpu:.1f}%")
    print(f"  Spawning      : {workers_needed} burn workers")
    print(f"  Memory cap    : {_MAX_MEMORY_MB} MB")
    print()
    print("  Watch Grafana at http://127.0.0.1:3000")
    print("  Expect: NORMAL -> DEGRADED -> HEALING -> RECOVERED")
    print()
    print("  Starting stress in 3 seconds...")
    time.sleep(3)

    # Start CPU burn workers + 1 memory pressure worker
    workers = []
    for _ in range(workers_needed):
        p = multiprocessing.Process(target=_cpu_burn, daemon=True)
        p.start()
        workers.append(p)

    mem_worker = multiprocessing.Process(target=_memory_pressure, daemon=True)
    mem_worker.start()
    workers.append(mem_worker)

    print(f"  [{time.strftime('%H:%M:%S')}] Stress started — burning CPU...")
    print("  Waiting for ML engine to detect anomaly (up to ~25s)...")
    print()

    # Monitor CPU and wait for healing to trigger
    start = time.time()
    try:
        while time.time() - start < 60:
            cpu_now = psutil.cpu_percent(interval=2)
            elapsed = int(time.time() - start)
            print(f"  [{time.strftime('%H:%M:%S')}] CPU={cpu_now:.1f}%  "
                  f"(+{cpu_now - baseline_cpu:.1f}% above baseline)  "
                  f"elapsed={elapsed}s", end="\r")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n  Stopped by user.")

    finally:
        print(f"\n\n  [{time.strftime('%H:%M:%S')}] Stopping stress workers...")
        for p in workers:
            p.terminate()
            p.join(timeout=2)

        recovered_cpu = psutil.cpu_percent(interval=2)
        print(f"  [{time.strftime('%H:%M:%S')}] CPU back to {recovered_cpu:.1f}%")
        print()
        print("  Check Grafana — you should see:")
        print("    * Anomaly count increased")
        print("    * System state cycled DEGRADED -> HEALING -> RECOVERED")
        print("    * Healing count incremented")
        print("=" * 55)


if __name__ == "__main__":
    main()
