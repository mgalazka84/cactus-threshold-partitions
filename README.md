# Cactus threshold partitions

Python implementation of maximum local-threshold partitions for simple cactus graphs.
For each vertex `v`, `thresholds[v]` specifies the minimum number of neighbours
that must belong to the same part. The solver returns the maximum number of
nonempty parts and a corresponding partition.

## Requirements

Python 3.10 or newer. No third-party dependencies.

## Usage

```python
from cactus_quorum import solve_cactus

edges = [(0, 1), (1, 2), (2, 0), (0, 3), (3, 4), (4, 0)]
optimum, parts, deleted_edge_ids = solve_cactus(5, edges)
assert optimum == 2

# Optional individual thresholds:
optimum, parts, deleted_edge_ids = solve_cactus(5, edges, [2, 1, 1, 1, 1])
```

Vertices are numbered `0, ..., n-1`. Edge IDs are positions in the input
edge list. Without explicit thresholds, each vertex uses `degree(v) // 2`
(ordinary quorum coloring). Thresholds must be integers between zero and
the vertex degree.

Empty graphs, isolated vertices and disconnected cactus graphs are supported.
Invalid inputs, loops, parallel edges and non-cactus graphs raise `ValueError`.
An optimal partition need not be unique.

The algorithm uses linear space and a linear number of operations in the
input size. Python dictionary and set operations use their usual expected-time
cost model.

## Tests and verification

```bash
python3 -m unittest discover -s tests -v
python3 verify.py --output results/verification.json
python3 verify_thresholds.py --output results/threshold_verification.json
```

Alternatively, run `make verify`. The scripts generate JSON reports in
`results/`, which is ignored by Git. GitHub Actions runs these checks on
pushes and pull requests.

- `cactus_quorum.py`: solver, reconstruction and input validation.
- `tests/test_solver.py`: boundary cases and invalid inputs.
- `verify.py`: exhaustive edge-deletion and direct-partition checks,
  reproducible random inputs, and large graph cases.
- `verify_thresholds.py`: all feasible thresholds on small cactus graphs
  and an independent graph-recognition check.
