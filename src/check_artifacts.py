import joblib
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACT_PATH = os.path.join(BASE_DIR, "artifacts.joblib")

artifacts = joblib.load(ARTIFACT_PATH)

iso = artifacts["isolation_forest"]

print("Number of features:", iso.n_features_in_)

# If trained with pandas (very likely)
if hasattr(iso, "feature_names_in_"):
    print("Feature names:", iso.feature_names_in_)
