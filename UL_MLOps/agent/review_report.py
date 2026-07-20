from pathlib import Path
from datetime import datetime
import json

from agents.recommendation import Recommendation


class ReviewReport:

    def __init__(

        self,

        output_directory: str = "reports"

    ):

        self.output_directory = Path(

            output_directory

        )

        self.output_directory.mkdir(

            parents=True,

            exist_ok=True

        )

    def save(

        self,

        recommendations: list[Recommendation],

        summary: str

    ):

        timestamp = datetime.now().strftime(

            "%Y%m%d_%H%M%S"

        )

        report_directory = (

            self.output_directory

            /

            f"review_{timestamp}"

        )

        report_directory.mkdir(

            parents=True,

            exist_ok=True

        )

        self._save_markdown(

            report_directory,

            recommendations,

            summary

        )

        self._save_json(

            report_directory,

            recommendations,

            summary

        )

    def _save_markdown(

        self,

        directory: Path,

        recommendations: list[Recommendation],

        summary: str

    ):

        markdown_file = (

            directory

            /

            "report.md"

        )

        with open(

            markdown_file,

            "w",

            encoding="utf-8"

        ) as file:

            file.write(

                "# Code Review Report\n\n"

            )

            file.write(

                "## Executive Summary\n\n"

            )

            file.write(

                summary

            )

            file.write(

                "\n\n---\n\n"

            )

            file.write(

                "## Recommendations\n\n"

            )

            for recommendation in recommendations:

                file.write(

                    recommendation.to_markdown()

                )

                file.write(

                    "\n\n---\n\n"

                )

    def _save_json(

        self,

        directory: Path,

        recommendations: list[Recommendation],

        summary: str

    ):

        json_file = (

            directory

            /

            "report.json"

        )

        data = {

            "generated_at":

                datetime.utcnow().isoformat(),

            "summary":

                summary,

            "recommendations": [

                {

                    "file":

                        str(

                            recommendation.file_path

                        ),

                    "severity":

                        recommendation.severity,

                    "category":

                        recommendation.category,

                    "title":

                        recommendation.title,

                    "explanation":

                        recommendation.explanation,

                    "suggestion":

                        recommendation.suggestion,

                    "corrected_code":

                        recommendation.corrected_code,

                    "line_start":

                        recommendation.line_start,

                    "line_end":

                        recommendation.line_end

                }

                for recommendation

                in recommendations

            ]

        }

        with open(

            json_file,

            "w",

            encoding="utf-8"

        ) as file:

            json.dump(

                data,

                file,

                indent=4,

                ensure_ascii=False

        )
