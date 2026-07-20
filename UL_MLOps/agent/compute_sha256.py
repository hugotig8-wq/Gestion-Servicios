import hashlib
from pathlib import Path


class CommputeSha256:

    def compute(self, old_path: Path = None, new_path: Path):
    
        hasher = hashlib.sha256()

        with open(

            new_path,

            "rb"

        ) as file:

            while chunk := file.read(8192):

                hasher.update(chunk)

        return hasher.hexdigest()
