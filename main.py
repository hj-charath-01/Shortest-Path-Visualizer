"""
main.py
=======
Entry point for the Route Planner project.

Usage examples
--------------
# Benchmark on a random grid
python main.py --mode grid --rows 50 --cols 80

# Load a real city from OpenStreetMap (opens interactive map in browser)
python main.py --mode osm --place "Singapore" --source <node_id> --target <node_id>

# Load from an edge-list CSV
python main.py --mode csv --file edges.csv --source A --target Z
"""

from __future__ import annotations
import argparse
import random
import sys
import textwrap
import webbrowser
import os
import json

from graph import Graph
from algorithms import dijkstra, a_star, bidirectional_dijkstra, AlgoResult

def export_results_json(graph, results, src, tgt, out="results.json"):
    data = {
        "nodes": {str(n): list(graph.node_pos[n]) for n in graph.node_pos},
        "results": []
    }
    for r in results:
        data["results"].append({
            "algorithm": r.algorithm,
            "visited_order": [str(n) for n in r.visited_order],
            "path": [str(n) for n in r.path],
            "path_cost": r.path_cost,
            "visited_count": r.visited_count,
            "compute_ms": r.compute_ms,
        })
    data["source"] = str(src)
    data["target"] = str(tgt)
    with open(out, "w") as f:
        json.dump(data, f)
    print(f"Exported results → {out}")


