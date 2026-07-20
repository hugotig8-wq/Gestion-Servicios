from dataclasses import dataclass
from pathlib import Path


@dataclass
class Recommendation:

    file_path: Path

    severity: str

    category: str

    title: str

    explanation: str

    suggestion: str

    corrected_code: str | None = None

    line_start: int | None = None

    line_end: int | None = None

    def to_markdown(self) -> str:

        markdown = f"""
        ## {self.severity} - {self.title}

        **Archivo**

        {self.file_path}

        **Categoría**

        {self.category}

        **Problema**

        {self.explanation}

        **Sugerencia**

        {self.suggestion}
    
        """
        if self.corrected_code:

            markdown += f"""

            ```python
            {self.corrected_code}
            """

        if (

            self.line_start is not None

            and

           self.line_end is not None

        ):

            markdown += f"""
            Lines:
                {self.line_start}-{self.line_end} 
            """
        return markdown
