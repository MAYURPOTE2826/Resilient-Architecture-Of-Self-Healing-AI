import multiprocessing

# Enterprise-grade Gunicorn configuration for Render deployment
# We must use exactly 1 worker to avoid multiple background ML threads and SQLite database locks
workers = 1

# We can use multiple threads for handling concurrent web requests safely
threads = 4

bind = "0.0.0.0:5000"

timeout = 120

# Standardized logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Ensure we cleanly shutdown the background thread on exit if possible
# (Handled by daemon=True in Python, but graceful timeout here gives requests a chance to finish)
graceful_timeout = 30
