from enum import Enum

class CheckpointType(Enum):

    BEST = "best"

    LAST = "last"

    PERIODIC = "periodic"
