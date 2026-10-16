"""Exact local-threshold partitions of simple cactus graphs.

No third-party dependencies. Integer vertex labels are 0,...,n-1.
"""


def blocks_of_cactus(n, edges):
    """Iterative Tarjan decomposition, with cactus validation."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 0:
        raise ValueError("n must be a nonnegative integer")
    adj = [[] for _ in range(n)]
    seen = set()
    for eid, (u, v) in enumerate(edges):
        if (not isinstance(u, int) or isinstance(u, bool)
                or not isinstance(v, int) or isinstance(v, bool)
                or not (0 <= u < n and 0 <= v < n) or u == v):
            raise ValueError("Expected a simple graph")
        key = (min(u, v), max(u, v))
        if key in seen:
            raise ValueError("Parallel edge")
        seen.add(key)
        adj[u].append((v, eid))
        adj[v].append((u, eid))
    disc = [-1] * n
    low = [0] * n
    par = [-1] * n
    pe = [-1] * n
    stack_edges, blocks, roots = [], [], []
    timer = 0
    for root in range(n):
        if disc[root] >= 0:
            continue
        roots.append(root)
        disc[root] = low[root] = timer
        timer += 1
        stack = [(root, iter(adj[root]))]
        while stack:
            v, it = stack[-1]
            try:
                u, eid = next(it)
            except StopIteration:
                stack.pop()
                if par[v] >= 0:
                    p = par[v]
                    low[p] = min(low[p], low[v])
                    if low[v] >= disc[p]:
                        block = []
                        while True:
                            eid = stack_edges.pop()
                            block.append(eid)
                            if eid == pe[v]:
                                break
                        blocks.append(block)
                continue
            if eid == pe[v]:
                continue
            if disc[u] < 0:
                par[u], pe[u] = v, eid
                stack_edges.append(eid)
                disc[u] = low[u] = timer
                timer += 1
                stack.append((u, iter(adj[u])))
            elif disc[u] < disc[v]:
                stack_edges.append(eid)
                low[v] = min(low[v], disc[u])
    for block in blocks:
        if len(block) == 1:
            continue
        degree = {}
        for eid in block:
            for v in edges[eid]:
                degree[v] = degree.get(v, 0) + 1
        if len(degree) != len(block) or any(d != 2 for d in degree.values()):
            raise ValueError("Graph is not a cactus")
    return adj, blocks, roots


def solve_cactus(n, edges, thresholds=None):
    """Return (maximum number of parts, parts, deleted_edge_ids).

    Each vertex v must have at least thresholds[v] neighbours in its part.
    Default thresholds[v] = degree(v)//2 gives ordinary quorum coloring.
    The algorithm takes O(n+m) time and space on a word RAM, including
    reconstruction. This Python implementation uses standard hash tables;
    its linear operation count assumes their usual expected constant cost.
    Input edge order determines edge IDs; an optimal partition need not
    be unique. Empty and disconnected graphs are supported.
    """
    edges = list(edges)
    adj, blocks, roots = blocks_of_cactus(n, edges)
    degree = [len(a) for a in adj]
    if thresholds is None:
        thresholds = [d // 2 for d in degree]
    else:
        thresholds = list(thresholds)
    if len(thresholds) != n or any(not isinstance(t, int) or isinstance(t, bool) or t < 0 or t > d
                                  for t, d in zip(thresholds, degree)):
        raise ValueError("Thresholds must be integers between 0 and degree")
    capacity = [d - t for d, t in zip(degree, thresholds)]
    incidence = [[] for _ in range(n + len(blocks))]
    for j, block in enumerate(blocks):
        vertices = set(v for eid in block for v in edges[eid])
        for v in vertices:
            incidence[v].append(n + j)
            incidence[n + j].append(v)
    parent = [-2] * len(incidence)
    order = []
    for r in roots:
        parent[r] = -1
        todo = [r]
        while todo:
            z = todo.pop()
            order.append(z)
            for w in incidence[z]:
                if w != parent[z]:
                    parent[w] = z
                    todo.append(w)
    av = [None] * n
    messages = [None] * len(blocks)
    counts = [None] * n
    for z in reversed(order):
        if z < n:
            base = units = pairs = 0
            for w in incidence[z]:
                if w == parent[z]:
                    continue
                msg = messages[w - n]
                f = msg['f']
                base += f[0]
                if len(f) == 2:
                    u, d = f[1] - f[0], 0
                else:
                    profile = (f[1] - f[0], f[2] - f[0])
                    assert profile in ((0, 0), (0, 1), (1, 1), (1, 2))
                    u, d = {(0, 0): (0, 0), (0, 1): (0, 1),
                            (1, 1): (1, 0), (1, 2): (2, 0)}[profile]
                msg['units'], msg['pairs'] = u, d
                units += u
                pairs += d
            counts[z] = (units, pairs)
            av[z] = []
            for t in range(3):
                c = capacity[z] - t
                if c < 0:
                    av[z].append(None)
                else:
                    av[z].append(base + min(units, c)
                                 + min(pairs, max(0, c - units) // 2))
            continue
        j, p = z - n, parent[z]
        block = blocks[j]
        if len(block) == 1:
            eid = block[0]
            u, v = edges[eid]
            child = v if u == p else u
            e = [av[child][0], None if av[child][1] is None else 1 + av[child][1]]
            bit = 1 if e[1] is not None and e[1] > e[0] else 0
            messages[j] = dict(f=[e[0], e[bit]], kind='bridge',
                               child=child, eid=eid, bit=bit)
            continue
        local = {}
        for eid in block:
            u, v = edges[eid]
            local.setdefault(u, []).append((v, eid))
            local.setdefault(v, []).append((u, eid))
        vertices, cycle_edges = [p], []
        prev, current = -1, p
        while True:
            nxt, eid = next((u, e) for u, e in local[current] if u != prev)
            cycle_edges.append(eid)
            if nxt == p:
                break
            vertices.append(nxt)
            prev, current = current, nxt
        traces = []
        exact = [None, None, None]
        ends = [None, None, None]
        for first in (0, 1):
            traces.append((None, first))
            dp = {(first, first): (first, len(traces) - 1)}
            for i in range(1, len(vertices)):
                new = {}
                for (previous, hit), (score, trace) in dp.items():
                    for bit in (0, 1):
                        child_score = av[vertices[i]][previous + bit]
                        if child_score is None:
                            continue
                        key = (bit, hit or bit)
                        value = score + bit + child_score
                        if key not in new or value > new[key][0]:
                            traces.append((trace, bit))
                            new[key] = (value, len(traces) - 1)
                dp = new
            for (last, hit), (score, trace) in dp.items():
                q = first + last
                value = score - int(bool(hit))
                if exact[q] is None or value > exact[q]:
                    exact[q], ends[q] = value, trace
        best = [0]
        for q in (1, 2):
            best.append(q if exact[q] is not None and exact[q] > exact[best[-1]] else best[-1])
        messages[j] = dict(kind='cycle', f=[exact[k] for k in best],
                           traces=traces, ends=[ends[k] for k in best],
                           vertices=vertices, edges=cycle_edges)
    optimum = len(roots) + sum(av[r][0] for r in roots)
    deleted = set()
    tasks = [('v', r, 0) for r in roots]
    while tasks:
        kind, z, t = tasks.pop()
        if kind == 'v':
            c = capacity[z] - t
            units, pairs = counts[z]
            u_left, d_left = min(units, c), min(pairs, max(0, c - units) // 2)
            for w in incidence[z]:
                if w == parent[z]:
                    continue
                msg = messages[w - n]
                take_u = min(u_left, msg['units'])
                u_left -= take_u
                take_d = min(d_left, msg['pairs'])
                d_left -= take_d
                tasks.append(('b', w - n, take_u + 2 * take_d))
        else:
            msg = messages[z]
            if msg['kind'] == 'bridge':
                bit = msg['bit'] if t else 0
                if bit:
                    deleted.add(msg['eid'])
                tasks.append(('v', msg['child'], bit))
            else:
                trace, bits = msg['ends'][t], []
                while trace is not None:
                    trace, bit = msg['traces'][trace]
                    bits.append(bit)
                bits.reverse()
                for eid, bit in zip(msg['edges'], bits):
                    if bit:
                        deleted.add(eid)
                for i in range(1, len(msg['vertices'])):
                    tasks.append(('v', msg['vertices'][i], bits[i - 1] + bits[i]))
    parts, used = [], set()
    for r in range(n):
        if r in used:
            continue
        used.add(r)
        component, todo = [], [r]
        while todo:
            v = todo.pop()
            component.append(v)
            for u, eid in adj[v]:
                if eid not in deleted and u not in used:
                    used.add(u)
                    todo.append(u)
        parts.append(component)
    assert len(parts) == optimum
    labels = {v: j for j, part in enumerate(parts) for v in part}
    assert all(sum(labels[u] == labels[v] for u, _ in adj[v]) >= thresholds[v]
               for v in range(n))
    return optimum, parts, deleted
