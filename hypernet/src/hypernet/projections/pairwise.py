from __future__ import annotations

from itertools import combinations

import networkx as nx
import numpy as np
from scipy import sparse

from hypernet.core import Hypergraph


def _pair_matrix(hg: Hypergraph, weight_of_size) -> sparse.csr_matrix:
    rows, cols, vals = [], [], []
    for e in hg.edges:
        k = len(e)
        if k < 2:
            continue
        w = weight_of_size(k)
        for u, v in combinations(e, 2):
            rows.append(u)
            cols.append(v)
            vals.append(w)
    upper = sparse.coo_matrix(
        (np.array(vals, dtype=np.float64), (np.array(rows, dtype=np.int64), np.array(cols, dtype=np.int64))),
        shape=(hg.num_nodes, hg.num_nodes),
    ).tocsr()
    return (upper + upper.T).tocsr()


def multi_edge_projection(hg: Hypergraph) -> sparse.csr_matrix:
    return _pair_matrix(hg, lambda k: 1.0)


def clique_projection(hg: Hypergraph, weighted: bool = True) -> sparse.csr_matrix:
    if weighted:
        return _pair_matrix(hg, lambda k: 1.0 / (k - 1))
    adjacency = _pair_matrix(hg, lambda k: 1.0)
    adjacency.data[:] = 1.0
    return adjacency


def to_networkx(adjacency: sparse.spmatrix) -> nx.Graph:
    return nx.from_scipy_sparse_array(adjacency)
