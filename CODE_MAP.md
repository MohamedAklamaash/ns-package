# Code map: hypernet

Everything is in `hypernet/`. Source under `src/hypernet/`, tests under `tests/`. Python 3.12, run with `uv run`.

## The hypergraph itself
- `core/hypergraph.py` : the `Hypergraph` class. Holds the node count, the list of hyperedges (sorted tuples of node ids), optional ground-truth labels. Gives sizes, degrees, incidence matrix, and `filter_edge_sizes` to keep only hyperedges in a size range.
- `projections/pairwise.py` : flattening. `clique_projection` turns every hyperedge into all its pairs (used by the clique percolation baseline). `to_networkx` wraps it as a graph.

## Generating synthetic hypergraphs
- `generators/random_modular.py` : the paper's random modular hypergraph. N nodes in C equal planted communities, N/C intra-community hyperedges per size per community, round(N p) random hyperedges per size from all nodes. `noise_edge_count` gives that number.

## The community detectors (the paper's method)
- `detectors/percolation/large.py` : `LargeEdgePercolation(k, min_intersection)`. Keeps hyperedges of size at least k, links two if they share at least I_abs nodes, communities are connected components.
- `detectors/percolation/small.py` : `SmallEdgePercolation(max_size, min_relative_intersection)`. Keeps hyperedges of size at most K, grows a community from a seed hyperedge by adding any hyperedge with at least floor(I_rel times S) nodes already inside.
- `detectors/percolation/clique.py` : `CliquePercolation(k)`. Classic k-clique percolation on the flattened graph, used as a baseline, with a time limit.
- `detectors/percolation/common.py` : drops communities contained in another and sorts the output.

## Scoring
- `metrics/cover.py` : element-centric similarity (`element_centric_similarity`), plus `coverage`, `largest_fraction`, `community_count`, and helpers to turn a label vector into a cover and to add singletons for unassigned nodes.
- `metrics/clustering.py` : ARI and NMI, kept for partitions.

## Benchmarking (the experiments)
- `experiments/percolation/grids.py` : the experiment grids. Which size layouts, noise fractions, parameter ranges, seeds, and the quick versus full budgets.
- `experiments/percolation/sweep.py` : runs one hypergraph through every parameter setting of a variant and records ECS, coverage, community sizes and the concentration score per setting.
- `experiments/percolation/selection.py` : OUR RULE. `select_parameters` discards settings with fewer than two communities or a giant community, then picks the highest concentration; `default_parameters` is the paper's recipe.
- `experiments/percolation/experiments.py` : builds the task lists for the check (paper's Figure 1 setting) and the size-cut map.
- `experiments/percolation/real.py` : the committee datasets run (not shown in the talk).
- `experiments/percolation/analysis.py` : turns the CSV rows into tables: per-cell means, oracle versus rule versus default, hit rates.
- `experiments/percolation/figures.py` : the heat maps and the line plots.
- `experiments/percolation/report.py` : writes `results/REPORT.md`.
- `experiments/percolation/run.py` : the command line. `uv run python -m hypernet.experiments.percolation.run {check,map,real,all} [--quick] [--processes N] [--report-only]`.
- `experiments/runner.py` : parallel, resumable task runner that appends rows to CSV so an interrupted run continues.

## Data loading
- `io/loaders.py` : loaders for the house and senate committee hypergraphs (Benson's collection).
- `config.py` : where data and results live (`HYPERNET_DATA`, `HYPERNET_RESULTS`).

## Tests (97, run with `uv run pytest`)
- `tests/test_core.py`, `test_projections.py` : hypergraph and flattening.
- `tests/test_random_modular.py` : generator counts, labels, determinism.
- `tests/test_percolation.py` : both variants on hand-built hypergraphs and on the authors' shipped hypergraphs (recovers the 10 planted communities).
- `tests/test_cover.py` : ECS properties (identical covers score 1, symmetry, singletons versus one cluster, overlap handled, matches a brute-force implementation).
- `tests/test_percolation_experiments.py` : task counts, the selection rule on hand-written cases, an end-to-end quick run.
- `tests/test_experiments_runner.py`, `test_metrics.py`, `test_loaders.py`, `test_import.py`.

## Outside the package
- `results/` : CSVs, `REPORT.md`, `figures/`.
- `slides/` : `build_deck_v4.py` builds `hyperedge_percolation_v4.pptx`.
- `paper/` : `main.tex`, `main.pdf`.
- `remote.sh` : syncs the repo to the 48-core machine and runs a command there.
