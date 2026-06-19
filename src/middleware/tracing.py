import uuid
from flask import request
import structlog
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from config import settings

def init_tracing(app):
    resource = Resource.create({"service.name": settings.APP_NAME})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    
    # Configure OTLP exporter (assuming a local collector or Datadog/Jaeger)
    # The endpoint can be overridden via environment variables
    otlp_exporter = OTLPSpanExporter()
    span_processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(span_processor)
    
    FlaskInstrumentor().instrument_app(app)

    @app.before_request
    def bind_request_info():
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        current_span = trace.get_current_span()
        trace_id = current_span.get_span_context().trace_id
        
        # OpenTelemetry trace IDs are 128-bit ints, formatting them as hex
        trace_id_hex = format(trace_id, '032x') if trace_id else "unknown"
        
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            trace_id=trace_id_hex,
            path=request.path,
            method=request.method,
            remote_addr=request.remote_addr
        )

    @app.after_request
    def unbind_request_info(response):
        structlog.contextvars.clear_contextvars()
        return response
