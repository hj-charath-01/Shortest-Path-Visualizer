"""
algorithms.py
=============
Core graph-search algorithms for the Route Planner project.

All three algorithms work on a Graph object (see graph.py) and return
an AlgoResult with the shortest path, visited-node order, and timing.
"""

from __future__ import annotations
import heapq
import time
import math
from dataclasses import dataclass, field
from typing import Any, Optional
from graph import Graph


# ─────────────────────────────────────────────────────────────────────────────
#  Result container
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AlgoResult:
    algorithm:     str
    path:          list[Any]          # ordered list of node ids (empty = no path)
    path_cost:     float              # total edge weight of the path
    visited_order: list[Any]          # nodes settled, in order
    visited_count: int
    compute_ms:    float              # wall-clock time in milliseconds


# ─────────────────────────────────────────────────────────────────────────────
#  Dijkstra
# ─────────────────────────────────────────────────────────────────────────────

def dijkstra(graph: Graph, source: Any, target: Any) -> AlgoResult:
    """
    Classic Dijkstra's algorithm with a binary min-heap.

    Guarantees the globally optimal shortest path for non-negative weights.
    Time complexity: O((V + E) log V).
    """
    t0 = time.perf_counter()

    dist:          dict[Any, float] = {source: 0.0}
    prev:          dict[Any, Any]   = {source: None}
    visited:       set[Any]         = set()
    visited_order: list[Any]        = []
    heap = [(0.0, source)]

    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        visited_order.append(u)

        if u == target:
            break

        for v, w in graph.neighbors(u):
            nd = d + w
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))

    path = _reconstruct(prev, source, target)
    return AlgoResult(
        algorithm     = "Dijkstra",
        path          = path,
        path_cost     = dist.get(target, math.inf),
        visited_order = visited_order,
        visited_count = len(visited),
        compute_ms    = (time.perf_counter() - t0) * 1000,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  A*
# ─────────────────────────────────────────────────────────────────────────────

def a_star(graph: Graph, source: Any, target: Any,
           heuristic=None) -> AlgoResult:
    """
    A* search with a caller-supplied admissible heuristic.

    If no heuristic is given, falls back to Euclidean distance (requires
    graph nodes to have (lat, lon) coordinates stored in graph.node_pos).

    Time complexity: O((V + E) log V) in the worst case; typically much
    faster than Dijkstra because the heuristic prunes irrelevant branches.
    """
    t0 = time.perf_counter()

    if heuristic is None:
        heuristic = _euclidean_heuristic(graph, target)

    g:             dict[Any, float] = {source: 0.0}
    prev:          dict[Any, Any]   = {source: None}
    visited:       set[Any]         = set()
    visited_order: list[Any]        = []
    # heap entries: (f-score, g-score, node)
    heap = [(heuristic(source), 0.0, source)]

    while heap:
        _, d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        visited_order.append(u)

        if u == target:
            break

        for v, w in graph.neighbors(u):
            ng = d + w
            if ng < g.get(v, math.inf):
                g[v]    = ng
                prev[v] = u
                f = ng + heuristic(v)
                heapq.heappush(heap, (f, ng, v))

    path = _reconstruct(prev, source, target)
    return AlgoResult(
        algorithm     = "A*",
        path          = path,
        path_cost     = g.get(target, math.inf),
        visited_order = visited_order,
        visited_count = len(visited),
        compute_ms    = (time.perf_counter() - t0) * 1000,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Bidirectional Dijkstra
# ─────────────────────────────────────────────────────────────────────────────

def bidirectional_dijkstra(graph: Graph, source: Any, target: Any) -> AlgoResult:
    """
    Bidirectional Dijkstra: two simultaneous Dijkstra searches expanding
    from source (forward) and target (backward).

    Terminates when the sum of the two heap tops meets or exceeds the best
    path found so far — approximately halving the search space compared
    with unidirectional Dijkstra.

    Requires the graph to expose a `reverse_neighbors(node)` method.
    Time complexity: roughly O((V_f + V_b + E) log V), where V_f and V_b
    are the sizes of the forward and backward settled sets.
    """
    t0 = time.perf_counter()

    # Forward structures
    dist_f:  dict[Any, float] = {source: 0.0}
    prev_f:  dict[Any, Any]   = {source: None}
    vis_f:   set[Any]         = set()
    heap_f                    = [(0.0, source)]

    # Backward structures
    dist_b:  dict[Any, float] = {target: 0.0}
    prev_b:  dict[Any, Any]   = {target: None}
    vis_b:   set[Any]         = set()
    heap_b                    = [(0.0, target)]

    best_cost  = math.inf
    meet_node  = None
    vis_order: list[tuple[str, Any]] = []  # ('F'|'B', node)

    def _step_forward():
        nonlocal best_cost, meet_node
        if not heap_f:
            return
        d, u = heapq.heappop(heap_f)
        if u in vis_f:
            return
        vis_f.add(u)
        vis_order.append(('F', u))

        total = d + dist_b.get(u, math.inf)
        if total < best_cost:
            best_cost = total
            meet_node = u

        for v, w in graph.neighbors(u):
            nd = d + w
            if nd < dist_f.get(v, math.inf):
                dist_f[v] = nd
                prev_f[v] = u
                heapq.heappush(heap_f, (nd, v))

    def _step_backward():
        nonlocal best_cost, meet_node
        if not heap_b:
            return
        d, u = heapq.heappop(heap_b)
        if u in vis_b:
            return
        vis_b.add(u)
        vis_order.append(('B', u))

        total = dist_f.get(u, math.inf) + d
        if total < best_cost:
            best_cost = total
            meet_node = u

        for v, w in graph.reverse_neighbors(u):
            nd = d + w
            if nd < dist_b.get(v, math.inf):
                dist_b[v] = nd
                prev_b[v] = u
                heapq.heappush(heap_b, (nd, v))

    while heap_f or heap_b:
        _step_forward()
        _step_backward()
        # Stopping criterion
        top_f = heap_f[0][0] if heap_f else math.inf
        top_b = heap_b[0][0] if heap_b else math.inf
        if top_f + top_b >= best_cost:
            break

    # Reconstruct path through meeting node
    path: list[Any] = []
    if meet_node is not None:
        fwd = _reconstruct(prev_f, source, meet_node)
        bwd = _reconstruct(prev_b, target, meet_node)[1:]  # exclude meet_node duplicate
        path = fwd + list(reversed(bwd))

    return AlgoResult(
        algorithm     = "Bidirectional Dijkstra",
        path          = path,
        path_cost     = best_cost if path else math.inf,
        visited_order = [n for _, n in vis_order],
        visited_count = len(vis_f) + len(vis_b),
        compute_ms    = (time.perf_counter() - t0) * 1000,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _reconstruct(prev: dict, source: Any, target: Any) -> list[Any]:
    """Trace `prev` pointers from target back to source."""
    path: list[Any] = []
    cur = target
    while cur is not None:
        path.append(cur)
        cur = prev.get(cur)
        if cur == source:
            path.append(source)
            break
    path.reverse()
    return path if (path and path[0] == source) else []


def _euclidean_heuristic(graph: Graph, target: Any):
    """Return a heuristic function using straight-line (Euclidean) distance."""
    tx, ty = graph.node_pos.get(target, (0, 0))
    def h(u: Any) -> float:
        ux, uy = graph.node_pos.get(u, (0, 0))
        return math.hypot(tx - ux, ty - uy)
    return h
