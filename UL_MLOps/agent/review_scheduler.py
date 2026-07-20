import subprocess
import threading
import time
from datetime import datetime


class ReviewScheduler:

    def __init__(

        self,

        manager,

        interval_seconds: int = 1800,

        poll_interval: int = 30,

        run_immediately: bool = True

    ):

        self.manager = manager

        self.interval_seconds = interval_seconds

        self.poll_interval = poll_interval

        self.run_immediately = run_immediately

        self._running = False

        self._thread = None

        self._last_full_review = 0

        self._last_diff = ""

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

        self._last_full_review = time.time()

        if self.run_immediately:

            self._execute_review(

                "Initial review"

            )

        while self._running:

            now = time.time()

            current_diff = self._git_diff()

            if (

                current_diff

                and

                current_diff != self._last_diff

            ):

                self._last_diff = current_diff

                self._execute_review(

                    "Git changes detected"

                )

                self._last_full_review = now

            elif (

                now - self._last_full_review

                >=

                self.interval_seconds

            ):

                self._execute_review(

                    "Scheduled review"

                )

                self._last_full_review = now

            time.sleep(

                self.poll_interval

            )

    def _git_diff(self) -> str:

        try:

            result = subprocess.run(

                [

                    "git",

                    "diff",

                    "--name-only"

                ],

                capture_output=True,

                text=True,

                check=False

            )

            return result.stdout.strip()

        except Exception:

            return ""

    def _execute_review(

        self,

        reason: str

    ):

        started = datetime.utcnow()

        print(

            f"\n[{started.isoformat()}]"

        )

        print(

            f"Reason: {reason}"

        )

        try:

            summary = self.manager.execute()

            finished = datetime.utcnow()

            print(

                f"[{finished.isoformat()}]"

            )

            print(

                "Review completed."

            )

            print(summary)

        except Exception as error:

            print(

                "Review failed."

            )

            print(error)
