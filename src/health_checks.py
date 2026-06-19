"""
Health Check Probes
Implements production-grade health checks: /health, /live, /ready, /startup
"""

import os
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Tuple
from database import get_db_session, engine
from logger import logger


class HealthChecker:
    """Comprehensive health checking."""

    def __init__(self):
        """Initialize health checker."""
        self.startup_time = time.time()
        self.last_check: Dict = {}

    def check_database(self) -> Tuple[bool, str]:
        """
        Check database connectivity.
        
        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            session = get_db_session()
            session.execute("SELECT 1")
            session.close()
            return True, "Database connected"
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False, f"Database error: {str(e)}"

    def check_disk_space(self, min_mb: int = 100) -> Tuple[bool, str]:
        """
        Check available disk space.
        
        Args:
            min_mb: Minimum MB required
            
        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            stat = psutil.disk_usage('/')
            available_mb = stat.free / (1024 * 1024)
            
            if available_mb < min_mb:
                return False, f"Low disk space: {available_mb:.1f} MB available"
            
            return True, f"Disk space OK: {available_mb:.1f} MB available"
        except Exception as e:
            logger.error("Disk space check failed", error=str(e))
            return False, f"Disk check error: {str(e)}"

    def check_memory(self, max_percent: float = 90.0) -> Tuple[bool, str]:
        """
        Check available memory.
        
        Args:
            max_percent: Maximum memory usage percentage
            
        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            memory = psutil.virtual_memory()
            
            if memory.percent > max_percent:
                return False, f"High memory usage: {memory.percent:.1f}%"
            
            return True, f"Memory OK: {memory.percent:.1f}% used"
        except Exception as e:
            logger.error("Memory check failed", error=str(e))
            return False, f"Memory check error: {str(e)}"

    def check_cpu(self, max_percent: float = 95.0) -> Tuple[bool, str]:
        """
        Check CPU availability.
        
        Args:
            max_percent: Maximum CPU usage percentage
            
        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            if cpu_percent > max_percent:
                return False, f"High CPU usage: {cpu_percent:.1f}%"
            
            return True, f"CPU OK: {cpu_percent:.1f}% used"
        except Exception as e:
            logger.error("CPU check failed", error=str(e))
            return False, f"CPU check error: {str(e)}"

    def check_process(self) -> Tuple[bool, str]:
        """
        Check current process health.
        
        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            proc = psutil.Process(os.getpid())
            memory_mb = proc.memory_info().rss / (1024 * 1024)
            threads = proc.num_threads()
            
            # Warn if process memory is very high
            if memory_mb > 500:
                return False, f"Process memory high: {memory_mb:.1f} MB"
            
            return True, f"Process OK: {memory_mb:.1f} MB, {threads} threads"
        except Exception as e:
            logger.error("Process check failed", error=str(e))
            return False, f"Process check error: {str(e)}"

    def check_startup(self) -> Tuple[bool, str]:
        """
        Check if service has completed startup.
        Checks if sufficient time has passed since startup.
        
        Returns:
            Tuple of (is_ready, message)
        """
        startup_grace_period = 10  # seconds
        uptime = time.time() - self.startup_time
        
        if uptime < startup_grace_period:
            return False, f"Service starting up: {uptime:.1f}s elapsed"
        
        return True, f"Service fully started: {uptime:.1f}s uptime"

    def get_uptime_seconds(self) -> float:
        """Get service uptime in seconds."""
        return time.time() - self.startup_time

    def get_health(self) -> Dict:
        """
        Get comprehensive health status.
        This is for /health endpoint (detailed).
        
        Returns:
            Dictionary with health status
        """
        checks = {
            "database": self.check_database(),
            "disk": self.check_disk_space(),
            "memory": self.check_memory(),
            "cpu": self.check_cpu(),
            "process": self.check_process(),
        }

        # Determine overall status
        failed_checks = [name for name, (status, _) in checks.items() if not status]
        
        if not failed_checks:
            overall_status = "healthy"
        elif len(failed_checks) <= 1:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": self.get_uptime_seconds(),
            "components": {
                name: {
                    "status": "ok" if status else "error",
                    "message": message
                }
                for name, (status, message) in checks.items()
            }
        }

    def get_readiness(self) -> Dict:
        """
        Get readiness probe status.
        Checks if service is ready to accept requests.
        
        Returns:
            Dictionary with readiness status
        """
        startup_ok, startup_msg = self.check_startup()
        db_ok, db_msg = self.check_database()
        
        is_ready = startup_ok and db_ok
        
        return {
            "ready": is_ready,
            "timestamp": datetime.utcnow().isoformat(),
            "dependencies": {
                "startup": startup_ok,
                "database": db_ok
            },
            "message": startup_msg if not startup_ok else (db_msg if not db_ok else "Ready")
        }

    def get_liveness(self) -> Dict:
        """
        Get liveness probe status.
        Checks if service process is still running and responsive.
        
        Returns:
            Dictionary with liveness status
        """
        try:
            proc = psutil.Process(os.getpid())
            is_alive = proc.is_running() and not proc.status() == psutil.STATUS_ZOMBIE
            
            return {
                "alive": is_alive,
                "uptime_seconds": self.get_uptime_seconds(),
                "timestamp": datetime.utcnow().isoformat(),
                "pid": os.getpid(),
                "status": proc.status() if is_alive else "dead"
            }
        except Exception as e:
            logger.error("Liveness check failed", error=str(e))
            return {
                "alive": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global health checker instance
_health_checker = HealthChecker()


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    return _health_checker


def health_check() -> Dict:
    """Get comprehensive health status."""
    return _health_checker.get_health()


def readiness_check() -> Dict:
    """Get readiness status."""
    return _health_checker.get_readiness()


def liveness_check() -> Dict:
    """Get liveness status."""
    return _health_checker.get_liveness()


def startup_check() -> Dict:
    """Get startup status."""
    startup_ok, msg = _health_checker.check_startup()
    return {
        "ready": startup_ok,
        "message": msg,
        "timestamp": datetime.utcnow().isoformat()
    }
