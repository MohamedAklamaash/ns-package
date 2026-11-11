from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from hypernet.experiments.percolation.analysis import heatmap_matrix, oracle_curves, setting_means
from hypernet.experiments.percolation.grids import CHECK_SETTINGS, Setting

DPI = 200
METHOD_STYLE = {
    "large": {"marker": "o", "linestyle": "-", "color": "0.0"},
    "small": {"marker": "s", "linestyle": "--", "color": "0.35"},
    "clique": {"marker": "^", "linestyle": ":", "color": "0.6"},
}
PICK_STYLE = {
    "oracle": {"marker": "o", "linestyle": "-", "color": "0.0"},
    "chosen": {"marker": "s", "linestyle": "--", "color": "0.35"},
    "chosen_coverage": {"marker": "D", "linestyle": "-.", "color": "0.5"},
    "default": {"marker": "^", "linestyle": ":", "color": "0.6"},
}
METHOD_TITLE = {
    "large": "large-edge (k, min intersection)",
    "small": "small-edge (K, relative intersection)",
}
AXIS_LABELS = {"large": ("k", "min intersection"), "small": ("K", "relative intersection")}
CHECK_TYPES = {"large": "e1_check_large.png", "small": "e1_check_small.png"}


def kind_setting(frame: pd.DataFrame, kind: str) -> str | None:
    for setting in CHECK_SETTINGS:
        if setting.kind == kind and setting.name in set(frame["setting"]):
            return setting.name
    return None


def draw_heatmap(axis, matrix: pd.DataFrame, labels: tuple[str, str]) -> None:
    values = matrix.to_numpy(dtype=float)
    axis.imshow(values, origin="lower", cmap="gray_r", vmin=0.0, vmax=1.0, aspect="auto")
    axis.set_xticks(range(matrix.shape[1]), [f"{c:g}" for c in matrix.columns], fontsize=7)
    axis.set_yticks(range(matrix.shape[0]), [f"{r:g}" for r in matrix.index], fontsize=7)
    axis.set_xlabel(labels[0], fontsize=8)
    axis.set_ylabel(labels[1], fontsize=8)
    for (row, col), value in np.ndenumerate(values):
        if np.isfinite(value):
            axis.text(col, row, f"{value:.2f}", ha="center", va="center", fontsize=6, color="white" if value > 0.5 else "black")


def check_figure(frame: pd.DataFrame, kind: str, path: Path) -> Path | None:
    setting = kind_setting(frame, kind)
    if setting is None:
        return None
    means = setting_means(frame[frame["setting"] == setting])
    noises = sorted(means["noise_fraction"].unique())
    figure, axes = plt.subplots(len(noises), 2, figsize=(9, 2.6 * len(noises)), squeeze=False)
    for row, noise in enumerate(noises):
        for col, method in enumerate(("large", "small")):
            matrix = heatmap_matrix(means, setting, noise, method)
            draw_heatmap(axes[row, col], matrix, AXIS_LABELS[method])
            axes[row, col].set_title(f"{METHOD_TITLE[method]}, noise {noise:g}", fontsize=8)
    figure.suptitle(f"Mean ECS, {kind}-edge communities ({setting})", fontsize=10)
    figure.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=DPI)
    plt.close(figure)
    return path


def ordered_settings(frame: pd.DataFrame, settings: tuple[Setting, ...]) -> list[str]:
    present = set(frame["setting"])
    return [s.name for s in settings if s.name in present]


def panel_grid(count: int):
    columns = 3
    rows = int(np.ceil(count / columns))
    figure, axes = plt.subplots(rows, columns, figsize=(4.2 * columns, 3.3 * rows), squeeze=False, sharey=True)
    return figure, axes.ravel()


def finish(figure, axes, used: int, path: Path, xlabel: str, ylabel: str) -> Path:
    for axis in axes[used:]:
        axis.set_visible(False)
    for axis in axes[:used]:
        axis.set_xlabel(xlabel, fontsize=8)
    for axis in axes[::3]:
        axis.set_ylabel(ylabel, fontsize=8)
    handles, labels = axes[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="lower center", ncol=len(labels), fontsize=8)
    figure.tight_layout(rect=(0, 0.05, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=DPI)
    plt.close(figure)
    return path


def map_figure(frame: pd.DataFrame, settings: tuple[Setting, ...], value: str, path: Path) -> Path | None:
    names = ordered_settings(frame, settings)
    if not names:
        return None
    best = oracle_curves(frame)
    figure, axes = panel_grid(len(names))
    for axis, name in zip(axes, names):
        for method, style in METHOD_STYLE.items():
            curve = best[(best["setting"] == name) & (best["method"] == method)].sort_values("noise_fraction")
            if curve.empty:
                continue
            error = curve["ecs_se"] if value == "ecs" else None
            axis.errorbar(curve["noise_fraction"], curve[value], yerr=error, capsize=2, markersize=4, label=method, **style)
        axis.set_title(name, fontsize=9)
        axis.set_ylim(-0.02, 1.02)
        axis.grid(alpha=0.3, color="0.8")
    label = "mean ECS at oracle-best parameters" if value == "ecs" else "mean coverage at oracle-best parameters"
    return finish(figure, axes, len(names), path, "noise fraction", label)


def tuning_figure(instances: pd.DataFrame, settings: tuple[Setting, ...], path: Path) -> Path | None:
    names = ordered_settings(instances, settings)
    if not names:
        return None
    figure, axes = plt.subplots(2, len(names), figsize=(3.4 * len(names), 6.4), squeeze=False, sharey=True)
    for col, name in enumerate(names):
        for row, method in enumerate(("large", "small")):
            axis = axes[row, col]
            cell = instances[(instances["setting"] == name) & (instances["method"] == method)]
            means = cell.groupby("noise_fraction")[[f"{p}_ecs" for p in PICK_STYLE]].mean()
            for pick, style in PICK_STYLE.items():
                axis.plot(means.index, means[f"{pick}_ecs"], markersize=4, label=pick, **style)
            axis.set_title(f"{name} {method}", fontsize=8)
            axis.set_ylim(-0.02, 1.02)
            axis.grid(alpha=0.3, color="0.8")
            axis.set_xlabel("noise fraction", fontsize=8)
    axes[0, 0].set_ylabel("mean ECS", fontsize=8)
    axes[1, 0].set_ylabel("mean ECS", fontsize=8)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    figure.legend(handles, labels, loc="lower center", ncol=4, fontsize=8)
    figure.tight_layout(rect=(0, 0.05, 1, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, dpi=DPI)
    plt.close(figure)
    return path
