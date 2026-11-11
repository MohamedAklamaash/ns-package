import numpy as np
import pytest

from hypernet.metrics import adjusted_rand_index, normalized_mutual_information


def test_identical_up_to_permutation():
    a = [0, 0, 1, 1, 2, 2]
    b = [5, 5, 3, 3, 9, 9]
    assert adjusted_rand_index(a, b) == pytest.approx(1.0)
    assert normalized_mutual_information(a, b) == pytest.approx(1.0)


def test_ari_known_value():
    assert adjusted_rand_index([0, 0, 1, 2], [0, 0, 1, 1]) == pytest.approx(4 / 7)


def test_ari_worst_case():
    assert adjusted_rand_index([0, 0, 1, 1], [0, 1, 0, 1]) == pytest.approx(-0.5)


def test_nmi_known_value():
    assert normalized_mutual_information([0, 0, 1, 1], [0, 0, 1, 2]) == pytest.approx(0.8, abs=1e-9)


def test_nmi_independent_is_zero():
    assert normalized_mutual_information([0, 0, 1, 1], [0, 1, 0, 1]) == pytest.approx(0.0, abs=1e-12)


def test_trivial_partitions():
    assert normalized_mutual_information([0, 0, 0], [1, 1, 1]) == 1.0
    assert adjusted_rand_index([0, 0, 0], [1, 1, 1]) == 1.0


def test_length_mismatch():
    with pytest.raises(ValueError):
        adjusted_rand_index([0, 1], [0, 1, 2])
