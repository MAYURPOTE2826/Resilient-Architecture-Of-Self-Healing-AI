"""
Unit tests for metrics collector module.
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))


def test_collect_metrics_returns_dict():
    """Test that metrics collector returns a dictionary."""
    from metrics_collector import collect_metrics
    
    metrics = collect_metrics()
    
    assert isinstance(metrics, dict)


def test_collect_metrics_has_required_keys():
    """Test that all required metrics are present."""
    from metrics_collector import collect_metrics
    
    metrics = collect_metrics()
    required_keys = {"cpu_usage", "memory_usage", "latency", "disk_io"}
    
    assert required_keys.issubset(metrics.keys())


def test_collect_metrics_cpu_in_range():
    """Test that CPU usage is between 0 and 100."""
    from metrics_collector import collect_metrics
    
    metrics = collect_metrics()
    
    assert 0 <= metrics["cpu_usage"] <= 100


def test_collect_metrics_memory_in_range():
    """Test that memory usage is between 0 and 100."""
    from metrics_collector import collect_metrics
    
    metrics = collect_metrics()
    
    assert 0 <= metrics["memory_usage"] <= 100


def test_collect_metrics_latency_positive():
    """Test that latency is non-negative."""
    from metrics_collector import collect_metrics
    
    metrics = collect_metrics()
    
    assert metrics["latency"] >= 0


def test_collect_metrics_disk_io_non_negative():
    """Test that disk IO is non-negative."""
    from metrics_collector import collect_metrics
    
    metrics = collect_metrics()
    
    assert metrics["disk_io"] >= 0


def test_collect_metrics_values_are_numeric():
    """Test that all metrics are numeric values."""
    from metrics_collector import collect_metrics
    
    metrics = collect_metrics()
    
    for key, value in metrics.items():
        assert isinstance(value, (int, float)), f"{key} should be numeric"


def test_collect_metrics_reproducible():
    """Test that multiple calls work correctly."""
    from metrics_collector import collect_metrics
    
    # Should be callable multiple times without error
    m1 = collect_metrics()
    m2 = collect_metrics()
    
    assert isinstance(m1, dict)
    assert isinstance(m2, dict)
    assert m1.keys() == m2.keys()
