"""Exhaust all local thresholds through order five and audit recognition.

The cactus oracle counts simple paths after removing each edge and does not
call the solver's block decomposition. The optimum oracle enumerates vertex
partitions directly; it does not use edge deletion or dynamic programming.
"""
import argparse
import itertools
import json
from pathlib import Path
import platform
import time

from cactus_quorum import blocks_of_cactus, solve_cactus
from verify import partitions


def is_cactus_by_paths(n, edges):
    adjacency = [[] for _ in range(n)]
    for i, (u, v) in enumerate(edges):
        adjacency[u].append((v, i))
        adjacency[v].append((u, i))
    for removed, (source, target) in enumerate(edges):
        paths = 0
        stack = [(source, 1 << source)]
        while stack:
            v, visited = stack.pop()
            for u, eid in adjacency[v]:
                if eid == removed or (visited >> u) & 1:
                    continue
                if u == target:
                    paths += 1
                    if paths >= 2:
                        return False
                else:
                    stack.append((u, visited | (1 << u)))
    return True


def check_witness(n, edges, thresholds, optimum, parts):
    labels = [-1] * n
    assert len(parts) == optimum
    for index, part in enumerate(parts):
        assert part
        for v in part:
            assert 0 <= v < n and labels[v] == -1
            labels[v] = index
    assert all(index >= 0 for index in labels)
    internal_degree = [0] * n
    for u, v in edges:
        if labels[u] == labels[v]:
            internal_degree[u] += 1
            internal_degree[v] += 1
    assert all(a >= b for a, b in zip(internal_degree, thresholds))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=Path('results/threshold_verification.json'))
    args = parser.parse_args()
    started = time.perf_counter()
    counts = dict(simple_graphs_recognition_checked=0,
                  cacti_order_1_to_6=0, threshold_instances=0,
                  threshold_graphs_including_empty=0, mismatches=0)
    for n in range(7):
        possible = list(itertools.combinations(range(n), 2))
        for mask in range(1 << len(possible)):
            edges = [e for i, e in enumerate(possible) if (mask >> i) & 1]
            reference_cactus = is_cactus_by_paths(n, edges)
            try:
                blocks_of_cactus(n, edges)
                accepted = True
            except ValueError:
                accepted = False
            assert accepted == reference_cactus, (n, edges)
            counts['simple_graphs_recognition_checked'] += 1
            if not reference_cactus:
                continue
            if n:
                counts['cacti_order_1_to_6'] += 1
            if n > 5:
                continue
            counts['threshold_graphs_including_empty'] += 1
            degrees = [0] * n
            for u, v in edges:
                degrees[u] += 1
                degrees[v] += 1
            # Equal internal-degree vectors are interchangeable for this oracle.
            candidates = {}
            for labels in partitions(n):
                internal = [0] * n
                for u, v in edges:
                    if labels[u] == labels[v]:
                        internal[u] += 1
                        internal[v] += 1
                key = tuple(internal)
                candidates[key] = max(candidates.get(key, 0), len(set(labels)))
            for thresholds in itertools.product(*(range(d + 1) for d in degrees)):
                expected = max(k for vector, k in candidates.items()
                               if all(a >= b for a, b in zip(vector, thresholds)))
                optimum, parts, _ = solve_cactus(n, edges, thresholds)
                assert optimum == expected, (n, edges, thresholds, optimum, expected)
                check_witness(n, edges, thresholds, optimum, parts)
                counts['threshold_instances'] += 1
    assert counts['cacti_order_1_to_6'] == 10025
    counts['seconds'] = round(time.perf_counter() - started, 3)
    counts['python'] = platform.python_version()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(counts, indent=2) + '\n')
    print(json.dumps(counts, indent=2))


if __name__ == '__main__':
    main()
