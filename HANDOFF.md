# HANDOFF: hypernet

Status date: 2026-10-28, late evening. Authors of the final paper: Mohamed Aklamaash and Luqmaan.
Presentation is on 2026-10-29. All code and all four experiment runs are done. The report, deck and paper are being
finished.

## 1. The idea in plain words
Real groups (a class in contact, co-authors, proteins in a complex) are one hyperedge each, not a set of pairs.
Hyperedge percolation finds overlapping communities by linking hyperedges that share enough nodes. We re-implement
it and ask three things:
- **E1 check.** In the paper's own setting (500 nodes, 10 communities, Figure 1 sizes and noise), does our
  implementation behave the same way? We do not claim the exact figures match.
- **E2 map.** When intra-community and noise hyperedges have overlapping sizes, and noise goes up to 0.8, does
  percolation still beat k-clique percolation on the projection? Measured by ECS and coverage.
- **E3 tune.** Can the parameters be chosen without labels? The rule rejects settings where the largest community
  is more than twice the second largest (the classical clique-percolation giant-component rule), rejects fewer than
  two communities, then picks the highest coverage among the rest, ties going to the stricter setting. Falls back to
  the paper default. Compared to the oracle-best setting and to the paper default.
- **E4 real.** House and senate committee hypergraphs with party labels, pairs dropped as in the paper.

A null result is a valid result. Never massage numbers.

## 2. Paper to cite
Kovacs, Benedek, Palla, "Community detection in hypergraphs through hyperedge percolation", arXiv:2504.15213,
Scientific Reports 2025. PDF and text: pdf-sources/2025_hyperedge-percolation_2504.15213.txt.
Format target for the final paper: paper/format-reference_NS_Paper.pdf (plain, human voice, no AI-sounding filler).

## 3. Folder map (everything lives in /home/aklamaash/Documents/college/sem9/ns_package)
- hypernet/ : the Python package (git repo, branch main, local only)
- pdf-sources/ : the paper PDF and its text (the three unused PDFs are removed)
- datasets/ : house-committees and senate-committees only
- code-refs/ : hyperedge-percolation only (old reference code removed)
- slides/ : deck (hyperedge_percolation.pptx, build_deck.py), filled with final numbers
- paper/ : format reference, main.tex, references.bib, main.pdf (about 6 pages, draft)
- results/ : experiment outputs (e1_check.csv, e2_map.csv, e4_real.csv, REPORT.md, figures/); not in git
- STUDY_GUIDE.md and STUDY_GUIDE.pdf : presenter's guide with final numbers (project root)
- remote.sh : runs a command on the 48-core machine (see section 4)
- IDEA.md, TRACKER.md, HANDOFF.md

Inside hypernet/src/hypernet:
- core/hypergraph.py : Hypergraph (edges, sizes, incidence, degrees)
- projections/ : clique projection (used by k-clique percolation)
- generators/random_modular.py : the paper's random modular hypergraph generator
- detectors/percolation/ : large.py (large-edge, k and I_abs), small.py (small-edge, K and I_rel),
  clique.py (k-clique percolation on the projection), common.py (shared helpers)
- metrics/cover.py : ECS, coverage, largest_fraction, community_count
- experiments/percolation/ : grids.py, sweep.py, selection.py (E3 rule), analysis.py, figures.py, report.py,
  run.py (CLI)

## 4. How to run
Local machine: editing and committing only. No compute runs here.

