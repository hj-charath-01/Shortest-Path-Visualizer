# Route Planner

An interactive city-map route planner implementing and comparing three
classic shortest-path algorithms with step-by-step animation.

---

## Project Structure

```
├── graph.py          Weighted directed/undirected graph + OSMnx loader
├── algorithms.py     Dijkstra · A* · Bidirectional Dijkstra
├── main.py           CLI benchmark + matplotlib/folium visualiser
├── pathfinder.html   Interactive browser visualiser (Leaflet.js)
└── README.md
```

---

## Algorithms Implemented

| Algorithm                  | Complexity                | Notes                                            |
|----------------------------|---------------------------|--------------------------------------------------|
| **Dijkstra**               | O((V+E) log V)            | Optimal, explores uniformly in all directions    |
| **A\***                    | O((V+E) log V) worst-case | Heuristic guides search; far fewer nodes visited |
| **Bidirectional Dijkstra** | ~½ Dijkstra               | Two simultaneous frontiers meeting in the middle |

---

## Quickstart (Python)

```bash
# Install dependencies
pip install matplotlib osmnx folium   # osmnx + folium optional — only needed for real map data

# Run on a random 30×40 weighted grid, compare all three algorithms
python main.py --mode grid --rows 30 --cols 40

# Load a real city road network from OpenStreetMap
python main.py --mode osm --place "Singapore"

# Load your own edge-list CSV
python main.py --mode csv --file my_roads.csv --source A --target Z

# Run only A* (skip the others)
python main.py --mode grid --algo astar

# Skip visualisation (print table only)
python main.py --mode grid --no-viz

# Save matplotlib comparison chart to a custom filename
python main.py --mode grid --out my_chart.png
```

Sample output:
```
Graph: Graph(undirected, nodes=1200, edges=2270)
Source: (0, 0)  →  Target: (29, 39)

────────────────────────────────────────────────────────────────────────
ALGORITHM                    VISITED   PATH LEN       COST  TIME (ms)
────────────────────────────────────────────────────────────────────────
Dijkstra                        1198         68     295.42      4.321
A*                               412         68     295.42      1.076
Bidirectional Dijkstra           634         68     295.42      2.209
────────────────────────────────────────────────────────────────────────

Speedup (nodes visited vs Dijkstra baseline):
  Dijkstra                         1.00×
  A*                               2.91×
  Bidirectional Dijkstra           1.89×
```

---

## Visualisation Modes

### Grid / CSV — Matplotlib

Running in `grid` or `csv` mode produces a side-by-side matplotlib comparison chart
(saved to `comparison.png` by default). Each panel shows visited nodes (green),
the shortest path (amber), and start/end markers.

### OSM — Interactive Folium Map

Running in `osm` mode opens an interactive Leaflet map in your browser (`route_map.html`).
Each algorithm gets its own toggleable layer; a stats legend is pinned to the bottom of the page.

It also exports `results.json` — a machine-readable snapshot of node positions, visited
orders, and paths — which can be loaded directly into the browser visualiser below.

---

## Interactive Browser Visualiser (`pathfinder.html`)

Open `pathfinder.html` in any modern browser. No build step required.

**Loading data:**

| Method          | How                                                                   |
|-----------------|-----------------------------------------------------------------------|
| From Python run | Run `python main.py --mode osm …` → drag `results.json` onto the page |
| File picker     | Click **Load results.json** and select the file                       |
| Demo mode       | Click **Try Demo** to explore a synthetic Singapore dataset           |

**Controls:**

| Action             | How                                                  |
|--------------------|------------------------------------------------------|
| Switch algorithm   | Click a tab (Dijkstra / A* / Bidirectional Dijkstra) |
| Animate search     | Press **▶ Run**                                      |
| Stop mid-animation | Press **⏹ Stop**                                     |
| Clear overlay      | Press **Clear**                                      |
| Adjust speed       | **Slow / Normal / Fast** buttons                     |
| Toggle layers      | Use the layer control (top-right of map)             |
|--------------------|------------------------------------------------------|

Stats (visited nodes, path length, cost, compute time) are displayed in the top bar
and in a detail panel once the animation completes.

---

## Extension Ideas

1. **Weighted terrain** — assign higher edge costs to "mountain" or "water" cells and observe how A* avoids them.
2. **Real OSM data** — use `Graph.from_osmnx('Your City')` for genuine street routing.
3. **Diagonal movement** — add 8-directional edges (weight √2) and switch to Euclidean heuristic in A*.
4. **Contraction Hierarchies** — preprocess the graph for sub-millisecond queries on large road networks.
5. **Time-expanded graph** — model transit schedules as edges with time-dependent weights.

---

## References

- Dijkstra, E.W. (1959). *A note on two problems in connexion with graphs.*
- Hart, Nilsson, Raphael (1968). *A formal basis for the heuristic determination of minimum cost paths.*
- Pohl, I. (1971). *Bi-directional search.*
- Boeing, G. (2017). *OSMnx: New methods for acquiring, constructing, analyzing, and visualizing complex street networks.*
