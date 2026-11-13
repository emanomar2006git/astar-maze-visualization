"""astar.py -- Task 2: A* Search (independent from maze generation)."""

import heapq

EMPTY = 0
WALL = 1


def manhattan(a, b):
    """h(n) = |x1 - x2| + |y1 - y2| for cells a and b given as (row, col)."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid, start, goal):
    """
    Search grid (0 = empty, 1 = wall) from start to goal with A*.
    Returns a dict:
      found          True / False
      path           list of (row, col) from start to goal ([] if not found)
      cost           number of steps in the path (each step costs 1)
      explored       cells expanded by A*, in the order they were expanded
      nodes_explored len(explored)
      message        short explanation (useful when something goes wrong)
    Every call builds its own queue, g-scores and parents, so nothing
    from a previous search can leak into this one.
    """
    result = {"found": False, "path": [], "cost": 0,
              "explored": [], "nodes_explored": 0, "message": ""}

    # ---- safety checks --------------------------------------------------
    if not grid or not grid[0]:
        result["message"] = "empty grid"
        return result
    rows, cols = len(grid), len(grid[0])
    for name, cell in (("start", start), ("goal", goal)):
        r, c = cell
        if not (0 <= r < rows and 0 <= c < cols):
            result["message"] = f"{name} is outside the grid"
            return result
        if grid[r][c] == WALL:
            result["message"] = f"{name} is inside a wall"
            return result

    # ---- fresh search data (reset on every call) ------------------------
    h_start = manhattan(start, goal)               # heuristic uses THIS goal
    open_heap = [(h_start, h_start, start)]        # entries: (f, h, cell)
    g_score = {start: 0}
    came_from = {}
    closed = set()

    # ---- main loop ------------------------------------------------------
    while open_heap:
        f, h, current = heapq.heappop(open_heap)
        if current in closed:
            continue                               # outdated queue entry
        closed.add(current)
        result["explored"].append(current)

        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            result.update(found=True, path=path, cost=g_score[goal],
                          nodes_explored=len(result["explored"]),
                          message="path found")
            return result

        r, c = current
        for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            nr, nc = nxt
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            if grid[nr][nc] == WALL or nxt in closed:
                continue
            new_g = g_score[current] + 1
            if new_g < g_score.get(nxt, float("inf")):
                g_score[nxt] = new_g
                came_from[nxt] = current
                h_n = manhattan(nxt, goal)
                heapq.heappush(open_heap, (new_g + h_n, h_n, nxt))

    result["nodes_explored"] = len(result["explored"])
    result["message"] = "no path exists"
    return result