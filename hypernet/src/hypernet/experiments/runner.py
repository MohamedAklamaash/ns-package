from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import time
import traceback
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from functools import partial
from multiprocessing import get_context
from pathlib import Path

THREAD_ENV = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS")

Task = dict
Worker = Callable[[Task], list[dict]]


@dataclass(frozen=True)
class RunSummary:
    submitted: int
    skipped: int
    failed: int
    seconds: float


def stable_seed(*parts) -> int:
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return int.from_bytes(digest[:4], "big")


def completed_ids(path: Path) -> set[str]:
    if not path.exists() or path.stat().st_size == 0:
        return set()
    with open(path, newline="") as handle:
        reader = csv.DictReader(handle)
        return {row["task_id"] for row in reader if row.get("task_id")}


def _guarded(worker: Worker, task: Task):
    try:
        return task["task_id"], worker(task), None
    except Exception:
        return task["task_id"], None, traceback.format_exc()


def _append(path: Path, fields: Sequence[str], rows: Iterable[dict]) -> None:
    fresh = not path.exists() or path.stat().st_size == 0
    with open(path, "a", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="raise")
        if fresh:
            writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())


def run_tasks(
    tasks: Sequence[Task],
    worker: Worker,
    path: Path,
    fields: Sequence[str],
    processes: int | None = None,
    label: str = "",
) -> RunSummary:
    path.parent.mkdir(parents=True, exist_ok=True)
    done = completed_ids(path)
    pending = [t for t in tasks if t["task_id"] not in done]
    skipped = len(tasks) - len(pending)
    started = time.time()
    failed = 0
    if not pending:
        return RunSummary(len(tasks), skipped, 0, 0.0)
    count = processes or os.cpu_count() or 1
    count = max(1, min(count, len(pending)))
    for name in THREAD_ENV:
        os.environ[name] = "1"
    print(f"[{label}] {len(pending)} tasks to run, {skipped} already done, {count} processes", file=sys.stderr, flush=True)
    with get_context("spawn").Pool(count) as pool:
        stream = pool.imap_unordered(partial(_guarded, worker), pending, chunksize=1)
        for index, (task_id, rows, error) in enumerate(stream, start=1):
            if error is not None:
                failed += 1
                print(f"[{label}] FAILED {task_id}\n{error}", file=sys.stderr, flush=True)
                continue
            _append(path, fields, rows)
            if index % 25 == 0 or index == len(pending):
                elapsed = time.time() - started
                eta = elapsed / index * (len(pending) - index)
                print(
                    f"[{label}] {index}/{len(pending)} done, {elapsed / 60:.1f} min elapsed, ~{eta / 60:.1f} min left",
                    file=sys.stderr,
                    flush=True,
                )
    return RunSummary(len(tasks), skipped, failed, time.time() - started)


def log_session(out_dir: Path, experiment: str, summary: RunSummary, processes: int | None) -> None:
    sessions = read_sessions(out_dir)
    sessions.append(
        {
            "experiment": experiment,
            "submitted": summary.submitted,
            "skipped": summary.skipped,
            "failed": summary.failed,
            "processes": processes or os.cpu_count() or 1,
            "seconds": round(summary.seconds, 1),
        }
    )
    (out_dir / "sessions.json").write_text(json.dumps(sessions, indent=1))


def read_sessions(out_dir: Path) -> list[dict]:
    path = out_dir / "sessions.json"
    return json.loads(path.read_text()) if path.exists() else []
