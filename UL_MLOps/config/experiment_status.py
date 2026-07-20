from enum import Enum


class ExperimentStatus(Enum):

    CREATED = "created"

    RUNNING = "running"

    FINISHED = "finished"

    FAILED = "failed"

    STOPPED = "stopped"
