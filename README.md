# Hyperedge percolation: re-implementation and a label-free parameter rule

Course project for Network Science, semester 9, by Mohamed Aklamaash and Luqmaan.

We re-implemented the two hyperedge percolation variants from Kovács, Benedek and Palla, ["Community detection in hypergraphs through hyperedge percolation"](https://arxiv.org/abs/2504.15213) (Scientific Reports, 2025), and tested them in places the original paper doesn't go: noise hyperedges that share sizes with community hyperedges, noise up to 0.8, and parameters chosen without labels.

## Results

| Question | Finding |
| --- | --- |
| Does our code behave like the paper in its Figure 1 setting? | Yes. Both variants reach ECS 1.000 without noise, and the variant matched to the size cut stays at 1.000 up to noise 0.4. |
| Does hyperedge percolation beat clique percolation on the projection? | Clique percolation scored 0.100 to 0.105 in every noisy case it finished, against 0.465 to 1.000 for the better hyperedge variant. 278 of its 350 runs timed out at 60 s. |
| Can a label-free rule pick the parameters? | On synthetic data it beat the paper's default (ECS 0.555 vs 0.292 for large-edge, 0.586 vs 0.229 for small-edge) but stayed below the oracle (0.644 and 0.698). On the House and Senate committee data it didn't help. |

The rule keeps parameter settings that give at least two communities with the largest at most twice the second largest, then picks the one with the highest concentration score.

Full tables are in `results/REPORT.md` and the write-up is `paper/main.pdf`.

## Layout

```
hypernet/       Python package: detectors, generator, metrics, experiments, tests
datasets/       House and Senate committee hypergraphs from Austin Benson's collection
results/        experiment CSVs, figures and REPORT.md
paper/          LaTeX source and compiled paper
slides/         presentation deck and the script that builds it
pdf-sources/    the original paper
code-refs/      the authors' reference implementation (git submodule)
```

## Running it

You need Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```
git clone --recursive https://github.com/MohamedAklamaash/ns-package.git
cd ns-package/hypernet
uv sync
uv run pytest
```

The package reads data from `HYPERNET_DATA` and writes to `HYPERNET_RESULTS`. Point them at the repo folders before running experiments:

```
export HYPERNET_DATA=$PWD/../datasets
export HYPERNET_RESULTS=$PWD/../results
uv run python -m hypernet.experiments.percolation.run all --quick
```

The experiment names are `check`, `map`, `real` and `all`. `--quick` runs the small grids; drop it for the full sweeps, which we ran on a 48-core machine. `--processes N` sets the worker count and `--report-only` rebuilds figures and the report from existing CSVs.

## Limits

We used 30 random realisations per cell where the paper used 100, and we don't claim to reproduce its figures exactly. ECS in the map experiment uses oracle-best parameters, so it shows what each method can do at best, not what you'd get without labels. The parameter rule is a heuristic tested on two real datasets, and on both of them the paper's default was as good or better.
