from pathlib import Path


class FileFilter:

    def __init__(

        self,

        max_size_mb: int = 2

    ):

        self.max_size = max_size_mb * 1024 * 1024

        self.allowed_extensions = {

            ".py"

            #".js",

            #".jsx",

            #".ts",

            #".tsx",

            #".json",

            #".yaml",

            #".yml",

            #".toml",

            #".md"

        }

        self.ignored_directories = {

            ".git",

            ".github",

            ".next",

            ".vscode",

            ".idea",

            "__pycache__",

            "node_modules",

            "dist",

            "build",

            ".venv",

            "venv",

            ".pytest_cache",

            ".mypy_cache",

            ".cache",
            
            "agents",

            "SmolLM3",

            "app",

            "db",

            "lib",

            "hooks",

            "src"
            

        }

        self.ignored_files = {

            ".DS_Store",

            "package-lock.json",

            "yarn.lock",

            "pnpm-lock.yaml"

        }

    def should_include(

        self,

        path: Path

    ) -> bool:

        if not path.is_file():

            return False

        if path.name in self.ignored_files:

            return False

        if path.suffix.lower() not in self.allowed_extensions:

            return False

        if any(

            part in self.ignored_directories

            for part in path.parts

        ):

            return False

        if path.stat().st_size > self.max_size:

            return False

        return True
