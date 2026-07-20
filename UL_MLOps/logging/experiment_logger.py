import json
from pathlib import Path
from dataclasses import asdict
from datetime import datetime


class ExperimentLogger:

    def __init__(self):

        pass

    def _experiment_directory(

        self,

        experiment

    ) -> Path:

        directory = (

            Path(

                experiment.config.log_dir

            )

            /

            experiment.experiment_id

        )

        directory.mkdir(

            parents=True,

            exist_ok=True

        )

        return directory

    def log_start(

        self,

        experiment

    ):

        directory = self._experiment_directory(

            experiment

        )

        config_file = (

            directory

            /

            "config.json"

        )

        with open(

            config_file,

            "w",

            encoding="utf-8"

        ) as file:

            json.dump(

                asdict(

                    experiment.config

                ),

                file,

                indent=4

            )

    def log_epoch(

        self,

        experiment,

        result,

        train_loss

    ):

        directory = self._experiment_directory(

            experiment

        )

        metrics_file = (

            directory

            /

            "metrics.jsonl"

        )

        record = {

            "timestamp":

                datetime.utcnow().isoformat(),

            "epoch":

                experiment.current_epoch,

            "train_loss":

                train_loss,

            "best_score":

                experiment.best_score,

            "status":

                experiment.status.value,

            "fsr":

                result.fsr,

            "mu":

                result.mu,

            "fc":

                result.fc,

            "mia":

                result.mia

        }

        with open(

            metrics_file,

            "a",

            encoding="utf-8"

        ) as file:

            json.dump(

                record,

                file

            )

            file.write("\n")

    def log_finish(

        self,

        experiment

    ):

        directory = self._experiment_directory(

            experiment

        )

        summary_file = (

            directory

            /

            "summary.json"

        )

        summary = {

            "experiment_id":

                experiment.experiment_id,

            "status":

                experiment.status.value,

            "started_at":

                experiment.started_at.isoformat(),

            "ended_at":

                experiment.ended_at.isoformat(),

            "best_score":

                experiment.best_score,

            "epochs":

                experiment.current_epoch

        }

        with open(

            summary_file,

            "w",

            encoding="utf-8"

        ) as file:

            json.dump(

                summary,

                file,

                indent=4

            )

    def log_failure(

        self,

        experiment,

        error

    ):

        directory = self._experiment_directory(

            experiment

        )

        failure_file = (

            directory

            /

            "failure.json"

        )

        record = {

            "timestamp":

                datetime.utcnow().isoformat(),

            "status":

                experiment.status.value,

            "epoch":

                experiment.current_epoch,

            "error":

                str(error)

        }

        with open(

            failure_file,

            "w",

            encoding="utf-8"

        ) as file:

            json.dump(

                record,

                file,

                indent=4

    )
