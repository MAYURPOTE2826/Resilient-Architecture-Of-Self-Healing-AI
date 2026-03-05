from prometheus_client import  Counter, Gauge

# Counter metrics
anomalies_total = Counter(
    "anomalies_total",
    "Total number of anomalies detected"
)

healings_total = Counter(
    "healings_total",
    "Total number of healing actions executed"
)

# Gauge for system state
system_state = Gauge(
    "system_state",
    "System state: 0=NORMAL, 1=DEGRADED, 2=HEALING, 3=RECOVERED"
)


