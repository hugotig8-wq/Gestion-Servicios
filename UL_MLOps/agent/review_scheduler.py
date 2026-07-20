import subprocess
import threading
import time
from datetime import datetime
from agente.git_change import GitChange
import agent.compute_sha256 import ComputeSha256


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

        self._last_full_review = 0.0

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

            self._execute_full_review(

                "Initial review"

            )

        while self._running:

            now = time.time()

            changes = self._git_diff()

            if changes:

                self._execute_changed_review(

                    changes

                )

                self._last_full_review = now

            elif (

                now - self._last_full_review

                >=

                self.interval_seconds

            ):

                self._execute_full_review(

                    "Scheduled full review"

                )

                self._last_full_review = now

            time.sleep(

                self.poll_interval

            )

    def _git_diff(

        self

    ) -> list[GitChange]:

        try:

            result = subprocess.run(

                [

                    "git",

                    "diff",

                    "--name-status"

                ],

                capture_output=True,

                text=True,

                check=False

            )

            diff = result.stdout.strip()

            if (

                not diff

                or

                diff == self._last_diff

            ):

                return []

            self._last_diff = diff

            changes = diff.splitlines()

            changes_formateado = []

            c= ComputeSha256()
            
            for change in changes:
                
                changes_formateado[change.index()] =
                GitChange(path= change.path.split[-1],
                          status=change.status[0],
                          sha256=c.encriptar(change.path)
                         )
                

            return changes_formateado

        except Exception:

            return []

    def _execute_changed_review(

        self,

        changes: list[GitChange]

    ):

        started = datetime.utcnow()

        print()

        print(

            f"[{started.isoformat()}]"

        )

        print(

            "Reviewing changed files..."

        )

        try:

            summary = self.manager.execute(

                changed_files=changes

            )

            finished = datetime.utcnow()

            print(

                f"[{finished.isoformat()}]"

            )

            print(

                "Incremental review completed."

            )

            print(summary)

        except Exception as error:

            print(

                "Incremental review failed."

            )

            print(error)

    def _execute_full_review(

        self,

        reason: str

    ):

        started = datetime.utcnow()

        print()

        print(

            f"[{started.isoformat()}]"

        )

        print(reason)

        try:

            summary = self.manager.execute()

            finished = datetime.utcnow()

            print(

                f"[{finished.isoformat()}]"

            )

            print(

                "Full review completed."

            )

            print(summary)

        except Exception as error:

            print(

                "Full review failed."

            )

            print(error)
