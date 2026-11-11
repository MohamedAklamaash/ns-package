# Questions from the slides, answered

## 3. Hyperedges, communities, partition, cover
- A community is only a set of nodes. It has no name. When two hyperedges merge, the community is the union of their nodes. Numbers like community 1, 2, 3 are assigned at the end and ECS ignores them.
- Partition: every node in exactly one community. Cover: a node may be in several or none.
- Not a choice when running: percolation outputs a cover by construction; Louvain outputs a partition; our ground truth is a partition. ECS compares a partition with a cover.
- Overlap example (large-edge variant, k = 4, I_abs = 3): A = {a,b,c,d}, B = {a,b,e,f} share only a,b, so they are not adjacent. Communities {a,b,c,d} and {a,b,e,f}; a and b are in both.

## 4. Clique percolation
- k = 3, cliques {a,b,c}, {b,c,d}, {b,c,e}. Adjacency is checked between original cliques pair by pair, never between a merged set and a clique. All three pairs share b,c, so all are adjacent and the community is {a,b,c,d,e}. Build a graph of cliques, link those sharing k-1 nodes, take connected components, union each.
- Overlap: {a,b,c} and {c,d,e} share only c, not adjacent, two communities, c in both.

## 5. Which hyperedge joins which community
- Large-edge variant: symmetric adjacency, so connected components; each hyperedge is in exactly one community, nodes can be in several.
- Small-edge variant: seed from the first unassigned hyperedge, scan all hyperedges in stored order, add any with enough nodes already inside, repeat until stable, then next seed. A hyperedge can be absorbed by two communities. Deterministic order.

## 6. Variants
- Large-edge: hyperedges of size below k are ignored; nodes only in them end up unassigned. Small-edge: hyperedges above K are ignored.
- Which variant fits is domain knowledge or trial. Corporate "everyone" hyperedge of size 48: small-edge. Co-authorship 6-author paper: large-edge. Our rule tunes parameters within a variant, not the variant (a limit).
- Weak tie: a connection that says little about closeness, like a school assembly.

## 7. Clean size cut
- A single size threshold separates intra-community from random hyperedges perfectly (6-8 vs 3-5). The right size filter is the k or K at that threshold (k = 6). Our size-cut study removed that luxury.

## 8. Intra-community and random hyperedges
- Random hyperedges: fixed count round(N p) per random size, nodes uniform from all N. N = 500, p = 0.1: 50 of size 3, 50 of size 4, 50 of size 5, 150 total; a size-3 one falls inside one community about 1 percent of the time. Intra: 10 x 3 x 50 = 1500.
- Mirror: structure in small hyperedges (3-5) with large random ones (6-8).
- p = 0, 0.1, 0.2, 0.3, 0.4. At 0.4: 600 random against 1500 intra.
- 30 realisations per cell: 30 hypergraphs with different seeds per (layout, p, setting), ECS averaged. Paper: 100.

## 9. ECS
- Element-centric similarity; element means node.
- For each node, compare the set of nodes sharing its community in the ground truth with the set in the detected cover; average the per-node agreement over all nodes.
- Example: nodes a-f, truth {a,b,c}, {d,e,f}; detected {a,b,c}, {d,e}, {f}. a, b, c perfect; d and e lost one co-member; f lost both. ECS = 0.78 with alpha 0.9.
- Overlap: a node in two detected communities splits its co-member list half and half, so it gets partial credit. A node in no community is a singleton with an empty list, the worst case.
