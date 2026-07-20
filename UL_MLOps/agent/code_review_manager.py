from pathlib import Path

from .repository_scanner import RepositoryScanner
from .prompt_builder import PromptBuilder
from .review_report import ReviewReport
from .recommendation import Recommendation
from .git_change import GitChange


class CodeReviewManager:

    def __init__(

        self,

        review_agent,

        scanner: RepositoryScanner,

        prompt_builder: PromptBuilder,

        report: ReviewReport

    ):

        self.review_agent = review_agent

        self.scanner = scanner

        self.prompt_builder = prompt_builder

        self.report = report

    def review_repository(

        self

    ) -> list[Recommendation]:

        recommendations = []

        files = self.scanner.scan()

        for file_path in files:

            if not self.scanner.exists(

                file_path

            ):

                continue

            recommendation = self.review_file(

                file_path

            )

            if recommendation is not None:

                recommendations.append(

                    recommendation

                )

        return recommendations

    def review_file(

        self,

        file_path: Path

    ) -> Recommendation | None:

        if not self.scanner.exists(

            file_path

        ):

            return None

        source_code = self.scanner.read(

            file_path

        )

        if source_code is None:

            return None

        prompt = self.prompt_builder.build(

            file_path,

            source_code

        )

        return self.review_agent.review(

            prompt,

            file_path

        )

    def build_summary(

        self,

        recommendations: list[Recommendation]

    ) -> str:

        prompt = self.prompt_builder.build_summary(

            recommendations

        )

        return self.review_agent.review_summary(

            prompt

        )

    def execute(

        self,

        changed_files: list[GitChange] | None = None

    ):
        if changed_files is None:

            recommendations = self.review_repository()

        else:

            recommendations = self.review_changed_files(

                changed_files

            )

            summary = self.build_summary(

                recommendations

            )

            self.report.save(

                recommendations,

                summary

            )

            return summary

    def review_changed_files(

        self,

        changes: list[GitChange]

    ) -> list[Recommendation]:

        recommendations = []

        for change in changes:

            file_path = self.scanner.resolve(

                change.path

            )

            if not self.scanner.exists(

                file_path

            ):

                continue

            recommendation = self.review_file(

                file_path

            )

            if recommendation is not None:

                recommendations.append(

                    recommendation

                )

        return recommendations
