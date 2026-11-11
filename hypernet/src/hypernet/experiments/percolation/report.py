from __future__ import annotations

from pathlib import Path

import pandas as pd

from hypernet.experiments.percolation import figures
from hypernet.experiments.percolation.analysis import (
    SYNTHETIC,
    load_csv,
    merge_synthetic,
    oracle_curves,
    fallback_sentence,
    real_table,
    tuning_instances,
    tuning_summary,
)
from hypernet.experiments.percolation.experiments import CHECK_FILE, MAP_FILE
from hypernet.experiments.percolation.grids import CHECK_SETTINGS, MAP_SETTINGS
from hypernet.experiments.runner import read_sessions

REAL_FILE = "e4_real.csv"
FIGURE_DIR = "figures"


def markdown_table(frame: pd.DataFrame, digits: int = 3) -> str:
    def cell(value) -> str:
        if isinstance(value, float):
            return "nan" if value != value else f"{value:.{digits}f}"
        return str(value)

    header = "| " + " | ".join(map(str, frame.columns)) + " |"
    divider = "| " + " | ".join("---" for _ in frame.columns) + " |"
    body = ["| " + " | ".join(cell(v) for v in row) + " |" for row in frame.itertuples(index=False)]
    return "\n".join([header, divider, *body])


def oracle_table(frame: pd.DataFrame) -> pd.DataFrame:
    best = oracle_curves(frame)
    best["best"] = best["param1"].map("{:g}".format) + "/" + best["param2"].map("{:g}".format)
    return best[["setting", "noise_fraction", "method", "ecs", "ecs_se", "best", "coverage", "seeds"]]


def pivot_oracle(frame: pd.DataFrame, value: str) -> pd.DataFrame:
    best = oracle_curves(frame)
    wide = best.pivot(index=["setting", "noise_fraction"], columns="method", values=value)
    return wide.reset_index()


def timeout_table(frame: pd.DataFrame) -> pd.DataFrame:
    clique = frame[frame["method"] == "clique"].copy()
    if clique.empty:
        return pd.DataFrame({"setting": [], "k": [], "runs": [], "timeout_fraction": []})
    clique["timed_out"] = (clique["status"] == "timeout").astype(float)
    grouped = clique.groupby(["setting", "param1"])["timed_out"].agg(["size", "mean"]).reset_index()
    return grouped.rename(columns={"param1": "k", "size": "runs", "mean": "timeout_fraction"})


def check_section(frame: pd.DataFrame | None, figure_names: list[str]) -> str:
    lines = ["## E1 check: reproduction of the paper's Figure 1", ""]
    if frame is None:
        return "\n".join(lines + ["Not run.", ""])
    seeds = int(frame["seed"].nunique())
    lines += [
        f"This reproduces the setting of Figure 1 of Kovacs, Benedek and Palla on N=500 nodes, 10 planted communities, "
        f"{seeds} random realisations per cell (the paper uses 100). Each row below shows, for one hypergraph type and noise level, "
        "the parameter setting with the highest mean element-centric similarity (ECS) to the planted partition, for each method. "
        "The full parameter grids appear as heat maps in the figure files.",
        "",
        markdown_table(oracle_table(frame[frame["method"].isin(["large", "small"])])),
        "",
        "Figures: " + ", ".join(f"`{n}`" for n in figure_names),
        "",
    ]
    return "\n".join(lines)


def map_section(frame: pd.DataFrame | None, figure_names: list[str]) -> str:
    lines = ["## E2 map: unclean size cuts", ""]
    if frame is None:
        return "\n".join(lines + ["Not run.", ""])
    lines += [
        "The same generator is used, but the intra-community and noise size ranges are allowed to overlap. "
        "Each method is scored at the parameters that maximise its mean ECS in that cell, so the numbers say what each method can do at best, "
        "not what a user without labels would obtain. Clique percolation is run on the clique projection with k in 3 and 4 (larger k is intractable on large hyperedges); timeouts are recorded as missing values and excluded from means.",
        "",
        "Mean ECS at oracle-best parameters:",
        "",
        markdown_table(pivot_oracle(frame, "ecs")),
        "",
        "Mean coverage at oracle-best parameters:",
        "",
        markdown_table(pivot_oracle(frame, "coverage")),
        "",
        "Fraction of clique percolation runs that timed out (60 s limit) or ran out of memory, by setting and k:",
        "",
        markdown_table(timeout_table(frame)),
        "",
        "Figures: " + ", ".join(f"`{n}`" for n in figure_names),
        "",
    ]
    return "\n".join(lines)


