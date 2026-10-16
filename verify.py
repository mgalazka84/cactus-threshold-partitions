"""Independent small-instance checks; run with Python 3, no dependencies."""
import itertools
import json
import argparse
import platform
import random
import time
from pathlib import Path
from cactus_quorum import blocks_of_cactus, solve_cactus


def brute_edges(n, edges, thresholds):
    degree = [0] * n
    for u, v in edges:
        degree[u] += 1
        degree[v] += 1
    caps = [d-t for d, t in zip(degree, thresholds)]
    best = 0
    for mask in range(1 << len(edges)):
        removed = [0] * n
        for i, (u, v) in enumerate(edges):
            if (mask >> i) & 1:
                removed[u] += 1
                removed[v] += 1
        if any(x > b for x, b in zip(removed, caps)):
            continue
        par = list(range(n))
        def root(v):
            while par[v] != v:
                v = par[v]
            return v
        components = n
        for i, (u, v) in enumerate(edges):
            if not ((mask >> i) & 1):
                u, v = root(u), root(v)
                if u != v:
                    par[u] = v
                    components -= 1
        best = max(best, components)
    return best


def partitions(n):
    if not n:
        yield []
        return
    labels = [0] * n
    def rec(i, largest):
        if i == n:
            yield labels[:]
            return
        for x in range(largest + 2):
            labels[i] = x
            yield from rec(i + 1, max(largest, x))
    yield from rec(1, 0)


def brute_partitions(n, edges, thresholds):
    best = 0
    for labels in partitions(n):
        score = [0] * n
        for u, v in edges:
            if labels[u] == labels[v]:
                score[u] += 1
                score[v] += 1
        if all(a >= b for a, b in zip(score, thresholds)):
            best = max(best, len(set(labels)))
    return best


def random_cactus(rng, target):
    n, edges = 1, []
    while n < target:
        v = rng.randrange(n)
        length = rng.choice([1, 1, 2, 3, 4])
        length = min(length, target-n)
        if length == 1:
            edges.append((v, n))
        else:
            walk = [v] + list(range(n, n+length)) + [v]
            edges.extend(zip(walk, walk[1:]))
        n += length
    return n, edges


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('results/verification.json'))
    args = parser.parse_args()
    rng = random.Random(20261016)
    counts = dict(labelled_cacti=0, exact_comparisons=0,
                  partition_oracle_comparisons=0, randomized_cacti=0)
    started = time.perf_counter()
    for n in range(1, 7):
        possible = list(itertools.combinations(range(n), 2))
        for graph_mask in range(1 << len(possible)):
            edges = [e for i, e in enumerate(possible) if (graph_mask >> i) & 1]
            try:
                adj, _, _ = blocks_of_cactus(n, edges)
            except ValueError:
                continue
            counts['labelled_cacti'] += 1
            degree = [len(x) for x in adj]
            scenarios = [[d//2 for d in degree],
                         [rng.randrange(d+1) for d in degree]]
            for thresholds in scenarios:
                got = solve_cactus(n, edges, thresholds)[0]
                expect = brute_edges(n, edges, thresholds)
                assert got == expect, (n, edges, thresholds, got, expect)
                counts['exact_comparisons'] += 1
                if n <= 5:
                    expect_p = brute_partitions(n, edges, thresholds)
                    assert got == expect_p, (n, edges, thresholds, got, expect_p)
                    counts['partition_oracle_comparisons'] += 1
    for _ in range(1500):
        n, edges = random_cactus(rng, rng.randrange(2, 12))
        degree = [0] * n
        for u, v in edges:
            degree[u] += 1
            degree[v] += 1
        thresholds = [rng.randrange(d+1) for d in degree]
        got = solve_cactus(n, edges, thresholds)[0]
        expect = brute_edges(n, edges, thresholds)
        assert got == expect, (n, edges, thresholds, got, expect)
        counts['randomized_cacti'] += 1
        counts['exact_comparisons'] += 1
    counts['small_checks_seconds'] = round(time.perf_counter()-started, 3)
    timings = []
    for family in ('path', 'star', 'triangle_flower'):
        n = 50001
        if family == 'path':
            edges = [(v-1, v) for v in range(1, n)]
        elif family == 'star':
            edges = [(0, v) for v in range(1, n)]
        else:
            edges = [e for v in range(1, n, 2)
                     for e in ((0, v), (v, v+1), (v+1, 0))]
        tic = time.perf_counter()
        got = solve_cactus(n, edges)[0]
        timings.append(dict(family=family, n=n, m=len(edges), optimum=got,
                            seconds=round(time.perf_counter()-tic, 3)))
    counts['large_sanity_checks'] = timings
    counts['seed'] = 20261016
    counts['environment'] = dict(python=platform.python_version(),
                                 implementation=platform.python_implementation(),
                                 platform=platform.platform())
    print(json.dumps(counts, indent=2))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('w') as out:
        json.dump(counts, out, indent=2)


if __name__ == '__main__':
    main()
