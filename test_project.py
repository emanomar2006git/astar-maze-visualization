"""
test_project.py -- Final testing for the A* Search Visualization project.

Run with:   python test_project.py

Generates 12 different mazes (4 per difficulty) and checks every requirement.
Exit code is 0 when everything passes, 1 otherwise.
"""

import random
import sys

from maze_generator import (generate_maze, validate_maze, is_solvable,
                            DIFFICULTIES, EMPTY, WALL)
from astar import astar, manhattan

MAZES_PER_LEVEL = 4
ROOMS = 15          # same size as the application (grid 31 x 31)


def check_maze(maze, previous):
    """Maze-level checks. Returns a list of failure messages."""
    bad = []
    rows, cols = len(maze.grid), len(maze.grid[0])
    if validate_maze(maze):
        bad += validate_maze(maze)
    if maze.start == maze.goal:
        bad.append("start equals goal")
    for name, (r, c) in (("start", maze.start), ("goal", maze.goal)):
        if not (0 <= r < rows and 0 <= c < cols) or maze.grid[r][c] != EMPTY:
            bad.append(f"{name} is not on an empty cell")
    if not is_solvable(maze.grid, maze.start, maze.goal):
        bad.append("maze is not solvable")
    if previous is not None and maze.grid == previous.grid \
            and maze.start == previous.start and maze.goal == previous.goal:
        bad.append("identical to the previous maze")
    return bad


def check_result(maze, res):
    """A* result checks. Returns a list of failure messages."""
    bad = []
    grid, start, goal = maze.grid, maze.start, maze.goal
    if not res["found"]:
        return ["A* did not find a path"]
    path = res["path"]

    if path[0] != start or path[-1] != goal:
        bad.append("path does not go from start to goal")
    if any(grid[r][c] == WALL for r, c in path):
        bad.append("path crosses a wall")
    if any(abs(a[0] - b[0]) + abs(a[1] - b[1]) != 1 for a, b in zip(path, path[1:])):
        bad.append("path has a jump (cells not adjacent)")
    if len(set(path)) != len(path):
        bad.append("path visits a cell twice")

    if res["cost"] != len(path) - 1:
        bad.append(f"cost {res['cost']} != steps {len(path) - 1}")
    if res["cost"] < manhattan(start, goal):
        bad.append("cost is lower than the Manhattan distance (impossible)")

    # f(n) = g(n) + h(n) along the solution path: g = steps so far.
    f_values = [g + manhattan(cell, goal) for g, cell in enumerate(path)]
    if f_values[-1] != res["cost"]:
        bad.append("f(goal) != path cost")
    if any(b < a for a, b in zip(f_values, f_values[1:])):
        bad.append("f(n) decreases along the path (heuristic not consistent)")

    explored = res["explored"]
    if res["nodes_explored"] != len(explored):
        bad.append("nodes_explored != len(explored)")
    if len(set(explored)) != len(explored):
        bad.append("a cell was explored twice")
    if any(grid[r][c] == WALL for r, c in explored):
        bad.append("A* explored a wall")
    if not set(path) <= set(explored):
        bad.append("path contains cells that were never explored")
    return bad


def main():
    rng = random.Random(2026)        # fixed seed -> same report every run
    failures = 0
    previous = None
    prev_result = None
    layouts = set()

    print(f"{'#':>2} {'level':<7}{'start':<10}{'goal':<10}{'cost':>5}{'explored':>10}  result")
    print("-" * 56)

    n = 0
    for level in DIFFICULTIES:
        for _ in range(MAZES_PER_LEVEL):
            n += 1
            maze = generate_maze(ROOMS, ROOMS, level, previous=previous, rng=rng)
            problems = check_maze(maze, previous)

            res = astar(maze.grid, maze.start, maze.goal)
            problems += check_result(maze, res)

            # Previous search data must not affect this maze:
            # a second, independent run must give exactly the same answer,
            # and results must not share mutable data between calls.
            again = astar(maze.grid, maze.start, maze.goal)
            if again != res:
                problems.append("running A* twice gives different results")
            if again["explored"] is res["explored"] or again["path"] is res["path"]:
                problems.append("search results share data between calls")
            if prev_result is not None and prev_result["explored"] is res["explored"]:
                problems.append("old search data leaked into new search")

            layout = (str(maze.grid), maze.start, maze.goal)
            if layout in layouts:
                problems.append("layout already seen earlier in this test")
            layouts.add(layout)

            status = "PASS" if not problems else "FAIL: " + "; ".join(problems)
            failures += bool(problems)
            print(f"{n:>2} {level:<7}{str(maze.start):<10}{str(maze.goal):<10}"
                  f"{res['cost']:>5}{res['nodes_explored']:>10}  {status}")
            previous, prev_result = maze, res

    print("-" * 56)

    # --- extra checks -------------------------------------------------------
    extra = []

    # Heuristic is recalculated for a new goal on the same grid.
    grid = [[0] * 5 for _ in range(5)]
    a = astar(grid, (0, 0), (0, 4))
    b = astar(grid, (0, 0), (4, 0))
    extra.append(("Manhattan h(n) = |x1-x2| + |y1-y2|",
                  manhattan((0, 0), (2, 3)) == 5 and manhattan((4, 4), (4, 4)) == 0))
    extra.append(("new goal -> new correct path and cost",
                  a["cost"] == 4 and b["cost"] == 4
                  and a["path"][-1] == (0, 4) and b["path"][-1] == (4, 0)))

    # Unexpected cases are handled safely (no crash, found = False).
    blocked = [[0, 1, 0], [0, 1, 0], [0, 1, 0]]
    extra.append(("unsolvable grid handled safely",
                  astar(blocked, (0, 0), (0, 2))["found"] is False))
    extra.append(("start inside a wall handled safely",
                  astar(blocked, (0, 1), (0, 2))["found"] is False))
    extra.append(("goal outside the grid handled safely",
                  astar(blocked, (0, 0), (9, 9))["found"] is False))
    extra.append(("empty grid handled safely",
                  astar([], (0, 0), (0, 0))["found"] is False))
    extra.append(("start == goal gives cost 0",
                  astar(grid, (2, 2), (2, 2))["cost"] == 0))

    for name, ok in extra:
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        failures += (not ok)

    total = n + len(extra)
    print("-" * 56)
    print(f"{total - failures}/{total} checks passed, {n} different mazes tested")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