Remote (48 cores): run through remote.sh from the project folder. It rsyncs the repo and runs the command in
~/ns_package/hypernet on the remote machine. Results land in ~/ns_package/results on the remote and are copied back
to results/ locally.
```
cd /home/aklamaash/Documents/college/sem9/ns_package
./remote.sh uv run python -m hypernet.experiments.percolation.run check --quick
./remote.sh uv run python -m hypernet.experiments.percolation.run map --quick
./remote.sh uv run python -m hypernet.experiments.percolation.run real
./remote.sh uv run python -m hypernet.experiments.percolation.run all --processes 48
./remote.sh uv run python -m hypernet.experiments.percolation.run all --report-only
```
Commands: check (E1), map (E2), real (E4), all (every experiment including E3). Flags: --quick for a small grid,
--processes N for the worker count, --report-only to rebuild REPORT.md and figures from the existing CSVs.
The full `all` run takes about 45 minutes on 48 cores; the clique baseline stage is the slow part (8 processes,
60 s limit per run).

Deck rebuild: `cd hypernet && uv run --with python-pptx --with pillow --with numpy python ../slides/build_deck.py`
(this runs locally, it only builds the file).

## 5. What exists
- Generator, metrics, detectors (large, small, clique, common) and tests: done and committed.
- Experiment pipeline (grids, sweep, selection, analysis, figures, report, CLI, E4 loaders): done and committed.
- Cleanup of old modules, tests, unused datasets and unused PDFs: done. Fallback flag in the real-data table is in.
- 97 tests pass on the remote machine.
- Full runs done on the remote: E1 check, E2 map (with clique baseline), E3 tune, E4 real. Copied back to results/.
- Results: results/REPORT.md, results/e1_check.csv, e2_map.csv, e4_real.csv, sessions.json, and figures/
  (e1_check_large.png, e1_check_small.png, e2_map.png, e2_coverage.png, e3_tuning.png).
- Headline numbers:
  - E1: matching variant ECS 1.000 at all noise up to 0.4; mismatched variant 0.206 (large) and 0.424 (small) at noise 0.4.
  - E2: exact recovery while one hyperedge size is pure; under full size overlap ECS 0.601 at noise 0.1 and about 0.24
    at 0.8. Clique percolation on the projection timed out on 100 percent of runs in the large-community settings and
    scores about 0.10 where it finishes under noise.
  - E3: rule mean ECS 0.555 (large) and 0.586 (small), versus oracle 0.644 and 0.698 and paper default 0.292 and 0.229.
    Oracle hit rates 46.6 and 55.4 percent.
  - E4: on house committees the large variant gives one all-covering community at every setting, so the rule falls back
    to the default (ECS 0.501). Party labels are a weak test.
- Deck: slides/hyperedge_percolation.pptx filled with final numbers (slide 12 states the concentration rule; slides 18,
  19, 21 filled). Wide crop of the E1 heat maps for slides 13 and 14 is being added to slides/figures/.
- Paper: paper/main.tex and references.bib build to main.pdf (about 6 pages). Results are being filled in from REPORT.md.
- Study guide: STUDY_GUIDE.md and STUDY_GUIDE.pdf with final numbers.

## 6. Open items
- Finish the wide E1 heat map crop for slides 13 and 14 in slides/figures/, replace the remaining deck placeholders,
  and rebuild slides/hyperedge_percolation.pptx before the presentation on 2026-10-29.
- Finish filling the paper's results from REPORT.md. Proofread the whole paper.
- Rehearse the talk with STUDY_GUIDE.pdf.
- Optional later work (LATER): more real datasets with labels, overlapping planted communities, a smarter clique
  baseline, downstream evaluation (centrality and spreading), multi-hypergraph coupling and gene-protein case study.

## 7. Working rules from the captain
- Python 3.12 through uv. Code has no comments and no docstrings. Clean, explainable folder structure.
- Every commit is a one-line message; never add Claude or any AI as co-author. Commit after each big feature.
- Do not claim to have reproduced the paper's exact figures. Cite it as the foundation.
- Paper voice: plain, human, no AI-sounding words.
- Firstmate side: hypernet is registered as local-only +yolo in the firstmate home (a symlink in firstmate/projects/hypernet points to the repo). Deferred firstmate backlog items: hypernet-gene-protein-later, hypernet-extensions-later.
