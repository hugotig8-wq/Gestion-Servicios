import hashlib
from pathlib import Path

def computeSha256(old_path: Path = None, new_path: Path)-> str:
        """
        Retorna el hash en chunks de 8192

        Parámetros
        ----------
        old_path
            Dirección antigua.

        new_path
            Dirección nueva.

        Retorna
        -------
        Retorna un hasher de SHA256.


        """
        hasher = hashlib.sha256()

        with open(

            new_path,

            "rb"

        ) as file:

            while chunk := file.read(8192):

                hasher.update(chunk)

        return hasher.hexdigest()
