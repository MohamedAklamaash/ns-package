import argparse

import numpy as np

from hypernet.generators.habcd import generate_habcd
from hypernet.generators.habcd.composition import weight_matrix
from hypernet.generators.habcd.diagnostics import (
    empirical_ccdf,
    empirical_composition,
    empirical_noise,
    theoretical_ccdf,
    volume_fractions,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--xi", type=float, default=0.2)
    parser.add_argument("--weights", default="majority", choices=["majority", "linear", "strict"])
    parser.add_argument("--gamma", type=float, default=2.5)
    parser.add_argument("--delta", type=int, default=5)
    parser.add_argument("--zeta", type=float, default=0.5)
    parser.add_argument("--beta", type=float, default=1.5)
    parser.add_argument("--min-comm", type=int, default=50)
    parser.add_argument("--tau", type=float, default=0.75)
    parser.add_argument("--q", type=float, nargs="+", default=[0, 0.25, 0.25, 0.25, 0.25])
    return parser.parse_args()


def pick(support, count=8):
    idx = np.unique(np.linspace(0, len(support) - 1, count).astype(int))
    return idx, support[idx]


def print_ccdf(title, name, support, theory, runs):
    print(f"\n{title}")
    print(f"{name:>8} {'theory':>10} {'sim mean':>10} {'sim std':>10}")
    stack = np.vstack(runs)
    for i, k in zip(*pick(support)):
        print(f"{k:>8d} {theory[i]:>10.5f} {stack[:, i].mean():>10.5f} {stack[:, i].std():>10.5f}")


def main():
    args = parse_args()
    d_max = int(args.n**args.zeta)
    c_max = int(args.n**args.tau)
    q = np.asarray(args.q)
    max_size = len(q)

    degree_runs, community_runs, volume_runs = [], [], []
    num_communities, num_edges, noise_runs, noise_by_size, composition_runs = [], [], [], [], []
    deg_support, deg_theory = theoretical_ccdf(args.gamma, args.delta, d_max)
    com_support, com_theory = theoretical_ccdf(args.beta, args.min_comm, c_max)

    for run in range(args.runs):
        hg, labels = generate_habcd(
            args.n, args.gamma, args.delta, d_max, args.beta, args.min_comm, c_max,
            args.xi, q, args.weights, args.seed + run,
        )
        sizes = np.bincount(labels)
        degree_runs.append(empirical_ccdf(hg.degrees, deg_support))
        community_runs.append(empirical_ccdf(sizes, com_support))
        volume_runs.append(volume_fractions(hg, max_size))
        num_communities.append(len(sizes))
        num_edges.append(hg.num_edges)
        overall, by_size = empirical_noise(hg, labels)
        noise_runs.append(overall)
        noise_by_size.append(by_size)
        composition_runs.append(empirical_composition(hg, labels, max_size))

    print(f"n={args.n} gamma={args.gamma} delta={args.delta} D={d_max} beta={args.beta} "
          f"s={args.min_comm} S={c_max} xi={args.xi} weights={args.weights} runs={args.runs}")
    print(f"communities: mean={np.mean(num_communities):.2f} std={np.std(num_communities):.2f}")
    print(f"hyperedges:  mean={np.mean(num_edges):.1f} std={np.std(num_edges):.1f}")

    print_ccdf("Fig 1: fraction of nodes with degree >= K", "K", deg_support, deg_theory, degree_runs)
    print_ccdf("Fig 2: fraction of communities with size >= K", "K", com_support, com_theory, community_runs)

    print("\nFig 3: volume fraction by hyperedge size")
    print(f"{'size':>8} {'target':>10} {'sim mean':>10} {'sim std':>10}")
    stack = np.vstack(volume_runs)
    for d in range(1, max_size + 1):
        if q[d - 1] > 0 or stack[:, d].mean() > 0:
            print(f"{d:>8d} {q[d - 1] / q.sum():>10.5f} {stack[:, d].mean():>10.5f} {stack[:, d].std():>10.5f}")

    print(f"\nempirical noise (edges without majority community): mean={np.mean(noise_runs):.4f} target xi={args.xi}")
    for d in sorted({d for run in noise_by_size for d in run}):
        values = [run[d] for run in noise_by_size if d in run]
        print(f"  size {d}: {np.mean(values):.4f}")

    print("\nFigs 4-5: composition of community hyperedges (c of d nodes in the majority community)")
    target = weight_matrix(args.weights, max_size)
    measured = np.mean(composition_runs, axis=0)
    print(f"{'d':>4} {'c':>4} {'target':>10} {'measured':>10}")
    for d in range(2, max_size + 1):
        if q[d - 1] == 0:
            continue
        for c in range(d // 2 + 1, d + 1):
            print(f"{d:>4d} {c:>4d} {target[c, d]:>10.4f} {measured[c, d]:>10.4f}")


if __name__ == "__main__":
    main()
