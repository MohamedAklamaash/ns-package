from __future__ import annotations

from pathlib import Path

from hypernet.experiments.percolation.grids import SweepGrid
from hypernet.experiments.percolation.sweep import FIELDS, run_sweep_task, sweep_tasks
from hypernet.experiments.runner import RunSummary, run_tasks

CLIQUE_PROCESS_CAP = 8

CHECK_FILE = "e1_check.csv"
MAP_FILE = "e2_map.csv"


def check_tasks(grid: SweepGrid):
    return sweep_tasks("check", grid)


def map_tasks(grid: SweepGrid):
    return sweep_tasks("map", grid)


def run_check(grid: SweepGrid, out_dir: Path, processes: int | None = None) -> RunSummary:
    return run_tasks(check_tasks(grid), run_sweep_task, out_dir / CHECK_FILE, FIELDS, processes, "check")


def run_map(grid: SweepGrid, out_dir: Path, processes: int | None = None) -> RunSummary:
    tasks = map_tasks(grid)
    path = out_dir / MAP_FILE
    percolation = [t for t in tasks if t["family"] != "clique"]
    clique = [t for t in tasks if t["family"] == "clique"]
    first = run_tasks(percolation, run_sweep_task, path, FIELDS, processes, "map")
    capped = min(processes or CLIQUE_PROCESS_CAP, CLIQUE_PROCESS_CAP)
    second = run_tasks(clique, run_sweep_task, path, FIELDS, capped, "map-clique")
    return RunSummary(
        first.submitted + second.submitted,
        first.skipped + second.skipped,
        first.failed + second.failed,
        first.seconds + second.seconds,
    )
