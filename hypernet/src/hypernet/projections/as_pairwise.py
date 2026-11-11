from __future__ import annotations

from itertools import combinations

from hypernet.core import Hypergraph


def as_pairwise_hypergraph(hg: Hypergraph, kind: str = "multi") -> Hypergraph:
    if kind not in ("multi", "clique"):
        raise ValueError("kind must be 'multi' or 'clique'")
    pairs = [pair for e in hg.edges for pair in combinations(e, 2)]
    if kind == "clique":
        pairs = sorted(set(pairs))
    return Hypergraph(hg.num_nodes, pairs, hg.node_labels)
