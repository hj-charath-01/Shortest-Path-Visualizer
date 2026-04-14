"""
main.py
=======
Entry point for the Route Planner project.

Usage examples
--------------
# Benchmark on a random grid
python main.py --mode grid --rows 50 --cols 80

# Load a real city from OpenStreetMap
python main.py --mode osm --place "Singapore" --source <node_id> --target <node_id>

# Load from an edge-list CSV
python main.py --mode csv --file edges.csv --source A --target Z
"""

from __future__ import annotations
import argparse
import random
import sys
import textwrap

from graph import Graph
from algorithms import dijkstra, a_star, bidirectional_dijkstra, AlgoResult


# ─────────────────────────────────────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Route Planner — Advanced Graph Algorithms Project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python main.py --mode grid --rows 40 --cols 60
              python main.py --mode csv  --file roads.csv --source NYC --target LA
              python main.py --mode osm  --place "Berlin, Germany"
        """)
    )
    p.add_argument('--mode',   choices=['grid','csv','osm'], default='grid')
    p.add_argument('--rows',   type=int, default=30,  help='Grid rows  (grid mode)')
    p.add_argument('--cols',   type=int, default=40,  help='Grid cols  (grid mode)')
    p.add_argument('--file',   type=str, default='',  help='Edge CSV   (csv mode)')
    p.add_argument('--place',  type=str, default='Singapore', help='City name (osm mode)')
    p.add_argument('--source', type=str, default='',  help='Source node id')
    p.add_argument('--target', type=str, default='',  help='Target node id')
    p.add_argument('--algo',   type=str, default='all',
                   choices=['dijkstra','astar','bidir','all'],
                   help='Algorithm to run (default: all three)')
    p.add_argument('--no-viz', action='store_true', help='Skip matplotlib visualisation')
    return p


# ─────────────────────────────────────────────────────────────────────────────
#  Graph builders
# ─────────────────────────────────────────────────────────────────────────────

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
    print(f"Downloading road network for '{place}' from OpenStreetMap…")
    g = Graph.from_osmnx(place)
    nodes = g.nodes
    src = int(source) if source else random.choice(nodes)
    tgt = int(target) if target else random.choice(nodes)
    return g, src, tgt


# ─────────────────────────────────────────────────────────────────────────────
#  Run & report
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
#  Visualisation (optional — requires matplotlib)
# ─────────────────────────────────────────────────────────────────────────────

def visualise(g: Graph, results: list[AlgoResult], src, tgt) -> None:
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        print("matplotlib not installed — skipping visualisation.")
        return

    n = len(results)
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 6))
    if n == 1:
        axes = [axes]

    pos = g.node_pos
    if not pos:
        print("No node positions available — skipping visualisation.")
        return

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
                ax.plot([ux, vx], [uy, vy], color=COLORS['edge'],
                        lw=0.4, zorder=1)

        # Draw visited nodes
        vx_list = [pos[n][0] for n in visited_set if n in pos]
        vy_list = [pos[n][1] for n in visited_set if n in pos]
        ax.scatter(vx_list, vy_list, s=6, c=COLORS['visited'],
                   zorder=2, linewidths=0)

        # Draw path
        if result.path:
            px = [pos[n][0] for n in result.path if n in pos]
            py = [pos[n][1] for n in result.path if n in pos]
            ax.plot(px, py, color=COLORS['path'], lw=2.5, zorder=3)
            ax.scatter(px, py, s=12, c=COLORS['path'], zorder=4, linewidths=0)

        # Start / end markers
        if src in pos:
            ax.scatter(*pos[src], s=80, c=COLORS['start'],
                       zorder=5, linewidths=0)
        if tgt in pos:
            ax.scatter(*pos[tgt], s=80, c=COLORS['end'],
                       zorder=5, linewidths=0)

        ax.set_xlim(min(all_x)-1, max(all_x)+1)
        ax.set_ylim(min(all_y)-1, max(all_y)+1)
        ax.set_aspect('equal')
        ax.set_xticks([]); ax.set_yticks([])

        title = (f"{result.algorithm}\n"
                 f"visited={result.visited_count}  "
                 f"path={len(result.path)}  "
                 f"{result.compute_ms:.2f}ms")
        ax.set_title(title, color='#94a3b8', fontsize=9, pad=8,
                     fontfamily='monospace')

    plt.tight_layout()
    plt.savefig('comparison.png', dpi=150, bbox_inches='tight',
                facecolor=COLORS['bg'])
    print("Saved visualisation → comparison.png")
    plt.show()


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    random.seed(42)
    args = build_parser().parse_args()

    # Build graph
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

    print(f"Graph: {g}")
    print(f"Source: {src}  →  Target: {tgt}\n")

    # Run algorithms
    results = run_algorithms(g, src, tgt, args.algo)

    # Report
    print_comparison(results)

    # Visualise
    if not args.no_viz:
        visualise(g, results, src, tgt)


if __name__ == '__main__':
    main()
