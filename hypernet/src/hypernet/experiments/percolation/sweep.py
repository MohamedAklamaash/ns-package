from __future__ import annotations

import inspect
import time

import numpy as np

from hypernet.experiments.percolation.grids import (
    SweepGrid,
    clique_parameters,
    large_parameters,
    small_parameters,
)
from hypernet.experiments.runner import Task, stable_seed

FIELDS = (
    "task_id",
    "experiment",
    "setting",
    "noise_fraction",
    "seed",
    "method",
    "param1",
    "param2",
    "ecs",
    "coverage",
    "largest_fraction",
    "n_communities",
    "largest_size",
    "second_largest_size",
    "concentration",
    "smallest_size_at_least_three",
    "largest_edge_size",
    "seconds",
    "status",
)
FAMILIES = ("large", "small", "clique")
EMPTY_STATS = {
    "ecs": float("nan"),
    "coverage": float("nan"),
    "largest_fraction": float("nan"),
    "n_communities": float("nan"),
    "largest_size": float("nan"),
    "second_largest_size": float("nan"),
    "concentration": float("nan"),
}


def instance_seed(grid_nodes: int, communities: int, intra, noise, fraction: float, seed: int) -> int:
    return stable_seed("random_modular", grid_nodes, communities, intra, noise, fraction, seed)


def sweep_tasks(experiment: str, grid: SweepGrid) -> list[Task]:
    tasks = []
    for setting in grid.settings:
        for fraction in grid.noise_fractions:
            for seed in range(grid.seeds):
                for family in FAMILIES:
                    if family == "clique" and (not grid.clique_ks or seed >= (grid.clique_seeds or grid.seeds)):
                        continue
                    key = (experiment, setting.name, fraction, seed, family)
                    tasks.append(
                        {
                            "task_id": "|".join(str(p) for p in key),
                            "experiment": experiment,
                            "setting": setting.name,
                            "intra": setting.intra,
                            "noise": setting.noise,
                            "noise_fraction": fraction,
                            "seed": seed,
                            "family": family,
                            "nodes": grid.nodes,
                            "communities": grid.communities,
                            "parameters": family_parameters(family, grid),
                            "clique_seconds": grid.clique_seconds,
                        }
                    )
    return tasks


def family_parameters(family: str, grid: SweepGrid) -> list[tuple[int, float]]:
    if family == "large":
        return large_parameters(grid.large_ks)
    if family == "small":
        return small_parameters(grid.small_ks, grid.relative_intersections)
    return clique_parameters(grid.clique_ks)


def planted_cover(labels: np.ndarray) -> list[set[int]]:
    return [set(np.flatnonzero(labels == c).tolist()) for c in np.unique(labels) if c >= 0]


def concentration(cover: list[set[int]], nodes: int) -> float:
    memberships = np.zeros(nodes)
    for community in cover:
        memberships[list(community)] += 1
    total = 0.0
    for community in cover:
        effective = float((1.0 / memberships[list(community)]).sum())
        total += effective * effective
    return total / (nodes * nodes)


def cover_stats(cover: list[set[int]], truth: list[set[int]], nodes: int) -> dict:
    from hypernet.metrics.cover import element_centric_similarity

    sizes = sorted((len(c) for c in cover), reverse=True)
    covered = len(set().union(*cover)) if cover else 0
    largest = sizes[0] if sizes else 0
    return {
        "ecs": float(element_centric_similarity(cover, truth, nodes)),
        "coverage": covered / nodes,
        "largest_fraction": largest / nodes,
        "n_communities": len(cover),
        "largest_size": largest,
        "second_largest_size": sizes[1] if len(sizes) > 1 else 0,
        "concentration": concentration(cover, nodes),
    }


def build_detector(family: str, first: int, second: float, drop_pairs: bool, clique_seconds: float = 60.0):
    from hypernet.detectors import percolation

    if family == "large":
        return percolation.LargeEdgePercolation(int(first), int(second))
    if family == "small":
        return percolation.SmallEdgePercolation(int(first), float(second), drop_pairs=drop_pairs)
    constructor = percolation.CliquePercolation
    if "max_seconds" in inspect.signature(constructor).parameters:
        return constructor(int(first), max_seconds=clique_seconds)
    return constructor(int(first))


def instance_summary(hg) -> dict:
    sizes = hg.sizes
    eligible = sizes[sizes >= 3]
    return {
        "smallest_size_at_least_three": int(eligible.min()) if len(eligible) else 3,
        "largest_edge_size": int(sizes.max()) if len(sizes) else 3,
    }


def sweep_rows(hg, truth, family: str, parameters, shared: dict, drop_pairs: bool = False, clique_seconds: float = 60.0) -> list[dict]:
    summary = instance_summary(hg)
    rows = []
    for first, second in parameters:
        detector = build_detector(family, first, second, drop_pairs, clique_seconds)
        started = time.time()
        try:
            stats = cover_stats(detector.fit_predict(hg), truth, hg.num_nodes)
        except (TimeoutError, MemoryError):
            stats = dict(EMPTY_STATS)
            status = "timeout"
        else:
            status = "ok"
        rows.append(
            {
                **shared,
                **summary,
                "method": family,
                "param1": first,
                "param2": second,
                **stats,
                "seconds": time.time() - started,
                "status": status,
            }
        )
    return rows


def run_sweep_task(task: Task) -> list[dict]:
    from hypernet.generators.random_modular import generate_random_modular

    seed = instance_seed(task["nodes"], task["communities"], task["intra"], task["noise"], task["noise_fraction"], task["seed"])
    hg, labels = generate_random_modular(
        task["nodes"],
        task["communities"],
        tuple(task["intra"]),
        tuple(task["noise"]),
        task["noise_fraction"],
        seed=seed,
    )
    shared = {
        "task_id": task["task_id"],
        "experiment": task["experiment"],
        "setting": task["setting"],
        "noise_fraction": task["noise_fraction"],
        "seed": task["seed"],
    }
    return sweep_rows(hg, planted_cover(labels), task["family"], task["parameters"], shared, clique_seconds=task["clique_seconds"])
