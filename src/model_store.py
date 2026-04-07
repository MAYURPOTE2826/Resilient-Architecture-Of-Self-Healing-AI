import hashlib
import os

import joblib

from logger import logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("DATA_DIR", BASE_DIR)
ARTIFACT_PATH = os.path.join(DATA_DIR, "artifacts.joblib")

_artifacts = None


def _load_artifacts():
    global _artifacts
    if _artifacts is not None:
        return _artifacts

    if not os.path.exists(ARTIFACT_PATH):
        raise RuntimeError(f"Artifact file not found: {ARTIFACT_PATH}. Run training first.")

    # Chunked SHA-256 — avoids loading the entire file into RAM just for hashing
    sha256 = hashlib.sha256()
    with open(ARTIFACT_PATH, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    logger.info(f"Loading artifacts from {ARTIFACT_PATH} (SHA256: {sha256.hexdigest()})")

    _artifacts = joblib.load(ARTIFACT_PATH)
    return _artifacts


def get_isolation_forest():
    artifacts = _load_artifacts()
    try:
        return artifacts["isolation_forest"]
    except KeyError:
        raise RuntimeError("Artifact file is missing 'isolation_forest' key.")


def get_random_forest():
    artifacts = _load_artifacts()
    try:
        return artifacts["random_forest"]
    except KeyError:
        raise RuntimeError("Artifact file is missing 'random_forest' key.")
