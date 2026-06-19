from logger import logger

def classify_fault(metrics: dict) -> str:
    # Rule-based classification based on new metric keys
    cpu = metrics.get("cpu", 0)
    memory = metrics.get("memory", 0)
    disk = metrics.get("disk", 0)
    ping = metrics.get("ping", 0)

    if cpu > 90:
        return "CPU_OVERLOAD"
    elif memory > 90:
        return "MEMORY_OVERLOAD"
    elif disk > 95:
        return "DISK_OVERLOAD"
    elif ping > 150:
        return "NETWORK_LATENCY"
    
    return "NORMAL"
