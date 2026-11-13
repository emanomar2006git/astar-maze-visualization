# A* Search Algorithm Visualization

**Course:** Fundamentals of AI (CF321) – Project 1, Search Algorithms
**University:** Innovation University, Faculty of Computers and Information Technology

A Python application that visualizes the **A\* search algorithm** finding the shortest path through **randomly generated mazes**. A new, guaranteed-solvable maze can be generated at any time, at three difficulty levels, so A\* can be tested on many different environments.

---

## 1. The idea

An agent must move from a **Start** cell to a **Goal** cell in a maze. A\* finds the cheapest path while exploring as few cells as possible, guided by a heuristic. The application shows what A\* does:

| Colour | Meaning |
|---|---|
| Green | Start node |
| Red | Goal node |
| Black lines | Walls |
| Light blue | Cells explored (expanded) by A\* |
| Orange | Final solution path |

The side panel shows the search statistics: whether a path was found, the **path cost**, and the **number of nodes explored**.

## 2. Problem definition

| Element | Definition |
|---|---|
| **States** | Every empty cell `(row, col)` of the grid |
| **Initial state** | The Start cell |
| **Goal state** | The Goal cell |
| **Actions** | Move up, down, left or right into a neighbouring cell that is inside the grid and is not a wall |
| **Cost of an action** | 1 per move, so the path cost is the number of steps |

## 3. The algorithm: A\* Search

For every cell `n`, A\* computes

```
f(n) = g(n) + h(n)
```

* `g(n)`: the real cost from the Start to `n`.
* `h(n)`: the heuristic, an estimate of the remaining cost from `n` to the Goal.
* A **priority queue** (`heapq`) always expands the cell with the smallest `f(n)` first; ties are broken by the smaller `h(n)`.

### Heuristic: Manhattan distance

```
h(n) = |x1 - x2| + |y1 - y2|
```

**Why this heuristic?** The agent moves in four directions and every move costs 1, so it can never reach the Goal in fewer steps than the Manhattan distance. Walls can only make the real path longer, never shorter. The heuristic therefore **never overestimates** (it is *admissible*) and is also *consistent*, which guarantees that A\* returns an **optimal (shortest) path**. It is also very cheap to compute.

### Implementation notes (`astar.py`)

* Every call to `astar(grid, start, goal)` creates a fresh priority queue, `g` scores, parent links and closed set, so nothing from a previous search can affect a new one.
* The heuristic is always calculated from the current Goal.
* The path is rebuilt by following parent links from the Goal back to the Start.
* Unexpected input (empty grid, Start/Goal outside the grid or inside a wall, no path) never crashes; the function returns `found = False` with a message.
* A\* is completely independent of the maze generator: it only receives `grid`, `start` and `goal`.

## 4. Random maze generation (`maze_generator.py`)

The maze is a classic corridor maze, built in four steps:

1. **Carve** a random maze with a randomized depth-first carving algorithm. This only builds the walls; it is not used to find the displayed path.
2. **Open extra walls** so that several routes exist. The difficulty decides how many:

   | Difficulty | Inner walls removed |
   |---|---|
   | Easy | 30 % (many routes) |
   | Medium | 15 % |
   | Hard | 5 % (long, winding paths) |

3. **Place Start and Goal** in random rooms, always different and a minimum distance apart. Rooms are never walls.
4. **Validate** with a Breadth-First Search that the Goal is reachable. If not, the maze is regenerated automatically. A maze identical to the previous one is also regenerated.

BFS is used **only** for this solvability check. The path shown on screen is always found by A\*.

**Why this approach?** Random generation plus BFS validation gives varied mazes, is simple, guarantees solvability, and keeps the generator completely separate from A\*.

The default maze has 15 × 15 rooms (a 31 × 31 grid). The grid format shared by all modules is `grid[row][col]` with `0` = empty and `1` = wall; Start and Goal are `(row, col)` tuples.

## 5. How to run

Requirements: **Python 3.10+** and **pygame** (or pygame-ce).

```
pip install -r requirements.txt
python main.py
```

### Controls

* **Generate New Maze**: creates a new random maze and clears the previous search (explored cells, path and statistics).
* **Run A\***: runs A\* on the current maze.
* **Easy / Medium / Hard**: selects the difficulty; changing it generates a new maze.

## 6. Tests

```
python test_project.py
```

The script generates 12 different mazes (4 per difficulty) and checks that:

* Start and Goal are valid, on empty cells, and different;
* every maze is solvable and differs from the previous one;
* A\* finds a path that starts at the Start, ends at the Goal, never crosses a wall and has no jumps;
* the path cost equals the number of steps and is not below the Manhattan distance;
* `f(n) = g(n) + h(n)` along the solution path is consistent;
* explored-node statistics are correct;
* a second search, or a search after another maze, is not affected by earlier results.

It also checks the Manhattan heuristic, heuristic recalculation for a new Goal, and safe handling of unsolvable grids, invalid Start/Goal and empty grids.

**Result:** 19 / 19 checks passed (12 different mazes plus 7 extra checks).

## 7. Project structure

```
main.py             Pygame application (entry point): drawing, buttons, statistics
maze_generator.py   Random maze generation, difficulty levels, BFS solvability check
astar.py            A* search with Manhattan heuristic
test_project.py     Automated tests
requirements.txt    Dependencies
```
