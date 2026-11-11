from __future__ import annotations

from collections import Counter, defaultdict

from hypernet.core import Hypergraph
from hypernet.detectors.percolation.common import finalize


class LargeEdgePercolation:
    def __init__(self, k: int, min_intersection: int):
        if k < 2:
            raise ValueError("k must be at least 2")
        if not 1 <= min_intersection <= k - 1:
            raise ValueError("min_intersection must satisfy 1 <= min_intersection <= k - 1")
        self.k = k
        self.min_intersection = min_intersection

    def fit_predict(self, hg: Hypergraph) -> list[set[int]]:
        edges = [e for e in hg.edges if len(e) >= self.k]
        parent = list(range(len(edges)))

        def find(i: int) -> int:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        edges_of_node: dict[int, list[int]] = defaultdict(list)
        for index, edge in enumerate(edges):
            shared = Counter(j for v in edge for j in edges_of_node[v])
            for other, count in shared.items():
                if count >= self.min_intersection:
                    parent[find(index)] = find(other)
            for v in edge:
                edges_of_node[v].append(index)

        groups: dict[int, set[int]] = defaultdict(set)
        for index, edge in enumerate(edges):
            groups[find(index)].update(edge)
        return finalize(groups.values())
