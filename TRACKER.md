# hypernet tracker

Scope: one paper (Kovacs, Benedek, Palla, arXiv:2504.15213). We re-implement it in hypernet, check it in its own
setting (E1), then extend it (E2, E3) and run it on real data (E4). See IDEA.md.

Legend: [x] done, [ ] to do, (LATER) deferred by the captain.

## Locked decisions
- [x] Package name hypernet, Python 3.12 via uv, local git only
- [x] Scope narrowed to one paper; the other three papers are no longer used
- [x] Experiments E1 check, E2 map, E3 tune, E4 real
- [x] Compute runs on the remote 48-core machine through remote.sh; no compute on the local machine
- [x] Framing: we do not claim to reproduce the paper's exact figures; null results are valid

## Setup
- [x] Find the paper and download its PDF to pdf-sources/
- [x] Extract the text copy pdf-sources/2025_hyperedge-percolation_2504.15213.txt
- [x] Scaffold hypernet package with git
- [x] Rewrite IDEA.md for the new scope
- [x] Set up the Python 3.12 uv environment
- [x] Rewrite TRACKER.md and HANDOFF.md for the new scope

## Core reuse
- [x] Hypergraph data structure (incidence, hyperedge sizes, degrees)
- [x] Clique projection of a hypergraph
- [x] ECS, coverage, largest fraction, community count in metrics/cover.py

## Generator
- [x] Random modular hypergraph generator (src/hypernet/generators/random_modular.py)
- [x] Generator tests (community and noise size ranges, noise fraction)
- [x] Overlap mode: intra and noise sizes clean, partial, full (for E2)

## Detectors
- [x] Large-edge hyperedge percolation (src/hypernet/detectors/percolation/large.py, parameters k and I_abs)
- [x] Small-edge hyperedge percolation (small.py, parameters K and I_rel)
- [x] k-clique percolation on the clique projection (clique.py)
- [x] Shared helpers (common.py)
- [x] Tests for each detector on hand-built examples

## Metrics
- [x] ECS (element-centric similarity)
- [x] Coverage, largest_fraction, community_count
- [x] Metric tests

## Experiments
- [x] Grids for E1 and E2 (src/hypernet/experiments/percolation/grids.py)
- [x] Sweep runner, parallel and resumable (sweep.py)
- [x] Label-free selection rule for E3 (selection.py)
- [x] Analysis and figure code (analysis.py, figures.py)
- [x] Report builder (report.py)
- [x] CLI: run {check,map,real,all} with --quick, --processes, --report-only (run.py)
- [x] E4 loaders for house and senate committee data with party labels
- [x] Experiment tests on small grids

## Runs (on the remote machine)
- [x] E1 check, quick run and then full run
- [x] E2 map, quick run and then full run (with the clique baseline)
- [x] E3 tune, after E1 and E2 are in
- [x] E4 real
- [x] Results copied back to results/

## Report
- [x] results/REPORT.md with the numbers as produced
- [x] e1_check_large.png
- [x] e1_check_small.png
- [x] e2_map.png
- [x] e2_coverage.png
- [x] e3_tuning.png

## Deck
- [x] Deck skeleton built with slides/build_deck.py
- [x] Figure placeholders replaced with the report figures (slides 13 and 14 use a two-row crop of the E1 heat maps from slides/figures/)
- [x] Rebuild slides/hyperedge_percolation.pptx (`cd hypernet && uv run --with python-pptx --with pillow --with numpy python ../slides/build_deck.py`)
- [ ] Presentation on 2026-10-29

## Paper
- [x] Draft in the format of paper/format-reference_NS_Paper.pdf (paper/main.tex builds to 7 pages with all results filled; proofread before submitting)
- [x] Authors: Mohamed Aklamaash and Luqmaan
- [ ] (LATER) Downstream evaluation: communities for centrality and spreading
- [ ] (LATER) Multi-hypergraph coupling and gene-protein case study

## Cleanup
- [x] Delete old detectors: detectors/mi, detectors/projection
- [x] Delete old generator: generators/habcd
- [x] Delete old experiment modules: experiments/{grids,phase_diagram,size_aware,analysis,figures,report,run}.py
- [x] Delete tests for the old modules
- [x] Delete unused datasets (datasets/ holds only house-committees and senate-committees)
- [x] Delete the three unused PDFs in pdf-sources/ (keep the 2025 hyperedge percolation paper and its text)

## Status 2026-10-28 late
All code phases are done and committed in the hypernet repo: the random modular generator, ECS and cover
statistics, the percolation detectors and clique baseline, the experiment pipeline with label-free parameter
selection, the cleanup that removed MI, h-ABCD and projection baselines, and the fallback flag in the real-data
table. 97 tests pass on the remote machine. Full runs of E1, E2, E3 and E4 are done on the remote (about 45 minutes
on 48 cores) and the results are in results/. The deck is filled with final numbers; the E1 heat map crop for
slides 13 and 14 is still being added. The paper draft builds and its results are being filled in. The study guide
(STUDY_GUIDE.pdf) has the final numbers. Open: proofread the paper, rehearse with the study guide, deck rebuild
before the presentation on 2026-10-29.
