from __future__ import annotations

import csv
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from hypernet.experiments.percolation import analysis
from hypernet.experiments.percolation.experiments import CHECK_FILE, check_tasks, map_tasks, run_check
from hypernet.experiments.percolation.grids import (
    CHECK_FULL,
    CHECK_QUICK,
    MAP_FULL,
    MAP_QUICK,
    large_parameters,
    real_size_range,
    small_parameters,
)
from hypernet.experiments.percolation.selection import default_parameters, select_parameters
from hypernet.experiments.percolation.sweep import FIELDS, concentration


def summary(first, second, communities, coverage, largest, runner_up, method="large", concentration=None):
    return {
        "param1": first,
        "param2": second,
        "n_communities": communities,
        "coverage": coverage,
        "largest_size": largest,
        "second_largest_size": runner_up,
        "method": method,
        "concentration": coverage if concentration is None else concentration,
    }


def test_parameter_grid_counts():
    assert len(large_parameters(range(3, 9))) == 27
    assert len(small_parameters(range(3, 9), (0.5, 0.6, 0.7, 0.8, 0.9))) == 30


def test_check_task_counts_and_unique_ids():
    for grid in (CHECK_QUICK, CHECK_FULL):
        tasks = check_tasks(grid)
        assert len(tasks) == 2 * 5 * grid.seeds * 2
        assert len({t["task_id"] for t in tasks}) == len(tasks)
    assert CHECK_QUICK.seeds == 3 and CHECK_FULL.seeds == 30


def test_map_task_counts_include_clique_family():
    for grid in (MAP_QUICK, MAP_FULL):
        tasks = map_tasks(grid)
        clique_runs = 5 * 7 * (grid.clique_seeds or grid.seeds)
        assert len(tasks) == 5 * 7 * grid.seeds * 2 + clique_runs
        assert {t["family"] for t in tasks} == {"large", "small", "clique"}
        assert len({t["task_id"] for t in tasks}) == len(tasks)


def test_real_size_range_is_capped_and_starts_at_three():
    assert real_size_range(np.arange(3, 100))[0] == 3
    assert len(real_size_range(np.arange(3, 100))) == 12
    assert real_size_range(np.array([2, 2, 2])) == (3,)


def test_selection_rejects_giant_component():
    rows = [
        summary(3, 2, 2, 1.0, 400, 50),
        summary(4, 3, 3, 0.8, 100, 90),
    ]
    assert select_parameters(rows)["param1"] == 4


def test_selection_rejects_single_community():
    rows = [summary(3, 2, 1, 1.0, 100, 0), summary(5, 4, 2, 0.5, 20, 20)]
    assert select_parameters(rows)["param1"] == 5


def test_concentration_rule_avoids_fragmentation_unlike_coverage_rule():
    rows = [
        summary(3, 2, 40, 1.0, 20, 18, concentration=0.05),
        summary(6, 3, 10, 0.9, 50, 50, concentration=0.2),
    ]
    assert select_parameters(rows)["param1"] == 6
    assert select_parameters(rows, criterion="coverage")["param1"] == 3


def test_selection_prefers_higher_coverage():
    rows = [summary(4, 3, 3, 0.6, 50, 40), summary(5, 3, 3, 0.9, 50, 40)]
    assert select_parameters(rows, criterion="coverage")["param1"] == 5
    assert select_parameters(rows)["param1"] == 5


def test_tie_break_large_prefers_larger_intersection_then_larger_k():
    rows = [summary(5, 2, 3, 0.9, 50, 40), summary(5, 4, 3, 0.9, 50, 40), summary(6, 4, 3, 0.9, 50, 40)]
    chosen = select_parameters(rows)
    assert (chosen["param1"], chosen["param2"]) == (6, 4)


def test_tie_break_small_prefers_larger_relative_then_smaller_max_size():
    rows = [
        summary(5, 0.6, 3, 0.9, 50, 40, "small"),
        summary(5, 0.8, 3, 0.9, 50, 40, "small"),
        summary(4, 0.8, 3, 0.9, 50, 40, "small"),
        summary(6, 0.8, 3, 0.9, 50, 40, "small"),
    ]
    chosen = select_parameters(rows)
    assert (chosen["param1"], chosen["param2"]) == (4, 0.8)


def test_selection_falls_back_when_nothing_survives():
    rows = [summary(3, 2, 1, 1.0, 100, 0), summary(4, 3, 2, 1.0, 300, 10)]
    outcome = select_parameters(rows, fallback=(6, 5))
    assert outcome == {"param1": 6, "param2": 5, "fallback": True}


