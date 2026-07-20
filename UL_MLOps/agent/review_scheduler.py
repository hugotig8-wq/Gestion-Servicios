from datetime import datetime
import threading
import time


class ReviewScheduler:

    def __init__(

        self,

        manager,

        interval_seconds: int = 3600,

        run_immediately: bool = True

    ):

        self.manager = manager

        self.interval_seconds = interval_seconds

        self.run_immediately = run_immediately

        self._running = False

        self._thread = None

    def start(self):

        if self._running:

            return

        self._running = True

        self._thread = threading.Thread(

            target=self._run,

            daemon=True

        )

        self._thread.start()

    def stop(self):

        self._running = False

        if self._thread is not None:

            self._thread.join()

    def _run(self):

        if self.run_immediately:

            self._execute_review()

        while self._running:

            time.sleep(

                self.interval_seconds

            )

            if not self._running:

                break

            self._execute_review()

    def _execute_review(self):

        started = datetime.utcnow()

        print(

            f"[{started.isoformat()}] "

            "Starting code review..."

        )

        try:

            summary = self.manager.execute()

            finished = datetime.utcnow()

            print(

                f"[{finished.isoformat()}] "

                "Code review completed."

            )

            print(summary)

        except Exception as error:

            print(

                f"[ERROR] "

                f"{error}"

            )
