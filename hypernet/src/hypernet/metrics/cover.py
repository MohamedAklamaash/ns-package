from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse
from scipy.sparse import csgraph
from scipy.sparse.linalg import splu

Cover = list[set[int]]

DENSE_COMPONENT_LIMIT = 2000


def partition_to_cover(labels) -> Cover:
    groups: dict[object, set[int]] = {}
    for node, label in enumerate(np.asarray(labels).tolist()):
        groups.setdefault(label, set()).add(node)
    return list(groups.values())


def complete_cover(cover: Cover, n: int) -> Cover:
    covered = set().union(*cover) if cover else set()
    return [set(community) for community in cover] + [{v} for v in range(n) if v not in covered]


def coverage(cover: Cover, n: int) -> float:
    covered = set().union(*cover) if cover else set()
    return len(covered) / n


def largest_fraction(cover: Cover, n: int) -> float:
    if not cover:
        return 0.0
    return max(len(community) for community in cover) / n


def community_count(cover: Cover) -> int:
    return len(cover)


def _membership_matrix(cover: Cover, n: int) -> sparse.csr_matrix:
    rows, cols = [], []
    for column, community in enumerate(cover):
        rows.extend(community)
        cols.extend([column] * len(community))
    data = np.ones(len(rows))
    return sparse.csr_matrix((data, (rows, cols)), shape=(n, len(cover)))


def _transition_matrix(membership: sparse.csr_matrix) -> sparse.csr_matrix:
    sizes = np.asarray(membership.sum(axis=0)).ravel()
    memberships = np.asarray(membership.sum(axis=1)).ravel()
    scaled = membership @ sparse.diags(1.0 / sizes)
    return (sparse.diags(1.0 / memberships) @ scaled @ membership.T).tocsr()


@dataclass
class _Block:
    nodes: np.ndarray
    alpha: float
    dense: np.ndarray | None = None
    solver: object | None = None
    uniform: bool = False

    def row(self, local: int) -> np.ndarray:
        if self.uniform:
            size = len(self.nodes)
            values = np.full(size, self.alpha / size)
            values[local] += 1.0 - self.alpha
            return values
        if self.dense is not None:
            return self.dense[local]
        unit = np.zeros(len(self.nodes))
        unit[local] = 1.0
        return (1.0 - self.alpha) * self.solver.solve(unit, trans="T")


def _build_block(
    nodes: np.ndarray, transition: sparse.csr_matrix, communities_touched: int, alpha: float
) -> _Block:
    if communities_touched == 1:
        return _Block(nodes=nodes, alpha=alpha, uniform=True)
    local = transition[nodes][:, nodes]
    system = sparse.identity(len(nodes), format="csc") - alpha * local.tocsc()
    if len(nodes) <= DENSE_COMPONENT_LIMIT:
        inverse = np.linalg.inv(system.toarray())
        return _Block(nodes=nodes, alpha=alpha, dense=(1.0 - alpha) * inverse)
    return _Block(nodes=nodes, alpha=alpha, solver=splu(system))


@dataclass
class _Affinity:
    blocks: list[_Block]
    block_of: np.ndarray
    local_of: np.ndarray

    def row(self, node: int) -> tuple[np.ndarray, np.ndarray]:
        block = self.blocks[self.block_of[node]]
        return block.nodes, block.row(self.local_of[node])


def _build_affinity(cover: Cover, n: int, alpha: float) -> _Affinity:
    membership = _membership_matrix(cover, n)
    transition = _transition_matrix(membership)
    count, component = csgraph.connected_components(transition, directed=False)
    touched = np.zeros(count, dtype=int)
    cluster_rows = membership.T.tocsr()
    first_nodes = cluster_rows.indices[cluster_rows.indptr[:-1]]
    np.add.at(touched, component[first_nodes], 1)
    blocks, block_of, local_of = [], np.zeros(n, dtype=int), np.zeros(n, dtype=int)
    for index in range(count):
        nodes = np.flatnonzero(component == index)
        blocks.append(_build_block(nodes, transition, int(touched[index]), alpha))
        block_of[nodes] = index
        local_of[nodes] = np.arange(len(nodes))
    return _Affinity(blocks, block_of, local_of)


def _row_distance(first: _Affinity, second: _Affinity, node: int, scratch: np.ndarray) -> float:
    nodes_a, values_a = first.row(node)
    nodes_b, values_b = second.row(node)
    scratch[nodes_a] = values_a
    scratch[nodes_b] -= values_b
    union = np.union1d(nodes_a, nodes_b)
    distance = float(np.abs(scratch[union]).sum())
    scratch[union] = 0.0
    return distance


def element_centric_similarity(
    cover_a: Cover, cover_b: Cover, n: int, alpha: float = 0.9
) -> float:
    affinity_a = _build_affinity(complete_cover(cover_a, n), n, alpha)
    affinity_b = _build_affinity(complete_cover(cover_b, n), n, alpha)
    scratch = np.zeros(n)
    total = sum(_row_distance(affinity_a, affinity_b, node, scratch) for node in range(n))
    return float(1.0 - total / (2.0 * alpha * n))
