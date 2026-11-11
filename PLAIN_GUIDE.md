# Plain guide: what this project does, in simple words

## Which experiments to show

Show E1 and E3. Keep E2 as one backup slide. Mention E4 in one line under limits.

- E1 is the clean success. Our code does exactly what the paper says. The matching variant scores a perfect 1.0 at every noise level up to 0.4, the wrong variant falls apart (0.206 for the large-edge variant and 0.424 for the small-edge variant at noise 0.4).
- E3 is our own contribution and it worked. The rule picks parameters without labels and beats the paper's default by a wide margin (0.555 against 0.292 for the large-edge variant, 0.586 against 0.229 for the small-edge variant). It stays below the oracle (0.644 and 0.698). Say that plainly.
- E2 is a half success. Percolation still works when some sizes overlap but breaks when community and noise sizes are identical (0.601 at noise 0.1, about 0.24 at 0.8). Keep it for questions.
- E4 is a null result on real committee data. Party labels are a weak test. Say it in one line.

## What the paper does

Think of a school. A hyperedge is one meeting, with everyone who was in it. The paper finds friend groups by chaining meetings.

1. Start from one meeting.
2. Add any other meeting that overlaps it enough.
3. Add any meeting that overlaps the growing pile enough.
4. When nothing more can join, the people in the pile are one community.
5. Start again from a meeting not yet used.

That is the whole method. Communities are built by a rule. There are two versions of "overlaps enough":

- Large-edge variant. Only count meetings with at least k people. Two meetings connect if they share at least I_abs people. Use it when big meetings are the real groups and tiny ones are chatter.
- Small-edge variant. Only count meetings with at most K people. A meeting joins a pile if at least a fraction I_rel of its people are already in the pile. Use it when huge meetings, like an assembly, mean nothing.

The paper leaves k, I_abs, K and I_rel to the user. That is the gap our rule fills.

## What noise is

In the synthetic test we invent 500 people in 10 planted groups of 50. We create two kinds of meetings.

- Community meetings draw everyone from one group. They are pure.
- Noise meetings draw people at random from all 500. They almost always mix groups.

Noise is there to try to fool the method into gluing groups together. The noise fraction p sets how many noise meetings exist: p times 500 per size. At p = 0.4 that is 200 per size, 600 in total, against 1500 community meetings.

## What "size cut" means

In the paper's own test, community meetings have sizes 6 to 8 and noise meetings have sizes 3 to 5, or the mirror. Size alone separates them. Keep only meetings of size 6 or more and every noise meeting is gone. That is a clean size cut.

We asked what happens when the cut is not clean.

- Partial overlap: community sizes 5 to 7, noise sizes 4 to 6. Sizes 5 and 6 appear on both sides, so no filter is perfect. Result: still works, because one pure size is enough to filter on.
- Full overlap: both 4 to 6. Size tells you nothing. Result: both variants break.

## What ECS is

ECS compares two groupings of the same people and gives a number from 0 to 1. Here the two groupings are the planted truth and what the method found. 1 means identical. Near 0 means unrelated. "Clustering", "grouping" and "community assignment" all mean the same thing.

We need a special score because the method's groups can overlap and can leave people out, and plain accuracy cannot handle that.

The idea: for each person, write down who they are grouped with in the truth and who they are grouped with in the result. If the two lists agree for everyone, the score is 1. Average over people. People left out by the method count as a group of one. The PageRank detail is only how "who I am grouped with" is turned into numbers. Not needed on stage.

Coverage is a second number: the fraction of people placed in any group at all.

## Three words from E3

- Oracle: parameters chosen by looking at the true answer. A cheating upper bound.
- Default: the parameters the paper suggests.
- Rule: our choice made without labels. Sweep the parameters, throw out settings where one group swallows the rest (largest more than twice the second), pick the setting whose groups are large but not giant. If nothing survives, use the default.

## One-minute version

Groups in real life are meetings of many people, not pairs. This paper finds communities by chaining meetings that overlap. It has two variants and four hand-set parameters. We rebuilt it, checked that it recovers planted groups exactly when community and noise meetings differ in size, showed it breaks when they do not, and added a simple rule that picks the parameters without labels. The rule beats the paper's default by a lot and stays below the cheating upper bound. On real committee data it does not help.