def test_default_parameters():
    assert default_parameters("large", 3, 8) == (3, 2)
    assert default_parameters("small", 3, 8) == (8, 0.5)


def synthetic_frame():
    records = []
    for seed in range(3):
        for first, second, ecs, communities, largest, runner_up in [
            (3, 2, 0.2, 2, 400, 50),
            (6, 5, 1.0 - 0.1 * seed, 10, 50, 50),
            (7, 6, 0.5, 4, 50, 40),
        ]:
            records.append(
                {
                    "setting": "i678_n345",
                    "noise_fraction": 0.0,
                    "seed": seed,
                    "method": "large",
                    "param1": first,
                    "param2": second,
                    "ecs": ecs,
                    "coverage": 1.0 if first == 6 else 0.5,
                    "n_communities": communities,
                    "largest_size": largest,
                    "second_largest_size": runner_up,
                    "concentration": 0.1 if first == 6 else 0.05,
                    "smallest_size_at_least_three": 3,
                    "largest_edge_size": 8,
                }
            )
    return pd.DataFrame(records)


def test_oracle_curves_pick_best_mean_setting():
    best = analysis.oracle_curves(synthetic_frame())
    assert len(best) == 1
    row = best.iloc[0]
    assert (row["param1"], row["param2"]) == (6, 5)
    assert row["ecs"] == pytest.approx(0.9)
    assert row["ecs_se"] > 0


def test_tuning_instances_on_synthetic_frame():
    instances = analysis.tuning_instances(synthetic_frame())
    assert len(instances) == 3
    assert (instances["chosen_param1"] == 6).all()
    assert (instances["chosen_coverage_param1"] == 6).all()
    assert instances["hit"].all()
    assert (instances["default_ecs"] == 0.2).all()
    assert instances["gap"].abs().max() < 1e-12
    summary_table = analysis.tuning_summary(instances, ["method"])
    assert summary_table["hit_rate"].iloc[0] == 1.0


def test_merge_synthetic_deduplicates_shared_instances():
    frame = synthetic_frame()
    merged = analysis.merge_synthetic([frame, frame.copy(), None])
    assert len(merged) == len(frame)


def test_end_to_end_check_single_seed(tmp_path):
    pytest.importorskip("hypernet.generators.random_modular")
    pytest.importorskip("hypernet.detectors.percolation")
    grid = replace(
        CHECK_QUICK,
        noise_fractions=(0.0,),
        seeds=1,
        large_ks=(6,),
        small_ks=(5,),
        relative_intersections=(0.5,),
        nodes=100,
        communities=5,
    )
    summary_run = run_check(grid, tmp_path, processes=2)
    assert summary_run.failed == 0
    with open(tmp_path / CHECK_FILE, newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert set(rows[0]) == set(FIELDS)
    assert {r["method"] for r in rows} == {"large", "small"}
    assert all(float(r["ecs"]) > 0.99 for r in rows if (r["setting"], r["method"]) in {("i678_n345", "large"), ("i345_n678", "small")} and r["param1"] in {"6", "5"})
    again = run_check(grid, tmp_path, processes=2)
    assert again.skipped == len(check_tasks(grid))


def test_timeout_table_counts_timeouts():
    from hypernet.experiments.percolation.report import timeout_table

    frame = pd.DataFrame(
        {
            "setting": ["a", "a", "a"],
            "method": ["clique", "clique", "large"],
            "param1": [3, 3, 6],
            "status": ["timeout", "ok", "ok"],
        }
    )
    table = timeout_table(frame)
    assert len(table) == 1 and table["timeout_fraction"].iloc[0] == 0.5


def test_concentration_of_partition_is_unchanged_by_normalisation():
    partition = [set(range(0, 50)), set(range(50, 100))]
    assert concentration(partition, 100) == pytest.approx(0.5)


def test_overlapping_fragmented_cover_scores_below_clean_partition():
    clean = [set(range(0, 50)), set(range(50, 100))]
    fragmented = [set(range(start, start + 40)) for start in range(0, 61, 5)]
    assert concentration(fragmented, 100) < concentration(clean, 100)


def test_real_table_marks_fallback_rows():
    frame = synthetic_frame()
    frame = frame[frame["param1"] == 3].assign(setting="data")
    instances = analysis.tuning_instances(frame)
    table = analysis.real_table(instances)
    assert set(table["fallback"][table["pick"] == "chosen"]) == {True}
    assert set(table["fallback"][table["pick"] == "oracle"]) == {"-"}
    assert "data large" in analysis.fallback_sentence(instances)
