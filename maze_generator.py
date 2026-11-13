"""
maze_generator.py  --  Task 1: Random Maze Generation & Validation

This module only CREATES the environment. It knows nothing about A*.
The A* module receives `maze.grid`, `maze.start`, `maze.goal` and searches it.

Maze style: a classic corridor maze (like a printed puzzle maze).
  * The grid is (2*n + 1) x (2*m + 1) for a maze of n x m "rooms".
  * Rooms sit on odd rows / odd columns. The cells between two rooms are
    either an open passage or a wall, and the cells on even/even positions
    are always wall pillars.

Approach: randomized maze carving + BFS solvability validation.
  1. Carve a random maze with a randomized depth-first "recursive backtracker".
     (This only builds the walls; it is NOT the search used to find the path.)
  2. Remove some extra walls so there are several possible routes.
     Difficulty controls how many: Easy = many openings (low wall density),
     Medium = some, Hard = very few (dense, winding maze).
  3. Pick random Start and Goal rooms (different, a minimum distance apart).
     Rooms are never walls, so Start/Goal can never be inside a wall.
  4. Check with BFS that Goal is reachable from Start. If not, regenerate.
  5. If the layout equals the previous maze, regenerate.

BFS is used ONLY in is_solvable(). It never searches for the displayed path.

Shared data format (used by every module):
  grid  : list of rows, grid[row][col], 0 = EMPTY, 1 = WALL
  start : (row, col)
  goal  : (row, col)
"""

import random
from collections import deque
from dataclasses import dataclass
from typing import List, Optional, Tuple

EMPTY = 0
WALL = 1

Cell = Tuple[int, int]
Grid = List[List[int]]

# Fraction of the remaining inner walls that are knocked down after carving.
# More openings = fewer walls = easier.
DIFFICULTY_OPENINGS = {"easy": 0.30, "medium": 0.15, "hard": 0.05}
DIFFICULTIES = tuple(DIFFICULTY_OPENINGS)

DEFAULT_ROWS = 15     # rooms per column (grid will have 2*15+1 = 31 rows)
DEFAULT_COLS = 15
MIN_SIZE = 3
MAX_SIZE = 30
MAX_ATTEMPTS = 200    # regenerate tries before the guaranteed-path fallback


@dataclass
class Maze:
    grid: Grid
    start: Cell
    goal: Cell
    difficulty: str

    @property
    def rows(self) -> int:          # grid rows
        return len(self.grid)

    @property
    def cols(self) -> int:          # grid columns
        return len(self.grid[0])

    @property
    def cell_rows(self) -> int:     # number of rooms vertically
        return (self.rows - 1) // 2

    @property
    def cell_cols(self) -> int:     # number of rooms horizontally
        return (self.cols - 1) // 2


# ----------------------------------------------------------------------------
# Solvability validation (BFS -- allowed ONLY here)
# ----------------------------------------------------------------------------
def is_solvable(grid: Grid, start: Cell, goal: Cell) -> bool:
    """True if a 4-directional path of empty cells links start to goal."""
    rows, cols = len(grid), len(grid[0])
    for r, c in (start, goal):
        if not (0 <= r < rows and 0 <= c < cols) or grid[r][c] == WALL:
            return False

    seen = {start}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        if (r, c) == goal:
            return True
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if (0 <= nr < rows and 0 <= nc < cols
                    and grid[nr][nc] == EMPTY and (nr, nc) not in seen):
                seen.add((nr, nc))
                queue.append((nr, nc))
    return False


def validate_maze(maze: Maze) -> List[str]:
    """Return a list of problems found. An empty list means the maze is valid."""
    errors = []
    grid = maze.grid
    if not grid or not grid[0]:
        return ["grid is empty"]
    cols = len(grid[0])
    if any(len(row) != cols for row in grid):
        errors.append("grid rows have different lengths")
    if any(v not in (EMPTY, WALL) for row in grid for v in row):
        errors.append("grid contains values other than 0 and 1")
    if errors:
        return errors

    for name, (r, c) in (("start", maze.start), ("goal", maze.goal)):
        if not (0 <= r < len(grid) and 0 <= c < cols):
            errors.append(f"{name} {(r, c)} is outside the grid")
        elif grid[r][c] == WALL:
            errors.append(f"{name} {(r, c)} is inside a wall")
    if maze.start == maze.goal:
        errors.append("start and goal are the same cell")
    if not errors and not is_solvable(grid, maze.start, maze.goal):
        errors.append("maze has no path from start to goal")
    return errors


