"""
Unit tests for the anomaly_detector module.
"""
import pytest
import os


class TestAnomalyDetectorNormal:
    def test_normal_metrics_returns_normal_status(self, mock_artifact_path):
        from anomaly_detector import detect_anomaly
        metrics = {
            "cpu_usage": 52.0,
            "memory_usage": 65.0,
            "latency": 32.0,
            "disk_io": 5.1,
        }
        result = detect_anomaly(metrics)
        assert result["status"] == "NORMAL"

    def test_confidence_in_valid_range_normal(self, mock_artifact_path):
        from anomaly_detector import detect_anomaly
        result = detect_anomaly({"cpu_usage": 50.0, "memory_usage": 60.0, "latency": 30.0, "disk_io": 5.0})
        assert 0.0 <= result["confidence"] <= 1.0

    def test_empty_metrics_returns_normal(self, mock_artifact_path):
        from anomaly_detector import detect_anomaly
        result = detect_anomaly({})
        assert result["status"] == "NORMAL"
        assert result["confidence"] == 0.0

    def test_partial_metrics_doesnt_crash(self, mock_artifact_path):
        from anomaly_detector import detect_anomaly
        result = detect_anomaly({"cpu_usage": 50.0})
        assert "status" in result
        assert "confidence" in result


class TestAnomalyDetectorAnomaly:
    def test_high_cpu_triggers_anomaly(self, mock_artifact_path):
        from anomaly_detector import detect_anomaly
        result = detect_anomaly({
            "cpu_usage": 88.0,     # ~3.8 sigma above mean
            "memory_usage": 60.0,
            "latency": 30.0,
            "disk_io": 5.0,
        })
        assert result["status"] == "ANOMALY"
        assert result["confidence"] > 0.5

    def test_multiple_anomalies_high_confidence(self, mock_artifact_path):
        from anomaly_detector import detect_anomaly
        result = detect_anomaly({
            "cpu_usage": 90.0,
            "memory_usage": 95.0,
            "latency": 50.0,
            "disk_io": 10.0,
        })
        assert result["status"] == "ANOMALY"
        assert result["confidence"] > 0.7

    def test_confidence_bounded_above_1(self, mock_artifact_path):
        from anomaly_detector import detect_anomaly
        result = detect_anomaly({
            "cpu_usage": 9999.0,
            "memory_usage": 9999.0,
            "latency": 9999.0,
            "disk_io": 9999.0,
        })
        assert result["confidence"] <= 1.0

    def test_unknown_metrics_ignored_gracefully(self, mock_artifact_path):
        from anomaly_detector import detect_anomaly
        result = detect_anomaly({"unknown_metric": 100.0})
        assert result["status"] == "NORMAL"


class TestAnomalyDetectorEdgeCases:
    def test_missing_artifact_raises_runtime_error(self, tmp_path, monkeypatch):
        import anomaly_detector as ad
        monkeypatch.setenv("DATA_DIR", str(tmp_path))
        ad._stats = None  # force reload
        with pytest.raises(RuntimeError, match="Artifact file not found"):
            ad.detect_anomaly({"cpu_usage": 50.0})

    def test_multiple_calls_are_stable(self, mock_artifact_path):
        from anomaly_detector import detect_anomaly
        m = {"cpu_usage": 50.0, "memory_usage": 60.0, "latency": 30.0, "disk_io": 5.0}
        r1 = detect_anomaly(m)
        r2 = detect_anomaly(m)
        assert r1["status"] == r2["status"]
        assert r1["confidence"] == r2["confidence"]
