import threading
from wsgiref.simple_server import make_server, WSGIRequestHandler
from prometheus_client import Counter, Gauge, make_wsgi_app

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


class _SilentHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass  # suppress request logs


def start_exporter(port: int = 8000) -> None:
    """Start the Prometheus HTTP metrics server on the given port as a daemon thread."""
    app = make_wsgi_app()
    httpd = make_server("", port, app, handler_class=_SilentHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
