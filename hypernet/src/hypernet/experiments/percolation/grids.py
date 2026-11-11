from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

NODES = 500
COMMUNITIES = 10
NOISE_CHECK = (0.0, 0.1, 0.2, 0.3, 0.4)
NOISE_MAP = (0.0, 0.1, 0.2, 0.3, 0.4, 0.6, 0.8)
LARGE_KS = tuple(range(3, 9))
SMALL_KS = tuple(range(3, 9))
RELATIVE_INTERSECTIONS = (0.5, 0.6, 0.7, 0.8, 0.9)
CLIQUE_KS = (3, 4)
REAL_PARAMETER_COUNT = 12
LARGE_INTRA = (6, 7, 8)
SMALL_INTRA = (3, 4, 5)


@dataclass(frozen=True)
class Setting:
    intra: tuple[int, ...]
    noise: tuple[int, ...]

    @property
    def name(self) -> str:
        return "i" + "".join(map(str, self.intra)) + "_n" + "".join(map(str, self.noise))

    @property
    def kind(self) -> str:
        return "large" if min(self.intra) >= 6 else "small"


CHECK_SETTINGS = (Setting((6, 7, 8), (3, 4, 5)), Setting((3, 4, 5), (6, 7, 8)))
MAP_SETTINGS = (
    Setting((6, 7, 8), (3, 4, 5)),
    Setting((5, 6, 7), (4, 5, 6)),
    Setting((4, 5, 6), (4, 5, 6)),
    Setting((3, 4, 5), (6, 7, 8)),
    Setting((4, 5, 6), (5, 6, 7)),
)


@dataclass(frozen=True)
class SweepGrid:
    settings: tuple[Setting, ...]
    noise_fractions: tuple[float, ...]
    seeds: int
    large_ks: tuple[int, ...] = LARGE_KS
    small_ks: tuple[int, ...] = SMALL_KS
    relative_intersections: tuple[float, ...] = RELATIVE_INTERSECTIONS
    clique_ks: tuple[int, ...] = ()
    clique_seeds: int | None = None
    clique_seconds: float = 60.0
    nodes: int = NODES
    communities: int = COMMUNITIES


CHECK_FULL = SweepGrid(CHECK_SETTINGS, NOISE_CHECK, seeds=30)
CHECK_QUICK = replace(CHECK_FULL, seeds=3)
MAP_FULL = SweepGrid(MAP_SETTINGS, NOISE_MAP, seeds=30, clique_ks=CLIQUE_KS, clique_seeds=5)
MAP_QUICK = replace(MAP_FULL, seeds=3, clique_seeds=1, clique_seconds=5.0)


def large_parameters(ks) -> list[tuple[int, float]]:
    return [(k, i) for k in ks for i in range(1, k)]


def small_parameters(ks, relative_intersections) -> list[tuple[int, float]]:
    return [(k, r) for k in ks for r in relative_intersections]


def clique_parameters(ks) -> list[tuple[int, float]]:
    return [(k, 0) for k in ks]


def real_size_range(sizes, count: int = REAL_PARAMETER_COUNT) -> tuple[int, ...]:
    upper = int(np.ceil(np.percentile(sizes, 90)))
    return tuple(range(3, max(upper, 3) + 1))[:count]
