import hashlib
import os

import joblib
import pandas as pd

from logger import logger

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR      = os.environ.get("DATA_DIR", BASE_DIR)
ARTIFACT_PATH = os.path.join(DATA_DIR, "artifacts.joblib")

_stats = None

ZSCORE_THRESHOLD = 2.5   # flag if any feature is 2.5+ std devs from baseline mean


def _load_stats():
    global _stats
    if _stats is not None:
        return _stats

    if not os.path.exists(ARTIFACT_PATH):
        raise RuntimeError(f"Artifact file not found: {ARTIFACT_PATH}. Run training first.")

    with open(ARTIFACT_PATH, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()
    logger.info(f"Loading anomaly stats from {ARTIFACT_PATH} (SHA256: {sha256})")

    artifacts = joblib.load(ARTIFACT_PATH)
    if "stats" not in artifacts:
        raise RuntimeError("Artifact file is missing 'stats' key. Run train.py again.")
    _stats = artifacts["stats"]
    return _stats


def detect_anomaly(metrics: dict) -> dict:
    stats = _load_stats()

    max_z = 0.0
    for feature, value in metrics.items():
        if feature not in stats:
            continue
        mean, std = stats[feature]
        if std > 0:
            # One-sided: only flag values ABOVE baseline (low CPU/memory is healthy)
            z = max(0.0, (value - mean) / std)
            if z > max_z:
                max_z = z

    # Confidence: normalise z-score to 0-1 range (z=2.5 → 0.625, z=4 → 1.0)
    confidence = min(1.0, max_z / 4.0)
    is_anomaly = max_z >= ZSCORE_THRESHOLD

    return {
        "status":     "ANOMALY" if is_anomaly else "NORMAL",
        "confidence": round(confidence, 4),
    }
