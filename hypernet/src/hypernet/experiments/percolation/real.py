from __future__ import annotations

from pathlib import Path

from hypernet.experiments.percolation.grids import (
    RELATIVE_INTERSECTIONS,
    large_parameters,
    real_size_range,
    small_parameters,
)
from hypernet.experiments.percolation.selection import DEFAULT_RELATIVE_INTERSECTION
from hypernet.experiments.percolation.sweep import FIELDS, planted_cover, sweep_rows
from hypernet.experiments.runner import RunSummary, Task, run_tasks

DATASETS = ("house_committees", "senate_committees")
REAL_FAMILIES = ("large", "small")


def real_tasks() -> list[Task]:
    return [
        {"task_id": f"real|{dataset}|{family}", "dataset": dataset, "family": family}
        for dataset in DATASETS
        for family in REAL_FAMILIES
    ]


def load_dataset(name: str):
    from hypernet import io

    return getattr(io, f"load_{name}")()


def real_parameters(family: str, hg) -> list[tuple[int, float]]:
    ks = real_size_range(hg.sizes)
    if family == "large":
        return large_parameters(ks)
    parameters = small_parameters(ks, RELATIVE_INTERSECTIONS)
    default = (int(hg.sizes.max()), DEFAULT_RELATIVE_INTERSECTION)
    return parameters if default in parameters else parameters + [default]


def run_real_task(task: Task) -> list[dict]:
    hg, labels = load_dataset(task["dataset"])
    shared = {
        "task_id": task["task_id"],
        "experiment": "real",
        "setting": task["dataset"],
        "noise_fraction": 0.0,
        "seed": 0,
    }
    parameters = real_parameters(task["family"], hg)
    return sweep_rows(hg, planted_cover(labels), task["family"], parameters, shared, drop_pairs=True)


def run_real(out_dir: Path, processes: int | None = None) -> RunSummary:
    return run_tasks(real_tasks(), run_real_task, out_dir / "e4_real.csv", FIELDS, processes, "real")
