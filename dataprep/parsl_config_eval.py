from parsl.executors import HighThroughputExecutor
from parsl.providers import LocalProvider
from parsl.config import Config
import os
from dataprep.config import BASE_DIR

REPO_ROOT = BASE_DIR

def make_parsl_config(workers):

    print(f"[Parsl] max_workers_per_node={workers}")

    return Config(
        executors=[
            HighThroughputExecutor(
                label="htex_local",

                max_workers_per_node=workers,

                provider=LocalProvider(
                    init_blocks=1,
                    max_blocks=1,

                    worker_init=
                    f"export PYTHONPATH={REPO_ROOT}:$PYTHONPATH",
                ),
            )
        ],

        retries=0,
    )
