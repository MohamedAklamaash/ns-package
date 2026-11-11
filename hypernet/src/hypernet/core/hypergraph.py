from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np
from scipy import sparse


class Hypergraph:
    def __init__(
        self,
        num_nodes: int,
        edges: Iterable[Iterable[int]],
        node_labels: Sequence[int] | np.ndarray | None = None,
    ):
        self.num_nodes = int(num_nodes)
        self.edges: list[tuple[int, ...]] = [tuple(sorted(set(int(v) for v in e))) for e in edges]
        for e in self.edges:
            if e and (e[0] < 0 or e[-1] >= self.num_nodes):
                raise ValueError("hyperedge contains a node outside 0..n-1")
        self.node_labels = None if node_labels is None else np.asarray(node_labels)
        if self.node_labels is not None and len(self.node_labels) != self.num_nodes:
            raise ValueError("node_labels length must equal num_nodes")

    @property
    def num_edges(self) -> int:
        return len(self.edges)

    @property
    def sizes(self) -> np.ndarray:
        return np.fromiter((len(e) for e in self.edges), dtype=np.int64, count=len(self.edges))

    @property
    def incidence(self) -> sparse.csr_matrix:
        sizes = self.sizes
        indices = np.fromiter((v for e in self.edges for v in e), dtype=np.int64, count=int(sizes.sum()))
        indptr = np.concatenate([[0], np.cumsum(sizes)])
        data = np.ones(len(indices), dtype=np.float64)
        edge_by_node = sparse.csr_matrix((data, indices, indptr), shape=(self.num_edges, self.num_nodes))
        return edge_by_node.T.tocsr()

    @property
    def degrees(self) -> np.ndarray:
        counts = np.fromiter((v for e in self.edges for v in e), dtype=np.int64)
        return np.bincount(counts, minlength=self.num_nodes)

    def size_histogram(self) -> dict[int, int]:
        values, counts = np.unique(self.sizes, return_counts=True)
        return {int(k): int(c) for k, c in zip(values, counts)}

    def filter_edge_sizes(self, min_size: int = 1, max_size: int | None = None) -> Hypergraph:
        kept = [e for e in self.edges if len(e) >= min_size and (max_size is None or len(e) <= max_size)]
        return Hypergraph(self.num_nodes, kept, self.node_labels)

    def __repr__(self) -> str:
        return f"Hypergraph(num_nodes={self.num_nodes}, num_edges={self.num_edges})"
