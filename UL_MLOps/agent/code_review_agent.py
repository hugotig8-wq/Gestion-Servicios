import json

from pathlib import Path

from .llm.LLMEngine import LLMEngine

from .recomendation import Recomendation


class PyCodeReviewAgent:

    def __init__(

        self,

        llm: LLMEngine

    ):

        self.llm = llm

    def review(

        self,

        prompt: str,

        file_path: Path

    ) -> Recomendation:

        response = self.llm.generate(

            prompt

        )

        try:

            data = json.loads(

                response

            )

        except json.JSONDecodeError:

            data = {

                "severity":"LOW",

                "category":"Parsing",

                "title":"Invalid JSON",

                "explanation":response,

                "suggestion":"",

                "corrected_code":None,

                "line_start":None,

                "line_end":None

            }

        return Recomendation(

            file_path=file_path,

            severity=data["severity"],

            category=data["category"],

            title=data["title"],

            explanation=data["explanation"],

            suggestion=data["suggestion"],

            corrected_code=data["corrected_code"],

            line_start=data["line_start"],

            line_end=data["line_end"]

        )

    def review_summary(

        self,

        prompt: str

    ) -> str:

        return self.llm.generate(

            prompt

        )
