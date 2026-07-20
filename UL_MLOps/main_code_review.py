from agent.code_review_agent import PyCodeReviewAgent
from agent.repository_scanner import RepositoryScanner
from agent.prompt_builder import PromptBuilder
from agent.review_report import ReviewReport
from agent.code_review_manager import CodeReviewManager

from agent.review_scheduler import ReviewScheduler
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
