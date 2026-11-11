from __future__ import annotations

GIANT_RATIO = 2
MIN_COMMUNITIES = 2
COVERAGE_DIGITS = 12
DEFAULT_RELATIVE_INTERSECTION = 0.5


def default_parameters(method: str, smallest_size_at_least_three: int, largest_size: int) -> tuple[int, float]:
    if method == "large":
        return smallest_size_at_least_three, smallest_size_at_least_three - 1
    return largest_size, DEFAULT_RELATIVE_INTERSECTION


def survives(row: dict) -> bool:
    if row["n_communities"] < MIN_COMMUNITIES:
        return False
    return row["largest_size"] <= GIANT_RATIO * row["second_largest_size"]


CRITERIA = ("concentration", "coverage")


def strictness_key(row: dict, criterion: str = "concentration") -> tuple:
    first = row["param1"] if row.get("method", "large") == "large" else -row["param1"]
    return (round(row[criterion], COVERAGE_DIGITS), row["param2"], first)


def select_parameters(rows: list[dict], fallback: tuple[float, float] | None = None, criterion: str = "concentration") -> dict:
    survivors = [row for row in rows if survives(row)]
    if survivors:
        best = max(survivors, key=lambda row: strictness_key(row, criterion))
        return {"param1": best["param1"], "param2": best["param2"], "fallback": False}
    if fallback is None:
        return {"param1": None, "param2": None, "fallback": True}
    return {"param1": fallback[0], "param2": fallback[1], "fallback": True}
