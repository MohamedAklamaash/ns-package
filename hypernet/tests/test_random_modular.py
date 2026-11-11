import numpy as np
import pytest

from hypernet.core import Hypergraph
from hypernet.generators import generate_random_modular, noise_edge_count

N = 200
C = 10
INTRA = (6, 7, 8)
NOISE = (3, 4, 5)


def make(noise_fraction=0.2, seed=1, intra=INTRA, noise=NOISE, n=N, c=C, **kwargs):
    return generate_random_modular(n, c, intra, noise, noise_fraction, seed, **kwargs)


def test_returns_hypergraph_and_label_layout():
    hg, labels = make()
    assert isinstance(hg, Hypergraph)
    assert labels.dtype == np.int64 and labels.shape == (N,)
    assert np.array_equal(hg.node_labels, labels)
    block = N // C
    for node in range(N):
        assert labels[node] == node // block


@pytest.mark.parametrize("noise_fraction", [0.0, 0.1, 0.4, 1.0])
def test_edge_count(noise_fraction):
    hg, _ = make(noise_fraction=noise_fraction)
    expected = len(INTRA) * C * (N // C) + len(NOISE) * round(N * noise_fraction)
    assert hg.num_edges == expected
    assert noise_edge_count(N, noise_fraction) == round(N * noise_fraction)


def test_intra_per_community_override():
    hg, _ = make(noise_fraction=0.0, intra_per_community=3)
    assert hg.num_edges == len(INTRA) * C * 3


def test_intra_edges_stay_inside_communities_without_noise():
    hg, labels = make(noise_fraction=0.0)
    for edge in hg.edges:
        assert len(set(labels[list(edge)].tolist())) == 1


def test_size_histogram_matches_requested_sizes():
    hg, _ = make(noise_fraction=0.2)
    per_intra = C * (N // C)
    per_noise = round(N * 0.2)
    expected = {s: per_intra for s in INTRA} | {s: per_noise for s in NOISE}
    assert hg.size_histogram() == expected


def test_edges_have_distinct_nodes():
    hg, _ = make()
    sizes = list(INTRA) * (C * (N // C)) + list(NOISE) * round(N * 0.2)
    assert sorted(hg.sizes.tolist()) == sorted(sizes)


def test_deterministic_for_seed_and_sensitive_to_it():
    a, la = make(seed=5)
    b, lb = make(seed=5)
    c, _ = make(seed=6)
    assert a.edges == b.edges and np.array_equal(la, lb)
    assert a.edges != c.edges


def test_overlapping_intra_and_noise_sizes_allowed():
    hg, _ = make(intra=(4, 5, 6), noise=(5, 6, 7))
    histogram = hg.size_histogram()
    assert histogram[5] == C * (N // C) + round(N * 0.2)
    assert histogram[4] == C * (N // C)
    assert histogram[7] == round(N * 0.2)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"n": 201},
        {"intra": (1, 6)},
        {"noise": (1, 3)},
        {"intra": (21,)},
        {"noise": (N + 1,)},
        {"noise_fraction": 1.1},
        {"noise_fraction": -0.1},
    ],
)
def test_invalid_arguments_rejected(kwargs):
    with pytest.raises(ValueError):
        make(**kwargs)
