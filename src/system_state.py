from enum import Enum

class SystemState(Enum):
    NORMAL = 0
    DEGRADED = 1
    HEALING = 2
    RECOVERED = 3
