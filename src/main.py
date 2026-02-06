import time
from collections import deque

from metrics_collector import collect_metrics
from anomaly_detector import detect_anomaly
from fault_classifier import classify_fault
from healing_engine import heal
from system_state import SystemState
from logger import logger
from prometheus_exporter import (
    start_exporter,
    anomalies_total,
    healings_total,
    system_state
)

# Start Prometheus exporter
start_exporter()

WINDOW_SIZE = 5
MIN_ANOMALIES = 3
CONFIDENCE_THRESHOLD = 0.01

history = deque(maxlen=WINDOW_SIZE)
state = SystemState.NORMAL

while True:
    metrics = collect_metrics()
    logger.info(f"Metrics: {metrics}")

    anomaly = detect_anomaly(metrics)
    logger.info(f"Anomaly: {anomaly}")

    if anomaly["status"] == "ANOMALY" and anomaly["confidence"] > CONFIDENCE_THRESHOLD:
        anomalies_total.inc()
        history.append(1)
    else:
        history.append(0)

    system_state.set(state.value)

    if sum(history) >= MIN_ANOMALIES:
        state = SystemState.DEGRADED
        system_state.set(state.value)

        fault = classify_fault(metrics)
        state = SystemState.HEALING
        system_state.set(state.value)

        heal(fault, anomaly["confidence"])

        healings_total.inc()

        state = SystemState.RECOVERED
        system_state.set(state.value)

        history.clear()

    time.sleep(5)
