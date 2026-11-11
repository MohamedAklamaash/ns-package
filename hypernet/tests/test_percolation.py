from pathlib import Path

import pytest

from hypernet.core import Hypergraph
from hypernet.detectors import CliquePercolation, LargeEdgePercolation, SmallEdgePercolation
from hypernet.detectors.percolation.common import finalize, remove_contained, sort_communities

DATA_ROOT = Path(__file__).resolve().parents[2] / "code-refs" / "hyperedge-percolation" / "hypergraphs" / "randomModular"
PLANTED = [set(range(50 * i, 50 * i + 50)) for i in range(10)]


def load_shipped(folder: str, name: str) -> Hypergraph:
    path = DATA_ROOT / folder / name
    if not path.exists():
        pytest.skip("shipped hypergraph not available")
    edges = [[int(token) for token in line.split()] for line in path.read_text().splitlines() if line.strip()]
    return Hypergraph(500, edges)


def two_chains(bridge: tuple[int, ...]) -> Hypergraph:
    left = [(0, 1, 2, 3), (2, 3, 4, 5)]
    right = [(10, 11, 12, 13), (12, 13, 14, 15)]
    return Hypergraph(20, left + right + [bridge])


def test_helpers_remove_contained_and_sort():
    result = finalize([{1, 2}, {1, 2, 3}, {7, 8}, {1, 2, 3}, {4, 5, 6, 9}])
    assert result == [{4, 5, 6, 9}, {1, 2, 3}, {7, 8}]
    assert remove_contained([{1}, {1}]) == [{1}]
    assert sort_communities([{5, 6}, {0, 1}]) == [{0, 1}, {5, 6}]


def test_large_merges_chains_with_strong_bridge():
    hg = two_chains((4, 5, 12, 13))
    result = LargeEdgePercolation(k=4, min_intersection=2).fit_predict(hg)
    assert result == [set(range(6)) | set(range(10, 16))]


def test_large_keeps_chains_apart_without_bridge():
    hg = two_chains((6, 7, 8, 9))
    result = LargeEdgePercolation(k=4, min_intersection=2).fit_predict(hg)
    assert result == [{0, 1, 2, 3, 4, 5}, {10, 11, 12, 13, 14, 15}, {6, 7, 8, 9}]


def test_large_min_intersection_controls_merging():
    hg = Hypergraph(8, [(0, 1, 2, 3), (3, 4, 5, 6)])
    assert LargeEdgePercolation(4, 1).fit_predict(hg) == [set(range(7))]
    assert LargeEdgePercolation(4, 2).fit_predict(hg) == [{0, 1, 2, 3}, {3, 4, 5, 6}]


def test_large_ignores_small_edges():
    hg = Hypergraph(6, [(0, 1, 2, 3), (3, 4), (4, 5)])
    assert LargeEdgePercolation(4, 3).fit_predict(hg) == [{0, 1, 2, 3}]


@pytest.mark.parametrize("k,min_intersection", [(1, 1), (4, 0), (4, 4)])
def test_large_validation(k, min_intersection):
    with pytest.raises(ValueError):
        LargeEdgePercolation(k, min_intersection)


def test_small_grows_through_community_overlap():
    hg = Hypergraph(12, [(0, 1, 2, 3), (2, 3, 4, 5), (4, 5, 6, 7), (9, 10, 11)])
    result = SmallEdgePercolation(max_size=4, min_relative_intersection=0.5).fit_predict(hg)
    assert result == [set(range(8)), {9, 10, 11}]


def test_small_uses_whole_community_not_single_edge():
    hg = Hypergraph(8, [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 4, 5)])
    result = SmallEdgePercolation(max_size=4, min_relative_intersection=0.5).fit_predict(hg)
    assert result == [set(range(8))]


def test_small_drops_large_edges_and_optionally_pairs():
    hg = Hypergraph(10, [(0, 1, 2), (0, 1), (1, 2, 3, 4, 5, 6)])
    assert SmallEdgePercolation(3, 0.5).fit_predict(hg) == [{0, 1, 2}]
    pairs_only = Hypergraph(4, [(0, 1), (2, 3)])
    assert SmallEdgePercolation(3, 0.5).fit_predict(pairs_only) == [{0, 1}, {2, 3}]
    assert SmallEdgePercolation(3, 0.5, drop_pairs=True).fit_predict(pairs_only) == []


def test_small_removes_contained_communities():
    hg = Hypergraph(8, [(0, 1, 2, 3), (0, 1, 2), (5, 6, 7)])
    result = SmallEdgePercolation(4, 0.6).fit_predict(hg)
    assert {0, 1, 2} not in result
    assert result == [{0, 1, 2, 3}, {5, 6, 7}]


@pytest.mark.parametrize("ratio", [0.4, 1.0])
def test_small_validation(ratio):
    with pytest.raises(ValueError):
        SmallEdgePercolation(5, ratio)


def test_clique_percolation_on_toy_graph():
    edges = [(0, 1, 2), (1, 2, 3), (5, 6, 7), (7, 8)]
    hg = Hypergraph(9, edges)
    assert CliquePercolation(3).fit_predict(hg) == [{0, 1, 2, 3}, {5, 6, 7}]


def test_clique_percolation_times_out():
    hg = Hypergraph(4, [(0, 1, 2, 3)])
    with pytest.raises(TimeoutError):
        CliquePercolation(3, max_seconds=-1.0).fit_predict(hg)


def test_large_recovers_planted_communities():
    hg = load_shipped("withRandomSmallEdges", "graph0_randomProp0.00.txt")
    result = LargeEdgePercolation(k=6, min_intersection=2).fit_predict(hg)
    assert sorted(result, key=min) == PLANTED


def test_small_recovers_planted_communities():
    hg = load_shipped("withRandomLargeEdges", "graph0_randomProp0.00.txt")
    result = SmallEdgePercolation(max_size=5, min_relative_intersection=0.5).fit_predict(hg)
    assert sorted(result, key=min) == PLANTED
