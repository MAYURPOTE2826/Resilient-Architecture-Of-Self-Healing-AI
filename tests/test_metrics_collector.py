"""
Unit tests for metrics_collector module.
"""
import pytest


class TestCollectMetrics:
    def test_returns_dict(self):
        from metrics_collector import collect_metrics
        assert isinstance(collect_metrics(), dict)

    def test_has_required_keys(self):
        from metrics_collector import collect_metrics
        required = {"cpu_usage", "memory_usage", "latency", "disk_io"}
        assert required.issubset(collect_metrics().keys())

    def test_cpu_in_valid_range(self):
        from metrics_collector import collect_metrics
        assert 0 <= collect_metrics()["cpu_usage"] <= 100

    def test_memory_in_valid_range(self):
        from metrics_collector import collect_metrics
        assert 0 <= collect_metrics()["memory_usage"] <= 100

    def test_latency_non_negative(self):
        from metrics_collector import collect_metrics
        assert collect_metrics()["latency"] >= 0

    def test_disk_io_non_negative(self):
        from metrics_collector import collect_metrics
        assert collect_metrics()["disk_io"] >= 0

    def test_all_values_are_numeric(self):
        from metrics_collector import collect_metrics
        for key, val in collect_metrics().items():
            assert isinstance(val, (int, float)), f"{key} should be numeric"

    def test_multiple_calls_stable(self):
        from metrics_collector import collect_metrics
        m1 = collect_metrics()
        m2 = collect_metrics()
        assert m1.keys() == m2.keys()
