import numpy as np
import pytest

from hypernet.metrics import (
    community_count,
    complete_cover,
    coverage,
    element_centric_similarity,
    largest_fraction,
    partition_to_cover,
)
from hypernet.metrics import cover as cover_module

ALPHA = 0.9


def dense_reference(cover_a, cover_b, n, alpha=ALPHA):
    def personalized_pagerank(cover):
        cover = complete_cover(cover, n)
        counts = np.array([sum(v in c for c in cover) for v in range(n)], dtype=float)
        affinity = np.zeros((n, n))
        for community in cover:
            members = sorted(community)
            for i in members:
                for j in members:
                    affinity[i, j] += 1.0 / (len(community) * counts[i])
        return (1.0 - alpha) * np.linalg.inv(np.eye(n) - alpha * affinity)

    difference = np.abs(personalized_pagerank(cover_a) - personalized_pagerank(cover_b))
    return 1.0 - difference.sum() / (2.0 * alpha * n)


def random_cover(rng, n, communities):
    return [
        set(rng.choice(n, rng.integers(2, n // 3), replace=False).tolist())
        for _ in range(communities)
    ]


def test_identical_covers_score_one():
    cover = [{0, 1, 2}, {2, 3}, {5, 6}]
    assert element_centric_similarity(cover, cover, 8) == pytest.approx(1.0)


def test_symmetry():
    rng = np.random.default_rng(1)
    a, b = random_cover(rng, 30, 4), random_cover(rng, 30, 5)
    forward = element_centric_similarity(a, b, 30)
    backward = element_centric_similarity(b, a, 30)
    assert forward == pytest.approx(backward)


def test_singletons_versus_one_cluster_is_low():
    n = 100
    singletons = [{v} for v in range(n)]
    everything = [set(range(n))]
    assert element_centric_similarity(singletons, everything, n) < 0.5


def test_half_split_versus_singletons_value():
    n = 100
    halves = [set(range(50)), set(range(50, 100))]
    singletons = [{v} for v in range(n)]
    value = element_centric_similarity(halves, singletons, n)
    expected = 1.0 - (2 * ALPHA * (1 - 1 / 50)) / (2 * ALPHA)
    assert value == pytest.approx(expected)
    assert value == pytest.approx(1 / 50)


def test_unclustered_nodes_equal_singletons():
    cover = [{0, 1, 2}]
    explicit = [{0, 1, 2}, {3}, {4}]
    assert element_centric_similarity(cover, explicit, 5) == pytest.approx(1.0)


def test_one_node_moved_is_slightly_below_one():
    labels = np.repeat([0, 1, 2], 20)
    moved = labels.copy()
    moved[0] = 1
    value = element_centric_similarity(
        partition_to_cover(labels), partition_to_cover(moved), 60
    )
    assert 0.9 < value < 1.0


def test_partition_closed_form():
    n, alpha = 12, ALPHA
    a = [set(range(0, 6)), set(range(6, 12))]
    b = [set(range(0, 4)), set(range(4, 12))]

    distance = 0.0
    for node in range(n):
        cluster_a = a[0] if node < 6 else a[1]
        cluster_b = b[0] if node < 4 else b[1]
        row_a = np.zeros(n)
        row_b = np.zeros(n)
        row_a[list(cluster_a)] = alpha / len(cluster_a)
        row_a[node] += 1 - alpha
        row_b[list(cluster_b)] = alpha / len(cluster_b)
        row_b[node] += 1 - alpha
        distance += np.abs(row_a - row_b).sum()
    expected = 1.0 - distance / (2 * alpha * n)
    assert element_centric_similarity(a, b, n) == pytest.approx(expected)


@pytest.mark.parametrize("seed", range(4))
def test_matches_dense_reference_on_overlapping_covers(seed):
    rng = np.random.default_rng(seed)
    n = 25
    a, b = random_cover(rng, n, 4), random_cover(rng, n, 5)
    assert element_centric_similarity(a, b, n) == pytest.approx(dense_reference(a, b, n))


def test_sparse_solver_path_matches_dense(monkeypatch):
    rng = np.random.default_rng(7)
    n = 25
    a, b = random_cover(rng, n, 4), random_cover(rng, n, 5)
    dense_value = element_centric_similarity(a, b, n)
    monkeypatch.setattr(cover_module, "DENSE_COMPONENT_LIMIT", 0)
    assert element_centric_similarity(a, b, n) == pytest.approx(dense_value)


def test_partition_to_cover():
    cover = partition_to_cover([3, 3, 7, 1, 7])
    assert sorted(map(sorted, cover)) == [[0, 1], [2, 4], [3]]


def test_complete_cover_adds_exactly_missing_nodes():
    cover = [{0, 1}, {1, 2}]
    completed = complete_cover(cover, 5)
    assert completed[:2] == cover
    assert completed[2:] == [{3}, {4}]
    assert cover == [{0, 1}, {1, 2}]


def test_coverage_largest_fraction_and_count():
    cover = [{0, 1, 2}, {2, 3}]
    assert coverage(cover, 8) == pytest.approx(0.5)
    assert largest_fraction(cover, 8) == pytest.approx(3 / 8)
    assert community_count(cover) == 2


def test_empty_cover_statistics():
    assert coverage([], 4) == 0.0
    assert largest_fraction([], 4) == 0.0
    assert community_count([]) == 0
