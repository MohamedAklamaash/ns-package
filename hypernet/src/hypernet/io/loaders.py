from __future__ import annotations

from pathlib import Path

import numpy as np

from hypernet.config import data_root
from hypernet.core import Hypergraph


def _resolve(root: str | Path | None) -> Path:
    return Path(root) if root is not None else data_root()


def load_benson_labeled(name: str, root: str | Path | None = None) -> tuple[Hypergraph, np.ndarray]:
    base = _resolve(root)
    labeled = base / f"{name}-labeled" / name
    folder = labeled if labeled.exists() else base / name / name
    labels = np.loadtxt(folder / f"node-labels-{name}.txt", dtype=np.int64, ndmin=1) - 1
    edges = []
    with open(folder / f"hyperedges-{name}.txt") as handle:
        for line in handle:
            line = line.strip()
            if line:
                edges.append([int(tok) - 1 for tok in line.split(",")])
    return Hypergraph(len(labels), edges, labels), labels


def load_house_committees(root: str | Path | None = None):
    return load_benson_labeled("house-committees", root)


def load_senate_committees(root: str | Path | None = None):
    return load_benson_labeled("senate-committees", root)
