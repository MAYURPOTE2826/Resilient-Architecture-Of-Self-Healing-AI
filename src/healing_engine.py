import threading
import time
import os
from datetime import datetime, timezone

import psutil

from alert_service import send_alert
from database import get_connection, prune_events
from logger import logger
from priority_manager import get_priority


# ==========================================
# Thread Safety + Cooldown
# ==========================================

_heal_lock = threading.Lock()
_last_heal_time: float = 0.0

_COOLDOWN = 60  # seconds


# ==========================================
# Protected Windows Processes
# NEVER terminate these
# ==========================================

PROTECTED_PROCESSES = [
    "System",
    "Idle",
    "Registry",
    "svchost.exe",
    "explorer.exe",
    "wininit.exe",
    "csrss.exe",
    "services.exe",
    "lsass.exe"
]


# ==========================================
# Main Healing Function
# ==========================================

def heal(fault_type: str, confidence: float) -> None:

    global _last_heal_time

    now = time.time()

    with _heal_lock:

        if now - _last_heal_time < _COOLDOWN:

            logger.warning("Healing skipped due to cooldown")

            return

        _last_heal_time = now

    logger.info(f"System healing triggered for fault: {fault_type}")

    # ======================================
    # Intelligent Healing Decisions
    # ======================================

    try:

        if fault_type == "CPU_OVERLOAD":

            handle_cpu_overload()

        elif fault_type == "MEMORY_OVERLOAD":

            handle_memory_overload()

        elif fault_type == "NETWORK_LATENCY":

            handle_network_issue()

        elif fault_type == "DOCKER_CRASH":

            handle_docker_crash()

        else:

            logger.warning(f"No healing strategy for: {fault_type}")

    except Exception as e:

        logger.error(f"Healing failed: {e}")

    # ======================================
    # Send Alert
    # ======================================

    subject = "Self-Healing System Alert"

    message = f"""
Self-Healing Action Triggered

Fault Detected : {fault_type}
Confidence     : {confidence:.4f}
Action Taken   : Automated Recovery
Time           : {time.ctime()}
"""

    send_alert(subject, message)

    # ======================================
    # Save Event
    # ======================================

    save_event(
        "HEALING",
        fault_type,
        confidence
    )


# ==========================================
# CPU OVERLOAD HEALING
# ==========================================

def handle_cpu_overload():

    logger.warning("CPU overload detected")

    terminated = []

    for proc in psutil.process_iter(
        ['pid', 'name', 'cpu_percent']
    ):

        try:

            pid = proc.info['pid']
            name = proc.info['name']
            cpu = proc.info['cpu_percent']

            if not name:
                continue

            # Skip protected processes
            if name in PROTECTED_PROCESSES:
                continue

            priority = get_priority(name)

            # Kill only LOW priority heavy CPU tasks
            if priority == "LOW" and cpu > 5:

                logger.info(
                    f"[AI ENGINE] AI Action: LOW priority process terminated: "
                    f"{name} | CPU={cpu}%"
                )

                proc.terminate()

                terminated.append(name)

                save_event(
                    "PROCESS_TERMINATED",
                    f"AI Action: Terminated {name}",
                    cpu
                )

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):

            continue

        except Exception as e:

            logger.error(
                f"CPU healing failed for process: {e}"
            )

    logger.info(
        f"CPU healing completed. "
        f"Terminated: {terminated}"
    )


# ==========================================
# MEMORY OVERLOAD HEALING
# ==========================================

def handle_memory_overload():

    logger.warning("Memory overload detected")

    terminated = []

    for proc in psutil.process_iter(
        ['pid', 'name', 'memory_percent']
    ):

        try:

            name = proc.info['name']
            memory = proc.info['memory_percent']

            if not name:
                continue

            if name in PROTECTED_PROCESSES:
                continue

            priority = get_priority(name)

            # Kill only LOW priority memory-heavy tasks
            if priority == "LOW" and memory > 5:

                logger.info(
                    f"Terminating LOW priority process: "
                    f"{name} | Memory={memory:.2f}%"
                )

                proc.terminate()

                terminated.append(name)

                save_event(
                    "PROCESS_TERMINATED",
                    name,
                    memory
                )

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):

            continue

        except Exception as e:

            logger.error(
                f"Memory healing failed: {e}"
            )

    logger.info(
        f"Memory healing completed. "
        f"Terminated: {terminated}"
    )


# ==========================================
# NETWORK LATENCY HEALING
# ==========================================

def handle_network_issue():

    logger.warning(
        "Network latency detected. "
        "Restarting network connection"
    )

    try:

        # Windows network reset
        os.system("ipconfig /release")
        os.system("ipconfig /renew")

        logger.info("Network reset completed")

        save_event(
            "NETWORK_RESET",
            "NETWORK_LATENCY",
            1.0
        )

    except Exception as e:

        logger.error(
            f"Network healing failed: {e}"
        )


# ==========================================
# DOCKER AUTO-HEALING
# ==========================================

def handle_docker_crash():

    logger.warning("[AI ENGINE] Docker container crash detected. Initiating Auto-Healing.")

    try:

        logger.info("Running: docker restart flask-app")
        os.system("docker restart flask-app")

        logger.info("[AI ENGINE] Docker Auto-Healing completed")

        save_event(
            "CONTAINER_RESTARTED",
            "AI Action: Restarted flask-app",
            1.0
        )

    except Exception as e:

        logger.error(f"Docker healing failed: {e}")

# ==========================================
# SAVE EVENT TO DATABASE
# ==========================================

from database import get_db_session, Event
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def save_event(
    event_type: str,
    fault_type: str,
    confidence: float
) -> None:

    session = get_db_session()
    try:
        new_event = Event(
            event_type=event_type,
            fault_type=fault_type,
            confidence=confidence,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        session.add(new_event)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to save event to database: {e}")
        raise e
    finally:
        session.close()

    # Prevent DB from growing forever
    prune_events()