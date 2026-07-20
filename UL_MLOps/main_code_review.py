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

        interval_seconds=1800,

        poll_interval=30,

        run_immediately=True

    )

    scheduler.start()

    try:

        while True:

            time.sleep(1)

    except KeyboardInterrupt:

        scheduler.stop()


if __name__ == "__main__":

    main()
