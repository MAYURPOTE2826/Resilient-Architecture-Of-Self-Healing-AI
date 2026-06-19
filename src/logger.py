import logging
import logging.handlers
import os
import structlog
from config import settings

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_LOG_DIR = os.path.join(_BASE_DIR, "logs")
os.makedirs(_LOG_DIR, exist_ok=True)

def setup_logging():
    log_level = logging.getLevelName(settings.LOG_LEVEL.upper())

    # Standard library logging setup
    logging.basicConfig(
        format="%(message)s",
        stream=None,  # We will use handlers
        level=log_level,
    )

    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(_LOG_DIR, "system.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    
    stream_handler = logging.StreamHandler()
    
    # Configure processors
    processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.contextvars.merge_contextvars,
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json" else structlog.dev.ConsoleRenderer()
    ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    if settings.LOG_FORMAT == "json":
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
        )
    else:
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(),
        )
        
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

setup_logging()
logger = structlog.get_logger("self_healing_logger")
