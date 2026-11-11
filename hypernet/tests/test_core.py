import numpy as np
import pytest

from hypernet.core import Hypergraph


@pytest.fixture
def hg():
    return Hypergraph(5, [(2, 0), (1, 2, 3), (4, 0, 2, 1)], node_labels=[0, 0, 1, 1, 1])


def test_edges_sorted_tuples(hg):
    assert hg.edges == [(0, 2), (1, 2, 3), (0, 1, 2, 4)]


def test_sizes_and_histogram(hg):
    assert hg.sizes.tolist() == [2, 3, 4]
    assert hg.size_histogram() == {2: 1, 3: 1, 4: 1}


def test_degrees(hg):
    assert hg.degrees.tolist() == [2, 2, 3, 1, 1]


def test_incidence(hg):
    inc = hg.incidence
    assert inc.shape == (5, 3)
    assert inc.toarray()[:, 0].tolist() == [1, 0, 1, 0, 0]
    assert np.array_equal(np.asarray(inc.sum(axis=1)).ravel(), hg.degrees)


def test_filter_returns_new(hg):
    sub = hg.filter_edge_sizes(min_size=3)
    assert sub is not hg
    assert sub.edges == [(1, 2, 3), (0, 1, 2, 4)]
    assert hg.num_edges == 3
    assert sub.num_nodes == 5
    assert sub.node_labels.tolist() == [0, 0, 1, 1, 1]
    assert hg.filter_edge_sizes(max_size=2).edges == [(0, 2)]


def test_validation():
    with pytest.raises(ValueError):
        Hypergraph(3, [(0, 3)])
    with pytest.raises(ValueError):
        Hypergraph(3, [(0, 1)], node_labels=[0, 1])
