import os
from pathlib import Path

DEFAULT_DATA_ROOT = "/home/aklamaash/Documents/college/sem9/ns_package/datasets"
DEFAULT_RESULTS_ROOT = "/home/aklamaash/Documents/college/sem9/ns_package/results"


def data_root() -> Path:
    return Path(os.environ.get("HYPERNET_DATA", DEFAULT_DATA_ROOT))


def results_root() -> Path:
    return Path(os.environ.get("HYPERNET_RESULTS", DEFAULT_RESULTS_ROOT))
