import csv

from hypernet.experiments.runner import completed_ids, log_session, read_sessions, run_tasks, stable_seed

FIELDS = ["task_id", "value"]


def worker(task):
    if task.get("fail"):
        raise ValueError("boom")
    return [{"task_id": task["task_id"], "value": task["value"] * 2}]


def make_tasks(count):
    return [{"task_id": f"t{i}", "value": i} for i in range(count)]


def read_rows(path):
    with open(path, newline="") as handle:
        return list(csv.DictReader(handle))


def test_stable_seed_is_deterministic_and_parameter_sensitive():
    assert stable_seed("a", 1, 0.5) == stable_seed("a", 1, 0.5)
    assert stable_seed("a", 1, 0.5) != stable_seed("a", 2, 0.5)


def test_run_is_resumable_and_does_not_duplicate_rows(tmp_path):
    path = tmp_path / "out.csv"
    tasks = make_tasks(4)
    first = run_tasks(tasks, worker, path, FIELDS, processes=2)
    assert first.failed == 0 and first.skipped == 0
    assert len(read_rows(path)) == 4
    second = run_tasks(tasks, worker, path, FIELDS, processes=2)
    assert second.skipped == 4
    assert len(read_rows(path)) == 4
    assert completed_ids(path) == {t["task_id"] for t in tasks}


def test_partial_resume_only_runs_missing_tasks(tmp_path):
    path = tmp_path / "out.csv"
    tasks = make_tasks(3)
    run_tasks(tasks[:1], worker, path, FIELDS, processes=1)
    summary = run_tasks(tasks, worker, path, FIELDS, processes=2)
    assert summary.skipped == 1
    assert len(completed_ids(path)) == 3


def test_failing_task_is_reported_and_not_marked_done(tmp_path):
    path = tmp_path / "out.csv"
    summary = run_tasks([{"task_id": "bad", "value": 1, "fail": True}], worker, path, FIELDS, processes=1)
    assert summary.failed == 1
    assert "bad" not in completed_ids(path)


def test_session_log_accumulates(tmp_path):
    summary = run_tasks([], worker, tmp_path / "out.csv", FIELDS, processes=1)
    log_session(tmp_path, "demo", summary, 4)
    log_session(tmp_path, "demo", summary, 4)
    assert len(read_sessions(tmp_path)) == 2