#  CLI

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Route Planner — Advanced Graph Algorithms Project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python main.py --mode grid --rows 40 --cols 60
              python main.py --mode csv  --file roads.csv --source NYC --target LA
              python main.py --mode osm  --place "Singapore"
              python main.py --mode osm  --place "Berlin, Germany" --algo astar
        """)
    )
    p.add_argument('--mode',   choices=['grid', 'csv', 'osm'], default='grid')
    p.add_argument('--rows',   type=int, default=30,  help='Grid rows  (grid mode)')
    p.add_argument('--cols',   type=int, default=40,  help='Grid cols  (grid mode)')
    p.add_argument('--file',   type=str, default='',  help='Edge CSV   (csv mode)')
    p.add_argument('--place',  type=str, default='Singapore', help='City name (osm mode)')
    p.add_argument('--source', type=str, default='',  help='Source node id')
    p.add_argument('--target', type=str, default='',  help='Target node id')
    p.add_argument('--algo',   type=str, default='all',
                   choices=['dijkstra', 'astar', 'bidir', 'all'],
                   help='Algorithm to run (default: all three)')
    p.add_argument('--no-viz', action='store_true', help='Skip visualisation')
    p.add_argument('--out',    type=str, default='comparison.png',
                   help='Output filename for grid/csv matplotlib chart (default: comparison.png)')
    return p


#  Graph builders

def build_grid_graph(rows: int, cols: int) -> tuple[Graph, tuple, tuple]:
    """Weighted grid with random edge weights in [1, 10]."""
    g = Graph(directed=False)
    for r in range(rows):
        for c in range(cols):
            g.add_node((r, c), pos=(c, r))
            if r > 0:
                g.add_edge((r, c), (r-1, c), weight=random.uniform(1, 10))
            if c > 0:
                g.add_edge((r, c), (r, c-1), weight=random.uniform(1, 10))
    src = (0, 0)
    tgt = (rows-1, cols-1)
    return g, src, tgt


def build_csv_graph(filepath: str, source: str, target: str) -> tuple[Graph, str, str]:
    g = Graph.from_edge_csv(filepath)
    return g, source, target


def build_osm_graph(place: str, source: str, target: str):
    print(f"  Downloading road network for '{place}' from OpenStreetMap…")
    g = Graph.from_osmnx(place)
    nodes = g.nodes
    src = int(source) if source else random.choice(nodes)
    tgt = int(target) if target else random.choice(nodes)
    return g, src, tgt


#  Run & report

def run_algorithms(g: Graph, src, tgt, which: str) -> list[AlgoResult]:
    runners = {
        'dijkstra': lambda: dijkstra(g, src, tgt),
        'astar':    lambda: a_star(g, src, tgt),
        'bidir':    lambda: bidirectional_dijkstra(g, src, tgt),
    }
    if which == 'all':
        selected = list(runners.values())
    else:
        selected = [runners[which]]
    return [fn() for fn in selected]

import json

def export_results_json(graph, results, src, tgt, out="results.json"):
    data = {
        "nodes": {str(n): list(graph.node_pos[n]) for n in graph.node_pos},
        "source": str(src),
        "target": str(tgt),
        "results": [{
            "algorithm":     r.algorithm,
            "visited_order": [str(n) for n in r.visited_order],
            "path":          [str(n) for n in r.path],
            "path_cost":     r.path_cost,
            "visited_count": r.visited_count,
            "compute_ms":    r.compute_ms,
        } for r in results]
    }
    with open(out, "w") as f:
        json.dump(data, f)
    print(f"Exported results → {out}")

def print_comparison(results: list[AlgoResult]) -> None:
    line = "─" * 72
    print(f"\n{line}")
    print(f"{'ALGORITHM':<28} {'VISITED':>8} {'PATH LEN':>10} {'COST':>10} {'TIME (ms)':>10}")
    print(line)
    for r in results:
        print(f"{r.algorithm:<28} {r.visited_count:>8} {len(r.path):>10} "
              f"{r.path_cost:>10.2f} {r.compute_ms:>10.3f}")
    print(line)

    if len(results) > 1:
        baseline = results[0].visited_count
        print("\nSpeedup (nodes visited vs Dijkstra baseline):")
        for r in results:
            ratio = baseline / r.visited_count if r.visited_count else float('inf')
            print(f"  {r.algorithm:<28}  {ratio:>6.2f}×")
    print()


#  Matplotlib visualisation  (grid / csv)

def visualise_matplotlib(g: Graph, results: list[AlgoResult], src, tgt,
                         out: str = 'comparison.png') -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed — skipping visualisation.")
        return

    pos = g.node_pos
    if not pos:
        print("No node positions available — skipping visualisation.")
        return

    n = len(results)
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 6))
    if n == 1:
        axes = [axes]

    all_x = [p[0] for p in pos.values()]
    all_y = [p[1] for p in pos.values()]

    COLORS = {
        'bg':      '#0d1b2e',
        'edge':    '#1a2e45',
        'visited': '#065f46',
        'path':    '#fbbf24',
        'start':   '#22d3ee',
        'end':     '#f97316',
    }

    for ax, result in zip(axes, results):
        ax.set_facecolor(COLORS['bg'])
        fig.patch.set_facecolor(COLORS['bg'])

        visited_set = set(result.visited_order)
        path_set    = set(result.path)

        # Draw edges
        for u in g.nodes:
            ux, uy = pos.get(u, (0, 0))
            for v, _ in g.neighbors(u):
                vx, vy = pos.get(v, (0, 0))
                ax.plot([ux, vx], [uy, vy], color=COLORS['edge'], lw=0.4, zorder=1)

        # Draw visited nodes
        vxl = [pos[n][0] for n in visited_set if n in pos]
        vyl = [pos[n][1] for n in visited_set if n in pos]
        ax.scatter(vxl, vyl, s=6, c=COLORS['visited'], zorder=2, linewidths=0)

        # Draw path
        if result.path:
            px = [pos[n][0] for n in result.path if n in pos]
            py = [pos[n][1] for n in result.path if n in pos]
            ax.plot(px, py, color=COLORS['path'], lw=2.5, zorder=3)
            ax.scatter(px, py, s=12, c=COLORS['path'], zorder=4, linewidths=0)

        # Start / end markers
        if src in pos:
            ax.scatter(*pos[src], s=80, c=COLORS['start'], zorder=5, linewidths=0)
        if tgt in pos:
            ax.scatter(*pos[tgt], s=80, c=COLORS['end'], zorder=5, linewidths=0)

        ax.set_xlim(min(all_x)-1, max(all_x)+1)
        ax.set_ylim(min(all_y)-1, max(all_y)+1)
        ax.set_aspect('equal')
        ax.set_xticks([]); ax.set_yticks([])

        title = (f"{result.algorithm}\n"
                 f"visited={result.visited_count}  "
                 f"path={len(result.path)}  "
                 f"{result.compute_ms:.2f}ms")
        ax.set_title(title, color='#94a3b8', fontsize=9, pad=8, fontfamily='monospace')

    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor=COLORS['bg'])
    print(f"Saved visualisation → {out}")
    plt.show()


#  Folium interactive map  (OSM mode)

# Colour scheme per algorithm  (folium uses hex strings)
_ALGO_COLORS = {
    'Dijkstra':               {'visited': '#1d4ed8', 'path': '#f59e0b'},
    'A*':                     {'visited': '#059669', 'path': '#f43f5e'},
    'Bidirectional Dijkstra': {'visited': '#7c3aed', 'path': '#06b6d4'},
}

def _latlon(graph: Graph, node) -> tuple[float, float]:
    """Return (lat, lon) from node_pos which stores (lon, lat) in OSMnx convention."""
    x, y = graph.node_pos[node]   # OSMnx: x = longitude, y = latitude
    return (y, x)


def visualise_folium(graph: Graph, results: list[AlgoResult],
                     src, tgt, place: str,
                     out: str = 'route_map.html') -> None:
    try:
        import folium
    except ImportError:
        print("\nfolium not installed — run:  pip install folium")
        print("Falling back to matplotlib visualisation.\n")
        visualise_matplotlib(graph, results, src, tgt)
        return

    # Centre map on the source node (or fallback to 0,0)
    if src in graph.node_pos:
        centre = _latlon(graph, src)
    else:
        lats = [graph.node_pos[n][1] for n in graph.node_pos]
        lons = [graph.node_pos[n][0] for n in graph.node_pos]
        centre = (sum(lats)/len(lats), sum(lons)/len(lons))

    # One tab per algorithm → use a FeatureGroup so they can be toggled
    m = folium.Map(location=centre, zoom_start=14,
                   tiles='CartoDB dark_matter')

    for result in results:
        colors = _ALGO_COLORS.get(result.algorithm,
                                  {'visited': '#94a3b8', 'path': '#f59e0b'})
        fg = folium.FeatureGroup(name=result.algorithm, show=True)

        # ── Visited nodes (small dots)
        # Limit to at most 4000 dots so the HTML stays fast
        sampled = result.visited_order
        if len(sampled) > 4000:
            step   = len(sampled) // 4000
            sampled = sampled[::step]

        for node in sampled:
            if node not in graph.node_pos:
                continue
            lat, lon = _latlon(graph, node)
            folium.CircleMarker(
                location=[lat, lon],
                radius=2,
                color=colors['visited'],
                fill=True,
                fill_color=colors['visited'],
                fill_opacity=0.5,
                weight=0,
                tooltip=f"{result.algorithm}: visited node",
            ).add_to(fg)

        # ── Path polyline 
        if result.path:
            path_coords = [
                _latlon(graph, n)
                for n in result.path
                if n in graph.node_pos
            ]
            if path_coords:
                folium.PolyLine(
                    locations=path_coords,
                    color=colors['path'],
                    weight=4,
                    opacity=0.9,
                    tooltip=(f"{result.algorithm} — "
                             f"{len(result.path)} nodes, "
                             f"cost={result.path_cost:.0f}s, "
                             f"{result.compute_ms:.1f}ms"),
                ).add_to(fg)

        fg.add_to(m)

    # ── Source & target markers 
    if src in graph.node_pos:
        lat, lon = _latlon(graph, src)
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(f"<b>START</b><br>node {src}", max_width=200),
            icon=folium.Icon(color='green', icon='play', prefix='fa'),
        ).add_to(m)

    if tgt in graph.node_pos:
        lat, lon = _latlon(graph, tgt)
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(f"<b>END</b><br>node {tgt}", max_width=200),
            icon=folium.Icon(color='red', icon='stop', prefix='fa'),
        ).add_to(m)

    # ── Stats legend (HTML panel) 
    legend_rows = "".join(
        f"<tr>"
        f"<td style='padding:4px 8px;color:{_ALGO_COLORS.get(r.algorithm,{}).get('path','#fff')};font-weight:bold'>"
        f"{r.algorithm}</td>"
        f"<td style='padding:4px 8px'>{r.visited_count:,} visited</td>"
        f"<td style='padding:4px 8px'>{len(r.path)} nodes in path</td>"
        f"<td style='padding:4px 8px'>{r.path_cost:.0f}s cost</td>"
        f"<td style='padding:4px 8px'>{r.compute_ms:.2f}ms</td>"
        f"</tr>"
        for r in results
    )

    legend_html = f"""
    <div style="
        position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%);
        z-index: 9999; background: rgba(15,20,40,0.93);
        border: 1px solid #2a3a5e; border-radius: 10px;
        padding: 14px 20px; font-family: 'Courier New', monospace;
        font-size: 12px; color: #e0e0e0; box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        max-width: 90vw; overflow-x: auto;
    ">
      <div style="font-size:14px;font-weight:bold;color:#4cc9f0;margin-bottom:10px">
        📍 {place} — Algorithm Comparison
      </div>
      <table style="border-collapse:collapse">
        <tr style="color:#8892a4;font-size:11px">
          <th style="padding:2px 8px;text-align:left">Algorithm</th>
          <th style="padding:2px 8px">Nodes visited</th>
          <th style="padding:2px 8px">Path length</th>
          <th style="padding:2px 8px">Cost (travel s)</th>
          <th style="padding:2px 8px">Compute time</th>
        </tr>
        {legend_rows}
      </table>
      <div style="margin-top:8px;color:#8892a4;font-size:10px">
        Toggle algorithms with the layer control (top-right) · Blue dots = visited · Coloured line = path
      </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Layer control to toggle each algorithm's layer
    folium.LayerControl(collapsed=False).add_to(m)

    # ── Save & open 
    m.save(out)
    abs_path = os.path.abspath(out)
    print(f"\nInteractive map saved → {out}")
    print(f"Opening in browser…  (file://{abs_path})\n")
    webbrowser.open(f"file://{abs_path}")


