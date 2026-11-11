# hypernet: idea

## Problem
Real systems have groups bigger than pairs: a class in contact, a set of co-authors, proteins in a complex.
Flattening these groups into pairwise edges loses the group. Hyperedge percolation (Kovacs, Benedek, Palla, 2025)
finds overlapping communities directly from hyperedges, but the paper tests on its own synthetic and real data
with its own choices of parameters. Nobody has checked the method in a setting where the community signal is
hard to separate from noise, and nobody has a rule for choosing its parameters without labels.

## The paper in five lines
Kovacs, Benedek, Palla, "Community detection in hypergraphs through hyperedge percolation", arXiv:2504.15213,
Scientific Reports 2025.
1. Communities are built from hyperedges, not from nodes: two hyperedges are linked when they share enough nodes.
2. The large-edge variant (parameters k and I_abs) percolates over hyperedges of size at least k.
3. The small-edge variant (parameters K and I_rel) percolates over small hyperedges with a relative overlap threshold.
4. Baseline: k-clique percolation on the clique projection of the same hypergraph.
5. Test setting: random modular hypergraphs (Figs 2-3 of the paper), scored by qualitative community recovery and comparison to clique percolation.

## Gaps we address
1. Overlap of sizes. The paper's setting keeps intra-community hyperedges and noise hyperedges at different sizes.
   We ask what happens when the sizes overlap (clean, partial, full), which is where size alone stops being a cue.
2. Heavy noise. The paper stops at moderate noise. We push noise to 0.8 and measure ECS and coverage against the
   clique-percolation baseline.
3. Parameter choice without labels. Both variants need k, I_abs, K and I_rel chosen by hand. We test a label-free
   selection rule that rejects settings with a giant community (more than twice the second largest, the classical
   clique-percolation rule) or fewer than two communities, and picks the highest coverage among the rest.

## Experiments
- E1 check: the paper's Figure 1 setting (500 nodes, 10 communities, intra sizes 6-8 against noise sizes 3-5 and the
  mirror, noise fraction 0 to 0.4, full parameter grids, ECS heat maps). This checks our implementation in their setting.
  We do not claim to reproduce their exact figures.
- E2 map: our extension. Same generator with intra and noise sizes overlapping (clean, partial, full), noise up to 0.8.
  Hyperedge percolation at oracle-best parameters against k-clique percolation on the projection. ECS and coverage vs noise.
- E3 tune: our contribution. The label-free rule from gap 3, compared to the oracle-best setting and to the paper's
  default parameters.
- E4 real: house and senate committee hypergraphs with party labels, pairs dropped as in the paper.

## What counts as a result
- A null result is a valid result. If overlap or noise breaks percolation, or the label-free rule fails to beat the
  paper default, we report that.
- Numbers are reported as produced. No tuning of the reporting after the fact.
- Success is measured by ECS against the planted communities, with coverage, largest-community fraction and
  community count alongside it so a high score cannot hide a degenerate partition.

Headline (working): "Does hyperedge percolation keep working when size stops separating community from noise, and can its
parameters be chosen without labels?"
