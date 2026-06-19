"""
Graceful Shutdown Manager
Implements graceful shutdown handling for clean service termination.
"""

import signal
import atexit
import threading
import time
from typing import Callable, List, Optional
from logger import logger


class ShutdownManager:
    """Manage graceful shutdown of the service."""

    def __init__(self, timeout_seconds: int = 30):
        """
        Initialize shutdown manager.
        
        Args:
            timeout_seconds: Maximum time to wait for cleanup
        """
        self.timeout_seconds = timeout_seconds
        self.is_shutting_down = False
        self._shutdown_lock = threading.RLock()
        self._handlers: List[Callable] = []
        self._started_cleanup = False

    def register_handler(self, handler: Callable, name: str = ""):
        """
        Register a cleanup handler.
        Handlers are called in reverse order of registration.
        
        Args:
            handler: Callable to execute during shutdown
            name: Name of handler for logging
        """
        with self._shutdown_lock:
            self._handlers.append((handler, name or handler.__name__))
            logger.info("Shutdown handler registered", name=name or handler.__name__)

    def shutdown(self, signum: Optional[int] = None, frame: Optional[object] = None):
        """
        Trigger graceful shutdown.
        
        Args:
            signum: Signal number (for signal handler)
            frame: Stack frame (for signal handler)
        """
        with self._shutdown_lock:
            if self.is_shutting_down:
                # Already shutting down, ignore subsequent signals
                logger.warning("Shutdown already in progress, ignoring signal")
                return
            
            self.is_shutting_down = True
            signal_name = signal.Signals(signum).name if signum else "API_CALL"
            logger.info("Graceful shutdown initiated", signal=signal_name)

        # Run cleanup handlers
        self._run_cleanup_handlers()

    def _run_cleanup_handlers(self):
        """Run all registered cleanup handlers."""
        if self._started_cleanup:
            return
        
        self._started_cleanup = True
        
        # Run handlers in reverse order (LIFO)
        for handler, name in reversed(self._handlers):
            try:
                logger.info("Executing shutdown handler", name=name)
                start = time.time()
                
                handler()
                
                duration = time.time() - start
                logger.info("Shutdown handler completed", name=name, duration_seconds=duration)
            except Exception as e:
                logger.error("Shutdown handler failed", name=name, error=str(e))

    def wait_for_shutdown(self) -> bool:
        """
        Wait for shutdown signal.
        Returns True if shutdown was graceful, False if timeout.
        """
        try:
            # This will block until a signal is received
            while not self.is_shutting_down:
                time.sleep(0.1)
            
            return True
        except KeyboardInterrupt:
            self.shutdown()
            return False

    def mark_shutdown_complete(self):
        """Mark shutdown as complete (for monitoring)."""
        with self._shutdown_lock:
            logger.info("Graceful shutdown complete")


# Global shutdown manager instance
_shutdown_manager = ShutdownManager()


def get_shutdown_manager() -> ShutdownManager:
    """Get the global shutdown manager."""
    return _shutdown_manager


def register_shutdown_handler(handler: Callable, name: str = ""):
    """Register a shutdown handler."""
    _shutdown_manager.register_handler(handler, name)


def trigger_shutdown(signum: Optional[int] = None, frame: Optional[object] = None):
    """Trigger graceful shutdown."""
    _shutdown_manager.shutdown(signum, frame)


def setup_signal_handlers():
    """
    Setup signal handlers for graceful shutdown.
    Should be called at application startup.
    """
    # Handle SIGTERM (default termination signal)
    signal.signal(signal.SIGTERM, trigger_shutdown)
    
    # Handle SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, trigger_shutdown)
    
    # On Windows, these signals are not available
    try:
        # Handle SIGHUP (hangup signal)
        signal.signal(signal.SIGHUP, trigger_shutdown)
    except (AttributeError, ValueError):
        pass
    
    try:
        # Handle SIGUSR1 (user-defined signal)
        signal.signal(signal.SIGUSR1, trigger_shutdown)
    except (AttributeError, ValueError):
        pass
    
    logger.info("Signal handlers registered for graceful shutdown")


def register_database_cleanup(db_engine):
    """Register database cleanup handler."""
    def cleanup():
        try:
            logger.info("Cleaning up database connections")
            db_engine.dispose()
            logger.info("Database connections cleaned up")
        except Exception as e:
            logger.error("Failed to clean up database connections", error=str(e))
    
    register_shutdown_handler(cleanup, "database_cleanup")


def register_thread_cleanup(thread_refs: List[threading.Thread]):
    """
    Register thread cleanup handler.
    
    Args:
        thread_refs: List of thread references to wait for
    """
    def cleanup():
        logger.info("Waiting for background threads", count=len(thread_refs))
        
        for thread in thread_refs:
            if thread.is_alive():
                thread.join(timeout=5)
                if thread.is_alive():
                    logger.warning("Thread did not terminate gracefully", thread_name=thread.name)
        
        logger.info("Background threads cleanup complete")
    
    register_shutdown_handler(cleanup, "thread_cleanup")


def register_cache_cleanup(cache):
    """Register cache cleanup handler."""
    def cleanup():
        try:
            logger.info("Clearing caches")
            if hasattr(cache, 'clear'):
                cache.clear()
            logger.info("Caches cleared")
        except Exception as e:
            logger.error("Failed to clear caches", error=str(e))
    
    register_shutdown_handler(cleanup, "cache_cleanup")


class GracefulShutdownContext:
    """Context manager for graceful shutdown."""

    def __init__(self, name: str = "operation"):
        """
        Initialize context.
        
        Args:
            name: Name of operation for logging
        """
        self.name = name
        self.start_time = None

    def __enter__(self):
        """Enter context."""
        self.start_time = time.time()
        logger.info("Operation started", operation=self.name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        duration = time.time() - self.start_time
        
        if exc_type is None:
            logger.info("Operation completed", operation=self.name, duration_seconds=duration)
        else:
            logger.error(
                "Operation failed",
                operation=self.name,
                duration_seconds=duration,
                error_type=exc_type.__name__,
                error=str(exc_val)
            )

        return False  # Don't suppress exceptions


def create_shutdown_handler(cleanup_func: Callable, timeout: int = 5) -> Callable:
    """
    Create a timeout-aware shutdown handler.
    
    Args:
        cleanup_func: Function to call for cleanup
        timeout: Maximum seconds to wait
        
    Returns:
        Handler function
    """
    def handler():
        try:
            logger.info("Running cleanup", timeout_seconds=timeout)
            
            # Run cleanup in thread with timeout
            thread = threading.Thread(target=cleanup_func, daemon=False)
            thread.start()
            thread.join(timeout=timeout)
            
            if thread.is_alive():
                logger.warning("Cleanup did not complete within timeout")
            else:
                logger.info("Cleanup completed successfully")
        except Exception as e:
            logger.error("Cleanup failed", error=str(e))
    
    return handler


# Register atexit handler as fallback
atexit.register(lambda: _shutdown_manager.mark_shutdown_complete())
