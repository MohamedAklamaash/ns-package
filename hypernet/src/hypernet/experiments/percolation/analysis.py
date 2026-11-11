from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from hypernet.experiments.percolation.selection import default_parameters, select_parameters

INSTANCE_KEYS = ["setting", "noise_fraction", "seed", "method"]
CELL_KEYS = ["setting", "noise_fraction", "method"]
SETTING_KEYS = ["setting", "noise_fraction", "method", "param1", "param2"]
PICKS = ("chosen", "chosen_coverage", "oracle", "default")
PICK_COLUMNS = ("param1", "param2", "ecs", "coverage", "n_communities")
SUMMARY_COLUMNS = ["n_communities", "coverage", "largest_size", "second_largest_size", "concentration"]
TUNED_METHODS = ("large", "small")
SYNTHETIC = ("check", "map")


def load_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists() or path.stat().st_size == 0:
        return None
    return pd.read_csv(path)


def standard_error(values) -> float:
    values = np.asarray(values, dtype=np.float64)
    values = values[np.isfinite(values)]
    return float(values.std(ddof=1) / np.sqrt(len(values))) if len(values) > 1 else float("nan")


def merge_synthetic(frames: list[pd.DataFrame | None]) -> pd.DataFrame | None:
    present = [f for f in frames if f is not None]
    if not present:
        return None
    merged = pd.concat(present, ignore_index=True)
    return merged.drop_duplicates(subset=INSTANCE_KEYS + ["param1", "param2"], keep="first").reset_index(drop=True)


def setting_means(frame: pd.DataFrame) -> pd.DataFrame:
    grouped = frame.groupby(SETTING_KEYS, sort=True)
    table = grouped.agg(
        ecs=("ecs", "mean"),
        coverage=("coverage", "mean"),
        n_communities=("n_communities", "mean"),
        seeds=("seed", "nunique"),
    )
    table["ecs_se"] = grouped["ecs"].apply(standard_error)
    return table.reset_index()


def oracle_curves(frame: pd.DataFrame) -> pd.DataFrame:
    means = setting_means(frame)
    ranked = means.assign(_ecs=means["ecs"].fillna(-1.0)).sort_values(
        CELL_KEYS + ["_ecs", "param2", "param1"], ascending=[True, True, True, False, False, True]
    )
    best = ranked.drop_duplicates(CELL_KEYS, keep="first").drop(columns="_ecs")
    return best.reset_index(drop=True)


def heatmap_matrix(means: pd.DataFrame, setting: str, noise: float, method: str) -> pd.DataFrame:
    cell = means[(means["setting"] == setting) & (means["noise_fraction"] == noise) & (means["method"] == method)]
    return cell.pivot(index="param2", columns="param1", values="ecs").sort_index()


def pick_record(row: pd.Series | None, name: str) -> dict:
    if row is None:
        return {f"{name}_{c}": float("nan") for c in PICK_COLUMNS}
    return {f"{name}_{c}": row[c] for c in PICK_COLUMNS}


def lookup(group: pd.DataFrame, first: float, second: float) -> pd.Series | None:
    hit = group[(group["param1"] == first) & (np.isclose(group["param2"], second))]
    return None if hit.empty else hit.iloc[0]


def instance_picks(group: pd.DataFrame) -> dict:
    method = group["method"].iloc[0]
    head = group.iloc[0]
    default = default_parameters(method, int(head["smallest_size_at_least_three"]), int(head["largest_edge_size"]))
    rows = [{**r, "method": method} for r in group[["param1", "param2", *SUMMARY_COLUMNS]].to_dict("records")]
    choice = select_parameters(rows, fallback=default, criterion="concentration")
    legacy = select_parameters(rows, fallback=default, criterion="coverage")
    chosen = lookup(group, choice["param1"], choice["param2"])
    chosen_coverage = lookup(group, legacy["param1"], legacy["param2"])
    ranked = group.assign(_ecs=group["ecs"].fillna(-1.0)).sort_values(
        ["_ecs", "param2", "param1"], ascending=[False, False, method == "small"]
    )
    return {
        **pick_record(chosen, "chosen"),
        **pick_record(chosen_coverage, "chosen_coverage"),
        **pick_record(ranked.iloc[0], "oracle"),
        **pick_record(lookup(group, *default), "default"),
        "fell_back": choice["fallback"],
        "fell_back_coverage": legacy["fallback"],
    }


def tuning_instances(frame: pd.DataFrame, methods=TUNED_METHODS) -> pd.DataFrame:
    subset = frame[frame["method"].isin(methods)]
    records = []
    for keys, group in subset.groupby(INSTANCE_KEYS, sort=True):
        records.append({**dict(zip(INSTANCE_KEYS, keys)), **instance_picks(group)})
    table = pd.DataFrame(records)
    if table.empty:
        return table
    table["gap"] = table["oracle_ecs"] - table["chosen_ecs"]
    table["gap_coverage"] = table["oracle_ecs"] - table["chosen_coverage_ecs"]
    table["hit"] = table["gap"].abs() < 1e-9
    table["hit_coverage"] = table["gap_coverage"].abs() < 1e-9
    return table


def tuning_summary(instances: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    grouped = instances.groupby(keys, sort=True)
    table = grouped.agg(
        instances=("gap", "size"),
        chosen=("chosen_ecs", "mean"),
        chosen_coverage=("chosen_coverage_ecs", "mean"),
        oracle=("oracle_ecs", "mean"),
        default=("default_ecs", "mean"),
        gap=("gap", "mean"),
        gap_coverage=("gap_coverage", "mean"),
        hit_rate=("hit", "mean"),
        hit_rate_coverage=("hit_coverage", "mean"),
        fallback_rate=("fell_back", "mean"),
    )
    return table.reset_index()


FALLBACK_COLUMNS = {
    "chosen": lambda row: bool(row["fell_back"]),
    "chosen_coverage": lambda row: bool(row["fell_back_coverage"]),
}


def fallback_sentence(instances: pd.DataFrame) -> str:
    fell = [
        f"{row['setting']} {row['method']} ({label})"
        for _, row in instances.iterrows()
        for label, column in (("chosen", "fell_back"), ("chosen_coverage", "fell_back_coverage"))
        if row[column]
    ]
    if not fell:
        return "The selection rule did not fall back to the paper default for any dataset and method pair."
    return "The selection rule fell back to the paper default for: " + ", ".join(fell) + "."


def real_table(instances: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in instances.iterrows():
        for pick in PICKS:
            rows.append(
                {
                    "dataset": row["setting"],
                    "method": row["method"],
                    "pick": pick,
                    "param1": row[f"{pick}_param1"],
                    "param2": row[f"{pick}_param2"],
                    "ecs": row[f"{pick}_ecs"],
                    "coverage": row[f"{pick}_coverage"],
                    "n_communities": row[f"{pick}_n_communities"],
                    "fallback": FALLBACK_COLUMNS[pick](row) if pick in FALLBACK_COLUMNS else "-",
                }
            )
    return pd.DataFrame(rows)
