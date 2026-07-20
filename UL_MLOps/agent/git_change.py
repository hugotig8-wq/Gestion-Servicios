from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GitChange:

    path: Path

    status: str

    sha256: str
