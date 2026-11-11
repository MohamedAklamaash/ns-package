from __future__ import annotations

import argparse
from pathlib import Path

from hypernet.config import results_root
from hypernet.experiments.percolation.experiments import run_check, run_map
from hypernet.experiments.percolation.grids import CHECK_FULL, CHECK_QUICK, MAP_FULL, MAP_QUICK
from hypernet.experiments.percolation.real import run_real
from hypernet.experiments.percolation.report import build_report
from hypernet.experiments.runner import log_session

CHOICES = ("check", "map", "real", "all")


def output_dir(quick: bool) -> Path:
    root = results_root()
    return root / "quick" if quick else root


def run_selected(which: str, quick: bool, processes: int | None, out_dir: Path) -> None:
    jobs = {
        "check": lambda: run_check(CHECK_QUICK if quick else CHECK_FULL, out_dir, processes),
        "map": lambda: run_map(MAP_QUICK if quick else MAP_FULL, out_dir, processes),
        "real": lambda: run_real(out_dir, processes),
    }
    names = list(jobs) if which == "all" else [which]
    for name in names:
        summary = jobs[name]()
        log_session(out_dir, name, summary, processes)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="hypernet.experiments.percolation.run")
    parser.add_argument("experiment", choices=CHOICES)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--processes", type=int, default=None)
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args(argv)
    out_dir = output_dir(args.quick)
    out_dir.mkdir(parents=True, exist_ok=True)
    if not args.report_only:
        run_selected(args.experiment, args.quick, args.processes, out_dir)
    print(build_report(out_dir, args.quick))


if __name__ == "__main__":
    main()
