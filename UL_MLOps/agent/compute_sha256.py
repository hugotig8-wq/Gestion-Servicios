import hashlib
from pathlib import Path

def compute_sha256(old_path: Path = None, new_path: Path)-> str:
    
        hasher = hashlib.sha256()

        with open(

            new_path,

            "rb"

        ) as file:

            while chunk := file.read(8192):

                hasher.update(chunk)

        return hasher.hexdigest()
