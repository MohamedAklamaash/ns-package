# hypernet

Python package (3.10+) for hypergraph community detection through hyperedge percolation. It implements the clique, small-edge and large-edge percolation detectors, a planted-community generator, cover-based quality metrics, and the experiments that test the method on synthetic and real hypergraphs.

Authors: Mohamed Aklamaash and Luqmaan.

Built on Kovács, Benedek and Palla, "Community detection in hypergraphs through hyperedge percolation", Scientific Reports 2025, arXiv:2504.15213.

## Module map

- `hypernet.core`: the `Hypergraph` class.
- `hypernet.projections`: clique and multi-edge pairwise projections, conversion to networkx.
- `hypernet.generators`: `random_modular`, a planted-community hypergraph generator with noise edges.
- `hypernet.detectors.percolation`: clique, small-edge and large-edge percolation.
- `hypernet.metrics`: overlapping-cover metrics (element-centric similarity, coverage, community count) and ARI/NMI for partitions.
- `hypernet.io`: loaders for the House and Senate committee hypergraphs (Benson collection).
- `hypernet.config`: data and results locations, overridable with `HYPERNET_DATA` and `HYPERNET_RESULTS`.
- `hypernet.experiments.runner`: resumable parallel task runner with CSV output and session log.
- `hypernet.experiments.percolation`: grids, sweeps, parameter selection, real-data runs, analysis, figures and the report.

## Tests

```
uv run pytest
```

## Experiments

```
uv run python -m hypernet.experiments.percolation.run {check,map,real,all} [--quick] [--processes N] [--report-only]
```

`check` and `map` run the synthetic sweeps, `real` runs the committee datasets, `all` runs the three in order. `--quick` uses the small grids, `--processes` sets the worker count, `--report-only` rebuilds figures and the report from existing CSV files.
