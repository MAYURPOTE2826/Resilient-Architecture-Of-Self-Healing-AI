import hashlib
import os

import joblib
import pandas as pd

from logger import logger

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.environ.get("DATA_DIR", BASE_DIR)
ARTIFACT_PATH = os.path.join(DATA_DIR, "artifacts.joblib")

_model = None


def _load_model():
    global _model
    if _model is not None:
        return _model

    if not os.path.exists(ARTIFACT_PATH):
        raise RuntimeError(f"Artifact file not found: {ARTIFACT_PATH}. Run training first.")

    # Log SHA-256 so operators can detect tampering against a known-good hash
    with open(ARTIFACT_PATH, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()
    logger.info(f"Loading fault classifier from {ARTIFACT_PATH} (SHA256: {sha256})")

    try:
        artifacts = joblib.load(ARTIFACT_PATH)
        _model = artifacts["random_forest"]
    except KeyError:
        raise RuntimeError("Artifact file is missing 'random_forest' key.")

    return _model


def classify_fault(metrics: dict) -> str:
    model = _load_model()
    X = pd.DataFrame([metrics])
    return str(model.predict(X)[0])  # cast np.str_ → str to avoid leaking numpy types
