from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from hypernet.core import Hypergraph


def noise_edge_count(n: int, noise_fraction: float) -> int:
    return round(n * noise_fraction)


def community_labels(n: int, n_communities: int) -> np.ndarray:
    return np.repeat(np.arange(n_communities, dtype=np.int64), n // n_communities)


def validate_arguments(
    n: int,
    n_communities: int,
    intra_sizes: Sequence[int],
    noise_sizes: Sequence[int],
    noise_fraction: float,
    intra_per_community: int,
) -> None:
    if n_communities < 1 or n % n_communities != 0:
        raise ValueError("n must be divisible by n_communities")
    community_size = n // n_communities
    if any(s < 2 for s in (*intra_sizes, *noise_sizes)):
        raise ValueError("hyperedge sizes must be at least 2")
    if any(s > community_size for s in intra_sizes):
        raise ValueError("intra sizes must not exceed the community size")
    if any(s > n for s in noise_sizes):
        raise ValueError("noise sizes must not exceed n")
    if not 0.0 <= noise_fraction <= 1.0:
        raise ValueError("noise_fraction must lie in [0, 1]")
    if intra_per_community < 0:
        raise ValueError("intra_per_community must be non-negative")


def sample_edges(
    rng: np.random.Generator, pool: np.ndarray, size: int, count: int
) -> list[tuple[int, ...]]:
    return [tuple(int(v) for v in rng.choice(pool, size=size, replace=False)) for _ in range(count)]


def generate_random_modular(
    n: int,
    n_communities: int,
    intra_sizes: Sequence[int],
    noise_sizes: Sequence[int],
    noise_fraction: float,
    seed: int = 0,
    intra_per_community: int | None = None,
) -> tuple[Hypergraph, np.ndarray]:
    if intra_per_community is None:
        intra_per_community = n // n_communities if n_communities >= 1 else 0
    validate_arguments(n, n_communities, intra_sizes, noise_sizes, noise_fraction, intra_per_community)
    rng = np.random.default_rng(seed)
    labels = community_labels(n, n_communities)
    edges: list[tuple[int, ...]] = []
    for size in intra_sizes:
        for community in range(n_communities):
            members = np.flatnonzero(labels == community)
            edges.extend(sample_edges(rng, members, size, intra_per_community))
    everyone = np.arange(n)
    for size in noise_sizes:
        edges.extend(sample_edges(rng, everyone, size, noise_edge_count(n, noise_fraction)))
    return Hypergraph(n, edges, labels), labels