def tune_section(instances: pd.DataFrame | None, figure_names: list[str]) -> str:
    lines = ["## E3 tune: label-free parameter selection", ""]
    if instances is None or instances.empty:
        return "\n".join(lines + ["No synthetic sweep data available.", ""])
    lines += [
        "For every hypergraph and method, a setting is discarded if it yields fewer than two communities or if the largest community is more than "
        "twice the second largest (the giant-component rule). Among the remaining settings the one with the highest concentration (sum over communities of size squared, divided by n squared) is chosen, with ties "
        "going to the stricter parameter. The columns ending in coverage give the earlier rule, which picks the highest coverage among the same survivors. If nothing survives, the paper default is used. The oracle here is the best setting for each individual hypergraph "
        "(unlike E2, where parameters are fixed per cell), so the gap oracle minus chosen is always non-negative. "
        "chosen is the concentration rule and chosen_coverage the coverage rule. Hit rate is the fraction of hypergraphs where the chosen setting reaches the oracle ECS.",
        "",
        "By setting and method (mean over noise fractions and seeds):",
        "",
        markdown_table(tuning_summary(instances, ["setting", "method"])),
        "",
        "By method:",
        "",
        markdown_table(tuning_summary(instances, ["method"])),
        "",
        "By setting, method and noise fraction:",
        "",
        markdown_table(tuning_summary(instances, ["setting", "method", "noise_fraction"])),
        "",
        "Figures: " + ", ".join(f"`{n}`" for n in figure_names),
        "",
    ]
    return "\n".join(lines)


def real_section(frame: pd.DataFrame | None) -> str:
    lines = ["## E4 real: committee hypergraphs", ""]
    if frame is None:
        return "\n".join(lines + ["Not run.", ""])
    instances = tuning_instances(frame)
    lines += [
        "House and Senate committee hypergraphs, with pairs dropped, scored by ECS against party labels. "
        "Parameter ranges for k and K run from 3 to the 90th percentile of hyperedge sizes (at most 12 values). "
        "Chosen uses the concentration rule from E3 (chosen_coverage is the coverage rule), oracle is the best ECS over the grid, default is the paper default.",
        "",
        markdown_table(real_table(instances)),
        "",
        fallback_sentence(instances),
        "",
    ]
    return "\n".join(lines)


def session_section(out_dir: Path) -> str:
    sessions = read_sessions(out_dir)
    if not sessions:
        return ""
    return "## Run log\n\n" + markdown_table(pd.DataFrame(sessions)) + "\n"


def build_report(out_dir: Path, quick: bool) -> Path:
    figure_dir = out_dir / FIGURE_DIR
    check = load_csv(out_dir / CHECK_FILE)
    mapping = load_csv(out_dir / MAP_FILE)
    real = load_csv(out_dir / REAL_FILE)
    check_figures = []
    if check is not None:
        for kind, name in figures.CHECK_TYPES.items():
            if figures.check_figure(check, kind, figure_dir / name):
                check_figures.append(name)
    map_figures = []
    if mapping is not None:
        for value, name in (("ecs", "e2_map.png"), ("coverage", "e2_coverage.png")):
            if figures.map_figure(mapping, MAP_SETTINGS, value, figure_dir / name):
                map_figures.append(name)
    merged = merge_synthetic([check, mapping])
    instances = tuning_instances(merged) if merged is not None else None
    tune_figures = []
    if instances is not None and not instances.empty:
        if figures.tuning_figure(instances, MAP_SETTINGS, figure_dir / "e3_tuning.png"):
            tune_figures.append("e3_tuning.png")
    title = "# Hyperedge percolation experiments" + (" (quick grids)" if quick else "")
    sections = [
        title,
        "",
        check_section(check, check_figures),
        map_section(mapping, map_figures),
        tune_section(instances, tune_figures),
        real_section(real),
        session_section(out_dir),
    ]
    path = out_dir / "REPORT.md"
    path.write_text("\n".join(sections))
    return path
