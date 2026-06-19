"""
Unit tests for anomaly detection module.
"""
import pytest
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Create mock artifacts for testing
def create_mock_artifacts(tmp_path):
    """Create a mock artifacts.joblib file for testing."""
    import joblib
    
    artifacts = {
        "stats": {
            "cpu_usage": (50.0, 10.0),      # mean, std
            "memory_usage": (60.0, 15.0),
            "latency": (30.0, 8.0),
            "disk_io": (5.0, 2.0)
        }
    }
    
    artifact_path = tmp_path / "artifacts.joblib"
    joblib.dump(artifacts, artifact_path)
    return str(artifact_path)


@pytest.fixture
def mock_artifact_path(tmp_path, monkeypatch):
    """Create and set up mock artifact path."""
    artifact_path = create_mock_artifacts(tmp_path)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    return artifact_path


def test_anomaly_detector_normal_metrics(mock_artifact_path):
    """Test that normal metrics don't trigger anomaly."""
    from anomaly_detector import detect_anomaly
    
    metrics = {
        "cpu_usage": 52.0,       # Within 1 sigma
        "memory_usage": 65.0,    # Within 1 sigma
        "latency": 32.0,         # Within 1 sigma
        "disk_io": 5.1           # Within 1 sigma
    }
    
    result = detect_anomaly(metrics)
    
    assert result["status"] == "NORMAL"
    assert result["confidence"] >= 0.0
    assert result["confidence"] <= 1.0


def test_anomaly_detector_high_cpu(mock_artifact_path):
    """Test that high CPU triggers anomaly."""
    from anomaly_detector import detect_anomaly
    
    metrics = {
        "cpu_usage": 85.0,       # ~3.5 sigma above mean
        "memory_usage": 60.0,    # Normal
        "latency": 30.0,         # Normal
        "disk_io": 5.0           # Normal
    }
    
    result = detect_anomaly(metrics)
    
    assert result["status"] == "ANOMALY"
    assert result["confidence"] > 0.5


def test_anomaly_detector_multiple_anomalies(mock_artifact_path):
    """Test detection with multiple anomalous metrics."""
    from anomaly_detector import detect_anomaly
    
    metrics = {
        "cpu_usage": 90.0,       # High
        "memory_usage": 95.0,    # High
        "latency": 50.0,         # High
        "disk_io": 10.0          # High
    }
    
    result = detect_anomaly(metrics)
    
    assert result["status"] == "ANOMALY"
    assert result["confidence"] > 0.7


def test_anomaly_detector_confidence_range(mock_artifact_path):
    """Test that confidence is properly bounded 0-1."""
    from anomaly_detector import detect_anomaly
    
    test_cases = [
        {"cpu_usage": 50.0, "memory_usage": 60.0, "latency": 30.0, "disk_io": 5.0},
        {"cpu_usage": 75.0, "memory_usage": 70.0, "latency": 40.0, "disk_io": 7.0},
        {"cpu_usage": 95.0, "memory_usage": 90.0, "latency": 60.0, "disk_io": 15.0},
    ]
    
    for metrics in test_cases:
        result = detect_anomaly(metrics)
        assert 0.0 <= result["confidence"] <= 1.0, f"Confidence out of range: {result['confidence']}"


def test_anomaly_detector_empty_metrics(mock_artifact_path):
    """Test anomaly detector with empty metrics dict."""
    from anomaly_detector import detect_anomaly
    
    metrics = {}
    result = detect_anomaly(metrics)
    
    assert result["status"] == "NORMAL"
    assert result["confidence"] == 0.0


def test_anomaly_detector_partial_metrics(mock_artifact_path):
    """Test with subset of expected metrics."""
    from anomaly_detector import detect_anomaly
    
    metrics = {
        "cpu_usage": 85.0,
        "memory_usage": 60.0
        # latency and disk_io missing
    }
    
    result = detect_anomaly(metrics)
    
    # Should not crash and should process available metrics
    assert "status" in result
    assert "confidence" in result


def test_anomaly_detector_missing_artifact():
    """Test graceful failure when artifact is missing."""
    import tempfile
    import os as os_module
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        os_module.environ["DATA_DIR"] = tmp_dir
        
        from anomaly_detector import detect_anomaly
        
        # Force reload to pick up new DATA_DIR
        import anomaly_detector as ad_module
        ad_module._stats = None
        
        with pytest.raises(RuntimeError, match="Artifact file not found"):
            detect_anomaly({"cpu_usage": 50.0})
