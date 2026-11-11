from __future__ import annotations

import time
from collections import Counter, defaultdict

import networkx as nx

from hypernet.core import Hypergraph
from hypernet.detectors.percolation.common import sort_communities
from hypernet.projections.pairwise import clique_projection, to_networkx


class CliquePercolation:
    def __init__(self, k: int, max_seconds: float | None = None):
        if k < 2:
            raise ValueError("k must be at least 2")
        self.k = k
        self.max_seconds = max_seconds

    def fit_predict(self, hg: Hypergraph) -> list[set[int]]:
        graph = to_networkx(clique_projection(hg, weighted=False))
        deadline = None if self.max_seconds is None else time.monotonic() + self.max_seconds
        cliques = self._maximal_cliques(graph, deadline)
        return sort_communities(self._merge_adjacent(cliques, deadline))

    def _maximal_cliques(self, graph: nx.Graph, deadline: float | None) -> list[frozenset[int]]:
        cliques = []
        for clique in nx.find_cliques(graph):
            self._check(deadline)
            if len(clique) >= self.k:
                cliques.append(frozenset(clique))
        return cliques

    def _merge_adjacent(self, cliques: list[frozenset[int]], deadline: float | None) -> list[set[int]]:
        parent = list(range(len(cliques)))

        def find(i: int) -> int:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        cliques_of_node: dict[int, list[int]] = defaultdict(list)
        for index, clique in enumerate(cliques):
            self._check(deadline)
            shared = Counter(j for v in clique for j in cliques_of_node[v])
            for other, count in shared.items():
                if count >= self.k - 1:
                    parent[find(index)] = find(other)
            for v in clique:
                cliques_of_node[v].append(index)

        groups: dict[int, set[int]] = defaultdict(set)
        for index, clique in enumerate(cliques):
            groups[find(index)].update(clique)
        return list(groups.values())

    @staticmethod
    def _check(deadline: float | None) -> None:
        if deadline is not None and time.monotonic() > deadline:
            raise TimeoutError("clique percolation exceeded max_seconds")
