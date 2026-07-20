from agents.code_review_agent import PyCodeReviewAgent
from agents.repository_scanner import RepositoryScanner
from agents.prompt_builder import PromptBuilder
from agents.review_report import ReviewReport
from agents.code_review_manager import CodeReviewManager


def main():

    review_agent = PyCodeReviewAgent()

    scanner = RepositoryScanner(
        root_path="."
    )

    prompt_builder = PromptBuilder()

    report = ReviewReport()

    manager = CodeReviewManager(
        review_agent=review_agent,
        scanner=scanner,
        prompt_builder=prompt_builder,
        report=report
    )

    summary = manager.execute()

    print(summary)


if __name__ == "__main__":

    main()
