from llm import LLMEngine

from agent.code_review_agent import PyCodeReviewAgent
from agent.repository_scanner import RepositoryScanner
from agent.prompt_builder import PromptBuilder
from agent.review_report import ReviewReport
from agent.code_review_manager import CodeReviewManager
from agent.review_scheduler import ReviewScheduler

import time


def main():

    llm = LLMEngine(

        model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",

        max_new_tokens=512

    )

    review_agent = PyCodeReviewAgent(

        llm=llm

    )

    scanner = RepositoryScanner(

        root_path="."

    )

    prompt_builder = PromptBuilder()

    report = ReviewReport(

        output_directory="reports"

    )

    manager = CodeReviewManager(

        review_agent=review_agent,

        scanner=scanner,

        prompt_builder=prompt_builder,

        report=report

    )

    scheduler = ReviewScheduler(

        manager=manager,

        interval_seconds=1800,

        poll_interval=30,

        run_immediately=True

    )

    scheduler.start()

    print(

        "PyCodeReviewAgent iniciado."

    )

    print(

        "• Revisión inmediata al arrancar."

    )

    print(

        "• Revisión cuando detecte cambios con git diff."

    )

    print(

        "• Revisión completa cada 30 minutos."

    )

    print(

        "Pulsa Ctrl+C para detener el agente."

    )

    try:

        while True:

            time.sleep(

                1

            )

    except KeyboardInterrupt:

        print(

            "\nDeteniendo PyCodeReviewAgent..."

        )

        scheduler.stop()

        print(

            "Agente detenido."

        )


if __name__ == "__main__":

    main()
