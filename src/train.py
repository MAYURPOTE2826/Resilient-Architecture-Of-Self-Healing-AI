"""
train.py — Build baseline stats (Z-score detector) + RandomForest classifier.

Run from the project root:
    src\\venv\\Scripts\\python.exe src\\train.py
"""
import os
import random

import joblib
import pandas as pd
import psutil
from sklearn.ensemble import RandomForestClassifier

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACT_PATH = os.path.join(BASE_DIR, "artifacts.joblib")
FEATURES      = ["cpu_usage", "memory_usage", "latency", "disk_io"]


def main() -> None:
    print("=" * 60)
    print("  Self-Healing System — Model Retraining")
    print("=" * 60)

    # ── 1. Collect real baseline (normal) samples ─────────────────────────────
    SAMPLE_COUNT = 60
    print(f"\n[1/3] Collecting {SAMPLE_COUNT} real baseline samples (~{SAMPLE_COUNT}s)...")

    # Prime disk delta
    _last = psutil.disk_io_counters()

    normal_rows = []
    for i in range(SAMPLE_COUNT):
        counters = psutil.disk_io_counters()
        delta_mb = max(0.0, (counters.read_bytes + counters.write_bytes -
                             _last.read_bytes - _last.write_bytes) / (1024 * 1024))
        _last = counters

        row = {
            "cpu_usage":    psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "latency":      random.uniform(1, 100),   # TODO: replace with real HTTP latency
            "disk_io":      round(delta_mb, 3),
        }
        normal_rows.append(row)
        if (i + 1) % 10 == 0:
            print(f"  {i+1:2d}/{SAMPLE_COUNT}  cpu={row['cpu_usage']:.1f}%  "
                  f"mem={row['memory_usage']:.1f}%  disk_io={row['disk_io']:.2f} MB/s")

    normal_df = pd.DataFrame(normal_rows, columns=FEATURES)

    # ── 2. Compute baseline stats (mean + std per feature) ────────────────────
    print("\n[2/3] Computing baseline statistics ...")

    stats = {}
    for feat in FEATURES:
        mean = normal_df[feat].mean()
        std  = max(normal_df[feat].std(), 0.1)   # min std avoids division by zero
        stats[feat] = (mean, std)
        print(f"  {feat:<15} mean={mean:.2f}  std={std:.2f}  "
              f"anomaly threshold (2.5σ) = {mean + 2.5*std:.2f}")

    # ── 3. Train RandomForest fault classifier ────────────────────────────────
    print("\n[3/3] Training RandomForest fault classifier ...")

    cpu_mean, cpu_std   = stats["cpu_usage"]
    mem_mean, mem_std   = stats["memory_usage"]
    disk_mean, disk_std = stats["disk_io"]

    def _clamp(v, lo, hi):
        return max(lo, min(hi, v))

    anomaly_rows, anomaly_labels = [], []

    for _ in range(20):   # cpu_spike
        anomaly_rows.append({
            "cpu_usage":    _clamp(cpu_mean + random.uniform(2.5, 4) * cpu_std, 0, 100),
            "memory_usage": random.gauss(mem_mean, mem_std),
            "latency":      random.uniform(1, 100),
            "disk_io":      max(0, random.gauss(disk_mean, disk_std)),
        })
        anomaly_labels.append("cpu_spike")

    for _ in range(20):   # memory_leak
        anomaly_rows.append({
            "cpu_usage":    random.gauss(cpu_mean, cpu_std),
            "memory_usage": _clamp(mem_mean + random.uniform(2.5, 4) * mem_std, 0, 100),
            "latency":      random.uniform(1, 100),
            "disk_io":      max(0, random.gauss(disk_mean, disk_std)),
        })
        anomaly_labels.append("memory_leak")

    for _ in range(20):   # network_latency
        anomaly_rows.append({
            "cpu_usage":    random.gauss(cpu_mean, cpu_std),
            "memory_usage": random.gauss(mem_mean, mem_std),
            "latency":      random.uniform(400, 600),
            "disk_io":      max(0, random.gauss(disk_mean, disk_std)),
        })
        anomaly_labels.append("network_latency")

    for _ in range(20):   # disk_stress
        anomaly_rows.append({
            "cpu_usage":    random.gauss(cpu_mean, cpu_std),
            "memory_usage": random.gauss(mem_mean, mem_std),
            "latency":      random.uniform(1, 100),
            "disk_io":      disk_mean + random.uniform(2.5, 4) * disk_std,
        })
        anomaly_labels.append("disk_stress")

    clf_X = pd.concat([normal_df, pd.DataFrame(anomaly_rows, columns=FEATURES)], ignore_index=True)
    clf_y = ["normal"] * len(normal_df) + anomaly_labels

    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(clf_X, clf_y)
    print(f"  Classes trained: {list(rf.classes_)}")

    # ── Save ──────────────────────────────────────────────────────────────────
    artifacts = {
        "stats":         stats,
        "random_forest": rf,
    }
    joblib.dump(artifacts, ARTIFACT_PATH)

    print(f"\n{'=' * 60}")
    print(f"  Artifacts saved to: {ARTIFACT_PATH}")
    print(f"  Done! Restart api.py to load the new models.")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
