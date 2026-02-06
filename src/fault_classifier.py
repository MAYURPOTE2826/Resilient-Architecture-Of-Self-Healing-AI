import joblib
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACT_PATH = os.path.join(BASE_DIR, "artifacts.joblib")

artifacts = joblib.load(ARTIFACT_PATH)
model = artifacts["random_forest"]

def classify_fault(metrics):
    X = pd.DataFrame([metrics])
    return model.predict(X)[0]
