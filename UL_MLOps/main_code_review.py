from agents.code_review_agent import PyCodeReviewAgent
from agents.repository_scanner import RepositoryScanner
from agents.prompt_builder import PromptBuilder
from agents.review_report import ReviewReport
from agents.code_review_manager import CodeReviewManager

from agents.review_scheduler import ReviewScheduler
import time


try:

    while True:

        time.sleep(1)

except KeyboardInterrupt:

    scheduler.stop()

def main():

    scheduler = ReviewScheduler(

        manager=manager,

        interval_seconds=3600,

        run_immediately=True

    )

    scheduler.start()

    try:

        while True:

            time.sleep(1)

    except KeyboardInterrupt:

        scheduler.stop()

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
