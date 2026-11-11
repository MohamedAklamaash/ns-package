from __future__ import annotations

import math

from hypernet.core import Hypergraph
from hypernet.detectors.percolation.common import finalize


class SmallEdgePercolation:
    def __init__(self, max_size: int, min_relative_intersection: float, drop_pairs: bool = False):
        if max_size < 2:
            raise ValueError("max_size must be at least 2")
        if not 0.5 <= min_relative_intersection < 1.0:
            raise ValueError("min_relative_intersection must satisfy 0.5 <= value < 1.0")
        self.max_size = max_size
        self.min_relative_intersection = min_relative_intersection
        self.drop_pairs = drop_pairs

    def fit_predict(self, hg: Hypergraph) -> list[set[int]]:
        min_size = 3 if self.drop_pairs else 2
        edges = [set(e) for e in hg.edges if min_size <= len(e) <= self.max_size]
        thresholds = [math.floor(self.min_relative_intersection * len(e)) for e in edges]
        unassigned = list(range(len(edges)))
        communities: list[set[int]] = []
        while unassigned:
            seed = unassigned[0]
            members = {seed}
            nodes = set(edges[seed])
            self._grow(edges, thresholds, members, nodes)
            unassigned = [i for i in unassigned if i not in members]
            communities.append(nodes)
        return finalize(communities)

    @staticmethod
    def _grow(edges: list[set[int]], thresholds: list[int], members: set[int], nodes: set[int]) -> None:
        changed = True
        while changed:
            changed = False
            for index, edge in enumerate(edges):
                if index in members:
                    continue
                if len(edge & nodes) >= thresholds[index]:
                    members.add(index)
                    nodes |= edge
                    changed = True
