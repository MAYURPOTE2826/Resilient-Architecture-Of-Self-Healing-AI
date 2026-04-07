import time
from collections import deque

from metrics_collector import collect_metrics
from anomaly_detector import detect_anomaly
from fault_classifier import classify_fault
from healing_engine import heal
from system_state import SystemState
from logger import logger
from database import init_db
from prometheus_exporter import (
    start_exporter,
    anomalies_total,
    healings_total,
    system_state,
)

WINDOW_SIZE = 5
MIN_ANOMALIES = 3
CONFIDENCE_THRESHOLD = 0.6   # Z-score: 2.5σ → 0.625 confidence


def main() -> None:
    # Start Prometheus HTTP metrics server on port 8000
    start_exporter()

    # Ensure database table exists
    init_db()

    history = deque(maxlen=WINDOW_SIZE)
    state = SystemState.NORMAL

    logger.info("Self-Healing AI standalone engine started")

    while True:
        try:
            metrics = collect_metrics()
            logger.info(f"Metrics: {metrics}")

            anomaly = detect_anomaly(metrics)
            logger.info(f"Anomaly: {anomaly}")

            if anomaly["status"] == "ANOMALY" and anomaly["confidence"] > CONFIDENCE_THRESHOLD:
                fault = classify_fault(metrics)
                logger.info(f"Fault classified: {fault}")
                anomalies_total.inc()
                history.append(1)
            else:
                fault = "normal"
                history.append(0)

            system_state.set(state.value)

            if sum(history) >= MIN_ANOMALIES:
                state = SystemState.DEGRADED
                system_state.set(state.value)

                state = SystemState.HEALING
                system_state.set(state.value)

                heal(fault, anomaly["confidence"])
                healings_total.inc()

                state = SystemState.RECOVERED
                system_state.set(state.value)

                history.clear()

                # Return to NORMAL after recovery
                state = SystemState.NORMAL
                system_state.set(state.value)

        except Exception as e:
            logger.error(f"Engine error: {e}")
            # Reset state and history so next cycle starts clean
            state = SystemState.NORMAL
            system_state.set(state.value)
            history.clear()

        finally:
            time.sleep(5)


if __name__ == "__main__":
    main()