#  Entry point

def main() -> None:
    random.seed(42)
    args = build_parser().parse_args()

    print()
    # ── Build graph 
    if args.mode == 'grid':
        print(f"Building {args.rows}×{args.cols} random-weight grid graph…")
        g, src, tgt = build_grid_graph(args.rows, args.cols)

    elif args.mode == 'csv':
        if not args.file:
            sys.exit("--file is required for csv mode")
        print(f"Loading graph from {args.file}…")
        g, src, tgt = build_csv_graph(args.file, args.source, args.target)

    else:  # osm
        g, src, tgt = build_osm_graph(args.place, args.source, args.target)

    print(f"  Graph : {g}")
    print(f"  Source: {src}  →  Target: {tgt}\n")

    # ── Run algorithms 
    print("Running algorithms…")
    results = run_algorithms(g, src, tgt, args.algo)

    # ── Print table 
    print_comparison(results)

    # ── Visualise 
    if args.no_viz:
        return

    if args.mode == 'osm':
        # Interactive folium map — opens in browser automatically
        export_results_json(g, results, src, tgt)
        visualise_folium(g, results, src, tgt,
                         place=args.place,
                         out='route_map.html')
    else:
        # Matplotlib comparison plot for grid / csv
        visualise_matplotlib(g, results, src, tgt, out=args.out)


if __name__ == '__main__':
    main()
