import hashlib
from pathlib import Path


class CommputeSha256():

    def encriptar(self, file_path: Path):
    
        hasher = hashlib.sha256()

        with open(

            file_path,

            "rb"

        ) as file:

            while chunk := file.read(8192):

                hasher.update(chunk)

        return hasher.hexdigest()