# ----------------------------------------------------------------------------
# Generation
# ----------------------------------------------------------------------------
def _carve_rooms(n_rows: int, n_cols: int, rng: random.Random) -> Grid:
    """Randomized depth-first carving: every room ends up connected to all others."""
    grid = [[WALL] * (2 * n_cols + 1) for _ in range(2 * n_rows + 1)]
    first = (rng.randrange(n_rows), rng.randrange(n_cols))
    grid[2 * first[0] + 1][2 * first[1] + 1] = EMPTY
    visited = {first}
    stack = [first]
    while stack:
        r, c = stack[-1]
        options = [(r + dr, c + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                   if 0 <= r + dr < n_rows and 0 <= c + dc < n_cols
                   and (r + dr, c + dc) not in visited]
        if not options:
            stack.pop()
            continue
        nr, nc = rng.choice(options)
        grid[r + nr + 1][c + nc + 1] = EMPTY     # open the wall between the rooms
        grid[2 * nr + 1][2 * nc + 1] = EMPTY     # open the new room
        visited.add((nr, nc))
        stack.append((nr, nc))
    return grid


def _open_extra_walls(grid: Grid, fraction: float, rng: random.Random) -> None:
    """Knock down a fraction of the remaining inner walls (creates alternate routes)."""
    rows, cols = len(grid), len(grid[0])
    removable = [(r, c) for r in range(1, rows - 1) for c in range(1, cols - 1)
                 if grid[r][c] == WALL and (r + c) % 2 == 1]   # wall between two rooms
    for r, c in rng.sample(removable, round(fraction * len(removable))):
        grid[r][c] = EMPTY


def place_start_goal(grid: Grid, rng: random.Random,
                     min_distance: int) -> Tuple[Cell, Cell]:
    """Random, different Start and Goal rooms at least min_distance apart (Manhattan)."""
    rooms = [(r, c) for r in range(1, len(grid), 2) for c in range(1, len(grid[0]), 2)]
    start = rng.choice(rooms)
    far = [rm for rm in rooms
           if abs(rm[0] - start[0]) + abs(rm[1] - start[1]) >= min_distance]
    if not far:  # only possible on tiny mazes
        far = [rm for rm in rooms if rm != start]
    return start, rng.choice(far)


def _carve_path(grid: Grid, start: Cell, goal: Cell, rng: random.Random) -> None:
    """Fallback: clear a random monotone path so the maze is surely solvable."""
    r, c = start
    grid[r][c] = EMPTY
    while (r, c) != goal:
        can_row, can_col = r != goal[0], c != goal[1]
        if can_row and (not can_col or rng.random() < 0.5):
            r += 1 if goal[0] > r else -1
        else:
            c += 1 if goal[1] > c else -1
        grid[r][c] = EMPTY


def _same_layout(a: Maze, b: Optional[Maze]) -> bool:
    return (b is not None and a.start == b.start and a.goal == b.goal
            and a.grid == b.grid)


def generate_maze(rows: int = DEFAULT_ROWS, cols: int = DEFAULT_COLS,
                  difficulty: str = "medium", previous: Optional[Maze] = None,
                  rng: Optional[random.Random] = None) -> Maze:
    """
    Build a new random, guaranteed-solvable maze.

    rows, cols : number of ROOMS (the grid is 2*rows+1 by 2*cols+1 cells).
    previous   : last maze shown; the new one will differ from it.
    rng        : pass random.Random(seed) for reproducible results (tests).
    """
    difficulty = str(difficulty).lower()
    if difficulty not in DIFFICULTY_OPENINGS:
        raise ValueError(f"difficulty must be one of {DIFFICULTIES}, got {difficulty!r}")
    if not (MIN_SIZE <= rows <= MAX_SIZE and MIN_SIZE <= cols <= MAX_SIZE):
        raise ValueError(f"rows and cols must be between {MIN_SIZE} and {MAX_SIZE}")

    rng = rng or random.Random()
    min_distance = max(4, (2 * rows + 2 * cols) // 3)  # avoid trivially short paths

    for _ in range(MAX_ATTEMPTS):
        grid = _carve_rooms(rows, cols, rng)
        _open_extra_walls(grid, DIFFICULTY_OPENINGS[difficulty], rng)
        start, goal = place_start_goal(grid, rng, min_distance)
        if not is_solvable(grid, start, goal):
            continue  # unsolvable -> regenerate automatically
        maze = Maze(grid, start, goal, difficulty)
        if _same_layout(maze, previous):
            continue
        return maze

    # Extremely unlikely: force a solvable layout instead of looping forever.
    while True:
        grid = _carve_rooms(rows, cols, rng)
        _open_extra_walls(grid, DIFFICULTY_OPENINGS[difficulty], rng)
        start, goal = place_start_goal(grid, rng, min_distance)
        _carve_path(grid, start, goal, rng)
        maze = Maze(grid, start, goal, difficulty)
        if not _same_layout(maze, previous):
            return maze


def maze_to_text(maze: Maze) -> str:
    """ASCII view for debugging: S start, G goal, # wall, . empty."""
    lines = []
    for r, row in enumerate(maze.grid):
        line = ""
        for c, v in enumerate(row):
            line += ("S" if (r, c) == maze.start else
                     "G" if (r, c) == maze.goal else
                     "#" if v == WALL else " ")
        lines.append(line)
    return "\n".join(lines)


if __name__ == "__main__":
    m = None
    for level in DIFFICULTIES:
        m = generate_maze(8, 12, level, previous=m)
        print(f"--- {level} | start={m.start} goal={m.goal} | "
              f"valid={not validate_maze(m)}")
        print(maze_to_text(m))
