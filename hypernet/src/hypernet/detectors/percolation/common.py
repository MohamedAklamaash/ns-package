from __future__ import annotations

from collections.abc import Iterable


def remove_contained(communities: Iterable[set[int]]) -> list[set[int]]:
    unique = {frozenset(c) for c in communities if c}
    by_size = sorted(unique, key=len, reverse=True)
    kept: list[frozenset[int]] = []
    for candidate in by_size:
        if not any(candidate <= larger for larger in kept):
            kept.append(candidate)
    return [set(c) for c in kept]


def sort_communities(communities: Iterable[set[int]]) -> list[set[int]]:
    return sorted((set(c) for c in communities), key=lambda c: (-len(c), min(c)))


def finalize(communities: Iterable[set[int]]) -> list[set[int]]:
    return sort_communities(remove_contained(communities))
