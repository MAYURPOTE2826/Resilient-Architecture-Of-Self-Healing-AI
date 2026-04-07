FROM python:3.12-slim

WORKDIR /app

COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source files
COPY src/ .

# Copy ML artifacts into the data directory
RUN mkdir -p /app/data
COPY artifacts.joblib /app/data/artifacts.joblib

ENV DATA_DIR=/app/data

# Run as non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 5000

# Docker will restart the container if the health check fails 3 times
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/status')" || exit 1

CMD ["python", "api.py"]
