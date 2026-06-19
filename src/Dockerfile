# Stage 1: Builder - Install dependencies into a clean virtual environment
FROM python:3.12-slim as builder

WORKDIR /app

COPY src/requirements.txt .

# Create a virtual environment and install dependencies into it.
# This isolates packages and makes them easy to copy to the final stage.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt


# Stage 2: Final Image - Create the lean, production-ready runtime image
FROM python:3.12-slim

WORKDIR /app

# Create the non-root user first for security
RUN useradd -m appuser

# Copy the isolated virtual environment from the builder stage.
# This layer only changes if requirements.txt changes.
COPY --from=builder /opt/venv /opt/venv

# Copy application source files
COPY src/ .

# Copy ML artifacts into the data directory
# This layer only changes when the model is retrained.
RUN mkdir -p /app/data
COPY src/artifacts.joblib /app/data/artifacts.joblib

ENV DATA_DIR=/app/data
# Make the venv's Python the default for all subsequent commands
ENV PATH="/opt/venv/bin:$PATH"

# Set correct ownership for all application files and switch to the non-root user
RUN chown -R appuser /app
USER appuser

EXPOSE 5000

# The health check ensures Docker can restart the container if it becomes unresponsive.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/status', timeout=5)" || exit 1

CMD ["python", "api.py"]
