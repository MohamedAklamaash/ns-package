import numpy as np

from hypernet.core import Hypergraph
from hypernet.projections import clique_projection, multi_edge_projection, to_networkx


def hg():
    return Hypergraph(4, [(0, 1, 2), (0, 1), (3,)])


def test_multi_edge_counts_shared_edges():
    a = multi_edge_projection(hg()).toarray()
    assert a[0, 1] == 2 and a[1, 0] == 2
    assert a[0, 2] == 1
    assert a[3].sum() == 0
    assert np.allclose(a, a.T)
    assert np.diag(a).sum() == 0


def test_clique_weighted():
    a = clique_projection(hg()).toarray()
    assert np.isclose(a[0, 1], 0.5 + 1.0)
    assert np.isclose(a[0, 2], 0.5)


def test_clique_binary():
    a = clique_projection(hg(), weighted=False).toarray()
    assert a[0, 1] == 1 and a[1, 2] == 1 and a[2, 3] == 0


def test_networkx():
    g = to_networkx(multi_edge_projection(hg()))
    assert g.number_of_nodes() == 4
    assert g[0][1]["weight"] == 2
