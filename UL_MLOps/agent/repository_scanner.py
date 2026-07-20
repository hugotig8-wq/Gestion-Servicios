from pathlib import Path

from .file_filter import FileFilter


class RepositoryScanner:

    def __init__(

        self,

        root_path: str,

        file_filter: FileFilter | None = None

    ):

        self.root_path = Path(root_path)

        self.file_filter = (

            file_filter

            if file_filter is not None

            else FileFilter()

        )

    def resolve(

        self,

        relative_path: str

    ) -> Path:

        return self.root_path / relative_path

    
    def exists(

        self,

        file_path: Path

    ) -> bool:

        return file_path.exists()
    

    def scan(self):

        files = []

        for path in self.root_path.rglob("*"):

            if not path.is_file():

                continue

            if not self.file_filter.should_include(path):

                continue

            files.append(path)

        files.sort()

        return files

    def scan_by_extension(

        self,

        *extensions: str

    ):

        extensions = {

            extension.lower()

            for extension in extensions

        }

        return [

            file

            for file in self.scan()

            if file.suffix.lower() in extensions

        ]

    def read(

        self,

        file_path: Path,

        encoding: str = "utf-8"

    ):

        try:

            return file_path.read_text(

                encoding=encoding

            )

        except UnicodeDecodeError:

            return None

    def scan_with_content(self):

        result = []

        for file in self.scan():

            content = self.read(file)

            if content is None:

                continue

            result.append(

                {

                    "path": str(file),

                    "content": content

                }

            )

        return result
