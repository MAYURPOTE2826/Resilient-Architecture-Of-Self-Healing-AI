import joblib
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACT_PATH = os.path.join(BASE_DIR, "artifacts.joblib")

artifacts = joblib.load(ARTIFACT_PATH)
model = artifacts["isolation_forest"]

def detect_anomaly(metrics):
    X = pd.DataFrame([metrics])
    prediction = model.predict(X)[0]
    score = model.decision_function(X)[0]

    return {
        "status": "ANOMALY" if prediction == -1 else "NORMAL",
        "confidence": abs(score)
    }
