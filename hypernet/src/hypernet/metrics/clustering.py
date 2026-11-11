import numpy as np


def _contingency(a, b) -> np.ndarray:
    a = np.asarray(a)
    b = np.asarray(b)
    if a.shape != b.shape or a.ndim != 1:
        raise ValueError("label vectors must be one-dimensional and equal length")
    _, ai = np.unique(a, return_inverse=True)
    _, bi = np.unique(b, return_inverse=True)
    table = np.zeros((ai.max() + 1, bi.max() + 1), dtype=np.float64)
    np.add.at(table, (ai, bi), 1.0)
    return table


def _comb2(x):
    return x * (x - 1) / 2.0


def adjusted_rand_index(a, b) -> float:
    table = _contingency(a, b)
    n = table.sum()
    sum_cells = _comb2(table).sum()
    sum_rows = _comb2(table.sum(axis=1)).sum()
    sum_cols = _comb2(table.sum(axis=0)).sum()
    total = _comb2(n)
    expected = sum_rows * sum_cols / total if total else 0.0
    maximum = (sum_rows + sum_cols) / 2.0
    if maximum == expected:
        return 1.0
    return float((sum_cells - expected) / (maximum - expected))


def _entropy(counts: np.ndarray) -> float:
    p = counts[counts > 0] / counts.sum()
    return float(-(p * np.log(p)).sum())


def normalized_mutual_information(a, b) -> float:
    table = _contingency(a, b)
    n = table.sum()
    ha = _entropy(table.sum(axis=1))
    hb = _entropy(table.sum(axis=0))
    if ha == 0.0 and hb == 0.0:
        return 1.0
    rows = table.sum(axis=1, keepdims=True)
    cols = table.sum(axis=0, keepdims=True)
    nz = table > 0
    mi = float((table[nz] / n * np.log(table[nz] * n / (rows @ cols)[nz])).sum())
    denom = (ha + hb) / 2.0
    return mi / denom if denom > 0 else 0.0
