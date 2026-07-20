from pathlib import Path

from .recommendation import Recommendation


class PromptBuilder:

    def __init__(

        self,

        max_characters: int = 8000

    ):

        self.max_characters = max_characters

    def build(

        self,

        file_path: Path,

        source_code: str

    ) -> str:

        source_code = self._truncate(

            source_code

        )

        return f"""
You are a senior software engineer.

Review the following source code.

Your response MUST be ONLY a valid JSON object.

Do not use Markdown.

Do not explain anything outside the JSON.

Return exactly this schema:

{{
    "severity":"LOW | MEDIUM | HIGH | CRITICAL",
    "category":"",
    "title":"",
    "explanation":"",
    "suggestion":"",
    "corrected_code":"",
    "line_start":0,
    "line_end":0
}}

File:

{file_path}

Source code:

{source_code}
"""

    def build_summary(

        self,

        recommendations: list[Recommendation]

    ) -> str:

        json_reports = []

        for recommendation in recommendations:

            json_reports.append(

                recommendation.to_json()

            )

        reports = ",\n".join(

            json_reports

        )

        return f"""
You are a software architect.

You have received multiple code reviews.

Return ONLY Markdown.

Produce:

# Executive Summary

# Main architectural issues

# Priority roadmap

Input:

[
{reports}
]
"""

    def _truncate(

        self,

        source_code: str

    ) -> str:

        if len(source_code) <= self.max_characters:

            return source_code

        return (

            source_code[:self.max_characters]

            +

            "\n\n...TRUNCATED..."
        )
