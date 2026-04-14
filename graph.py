"""
graph.py
========
Weighted directed graph with support for:
  - adjacency-list storage
  - reverse-edge lookup (needed by bidirectional search)
  - optional (x, y) or (lat, lon) node coordinates for heuristics
  - I/O helpers (CSV edge list, OSMnx integration)
"""

from __future__ import annotations
import csv
import math
from collections import defaultdict
from typing import Any, Iterable, Iterator, Optional, Tuple


EdgeList = list[Tuple[Any, float]]   # [(neighbor, weight), ...]


class Graph:
    """
    Undirected weighted graph stored as two adjacency lists
    (forward + reverse) so bidirectional search works without
    having to build a separate reversed copy.

    For undirected graphs both lists are identical; for directed
    graphs they differ.
    """

    def __init__(self, directed: bool = False) -> None:
        self.directed  = directed
        self._fwd: dict[Any, EdgeList] = defaultdict(list)
        self._rev: dict[Any, EdgeList] = defaultdict(list)
        self.node_pos:  dict[Any, Tuple[float, float]] = {}   # node → (x, y)

    # ── Mutation ──────────────────────────────────────────────────────────────

    def add_node(self, node: Any, pos: Optional[Tuple[float, float]] = None) -> None:
        """Register a node (and optionally its 2-D coordinates)."""
        if node not in self._fwd:
            self._fwd[node] = []
            self._rev[node] = []
        if pos is not None:
            self.node_pos[node] = pos

    def add_edge(self, u: Any, v: Any, weight: float = 1.0) -> None:
        """Add a weighted edge u → v (and v → u if undirected)."""
        self.add_node(u); self.add_node(v)
        self._fwd[u].append((v, weight))
        self._rev[v].append((u, weight))
        if not self.directed:
            self._fwd[v].append((u, weight))
            self._rev[u].append((v, weight))

    # ── Query ─────────────────────────────────────────────────────────────────

    def neighbors(self, node: Any) -> EdgeList:
        """Forward neighbours of `node`: [(v, w), ...]"""
        return self._fwd.get(node, [])

    def reverse_neighbors(self, node: Any) -> EdgeList:
        """Reverse neighbours of `node` (needed by bidirectional search)."""
        return self._rev.get(node, [])

    @property
    def nodes(self) -> list[Any]:
        return list(self._fwd.keys())

    @property
    def num_nodes(self) -> int:
        return len(self._fwd)

    @property
    def num_edges(self) -> int:
        total = sum(len(v) for v in self._fwd.values())
        return total if self.directed else total // 2

    # ── I/O ───────────────────────────────────────────────────────────────────

    @classmethod
    def from_edge_csv(cls, path: str, directed: bool = False,
                      delimiter: str = ',') -> "Graph":
        """
        Load from a CSV with columns: source, target[, weight].
        Weight defaults to 1.0 if the column is absent.

        Example file:
            A,B,4.2
            B,C,1.5
            A,C,9.0
        """
        g = cls(directed=directed)
        with open(path, newline='') as f:
            for row in csv.reader(f, delimiter=delimiter):
                if not row or row[0].startswith('#'):
                    continue
                u, v = row[0].strip(), row[1].strip()
                w = float(row[2]) if len(row) > 2 else 1.0
                g.add_edge(u, v, w)
        return g

    @classmethod
    def from_osmnx(cls, place: str, network_type: str = 'drive') -> "Graph":
        """
        Build a road-network graph from OpenStreetMap via OSMnx.

        Requires: pip install osmnx

        Usage:
            g = Graph.from_osmnx('Singapore', network_type='drive')
        """
        try:
            import osmnx as ox
        except ImportError:
            raise ImportError("osmnx is not installed. Run: pip install osmnx")

        ox_graph = ox.graph_from_place(place, network_type=network_type)
        ox_graph = ox.add_edge_speeds(ox_graph)
        ox_graph = ox.add_edge_travel_times(ox_graph)

        g = cls(directed=True)
        for node_id, data in ox_graph.nodes(data=True):
            g.add_node(node_id, pos=(data['x'], data['y']))

        for u, v, data in ox_graph.edges(data=True):
            # Use travel_time (seconds) as weight for realistic routing
            w = data.get('travel_time', data.get('length', 1.0))
            g.add_edge(u, v, float(w))

        return g

    # ── Generators ────────────────────────────────────────────────────────────

    @classmethod
    def grid(cls, rows: int, cols: int) -> "Graph":
        """Create a rows×cols undirected grid graph (4-connected)."""
        g = cls(directed=False)
        for r in range(rows):
            for c in range(cols):
                g.add_node((r, c), pos=(c, -r))  # x=col, y=-row for display
                if r > 0: g.add_edge((r, c), (r-1, c))
                if c > 0: g.add_edge((r, c), (r, c-1))
        return g

    # ── Utilities ─────────────────────────────────────────────────────────────

    def haversine_weight(self, u: Any, v: Any) -> float:
        """
        Great-circle distance (km) between two nodes given (lat, lon) coords.
        Useful as an admissible heuristic for real-world maps.
        """
        (lat1, lon1) = self.node_pos[u]
        (lat2, lon2) = self.node_pos[v]
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * \
            math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))

    def __repr__(self) -> str:
        kind = "directed" if self.directed else "undirected"
        return f"Graph({kind}, nodes={self.num_nodes}, edges={self.num_edges})"
