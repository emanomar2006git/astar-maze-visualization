"""main.py -- A* Search Visualization (entry point)."""

import pygame

from maze_generator import (generate_maze, DEFAULT_ROWS, DEFAULT_COLS,
                            DIFFICULTIES, WALL)
from astar import astar

# The maze is drawn like a printed maze: thin wall lines, wide corridors.
# Grid rows/columns with an EVEN index are wall lines (thin),
# rows/columns with an ODD index are corridors (wide).
WALL_T = 4         # thickness of a wall line in pixels
PATH_W = 34        # width of a corridor in pixels
MARGIN = 12        # empty space around the maze
PANEL_W = 260      # width of the side panel
ANIM_FRAMES = 90   # about how many frames the exploring animation lasts (60 fps)

WHITE = (255, 255, 255)
WALL_COLOR = (20, 20, 20)
START_COLOR = (46, 160, 67)       # green
GOAL_COLOR = (219, 68, 55)        # red
EXPLORED_COLOR = (190, 220, 250)  # light blue: cells A* expanded
PATH_COLOR = (255, 200, 60)       # orange: final solution path
PANEL_BG = (240, 242, 245)
TEXT_COLOR = (30, 30, 30)
BUTTON_COLOR = (255, 255, 255)
BUTTON_HOVER = (225, 235, 250)
BUTTON_ACTIVE = (70, 120, 220)    # selected difficulty
BUTTON_BORDER = (170, 175, 185)


def offset(i):
    """Pixel position where grid row/column i starts."""
    return ((i + 1) // 2) * WALL_T + (i // 2) * PATH_W


def span(i):
    """Pixel thickness of grid row/column i."""
    return WALL_T if i % 2 == 0 else PATH_W


def cell_box(r, c):
    """(x, y, width, height) in pixels of grid cell (r, c)."""
    return (MARGIN + offset(c), MARGIN + offset(r), span(c), span(r))


def is_lonely_pillar(grid, r, c):
    """True for a wall corner (even row, even column) touching no other wall."""
    if r % 2 == 1 or c % 2 == 1:
        return False
    for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
        if 0 <= nr < len(grid) and 0 <= nc < len(grid[0]) and grid[nr][nc] == WALL:
            return False
    return True


def draw_maze(screen, maze, result, n_explored, n_path):
    """
    Draw corridors, A* explored cells, final path, walls, Start and Goal.
    Only the first n_explored explored cells and the first n_path path cells
    are drawn, which is what makes the search animate.
    """
    board = (MARGIN, MARGIN, offset(maze.cols), offset(maze.rows))
    pygame.draw.rect(screen, WHITE, board)

    if result is not None:
        for r, c in result["explored"][:n_explored]:
            pygame.draw.rect(screen, EXPLORED_COLOR, cell_box(r, c))
        for r, c in result["path"][:n_path]:
            pygame.draw.rect(screen, PATH_COLOR, cell_box(r, c))

    for r in range(maze.rows):
        for c in range(maze.cols):
            if maze.grid[r][c] == WALL and not is_lonely_pillar(maze.grid, r, c):
                pygame.draw.rect(screen, WALL_COLOR, cell_box(r, c))

    pygame.draw.rect(screen, START_COLOR, cell_box(*maze.start))
    pygame.draw.rect(screen, GOAL_COLOR, cell_box(*maze.goal))


class Button:
    """A simple clickable rectangle with a text label."""

    def __init__(self, label, x, y, w, h):
        self.label = label
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, screen, font, mouse_pos, active=False):
        if active:
            fill, text_color = BUTTON_ACTIVE, WHITE
        elif self.rect.collidepoint(mouse_pos):
            fill, text_color = BUTTON_HOVER, TEXT_COLOR
        else:
            fill, text_color = BUTTON_COLOR, TEXT_COLOR
        pygame.draw.rect(screen, fill, self.rect, border_radius=6)
        pygame.draw.rect(screen, BUTTON_BORDER, self.rect, 1, border_radius=6)
        text = font.render(self.label, True, text_color)
        screen.blit(text, text.get_rect(center=self.rect.center))

    def clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.rect.collidepoint(event.pos))


def build_buttons(x):
    """Create all buttons of the side panel. x = left edge of the panel."""
    width = PANEL_W - 30
    y = MARGIN + 44
    generate = Button("Generate New Maze", x, y, width, 40)
    run = Button("Run A*", x, y + 50, width, 40)
    gap = 8
    small = (width - 2 * gap) // 3
    top = y + 128
    levels = {name: Button(name.capitalize(), x + i * (small + gap), top, small, 34)
              for i, name in enumerate(DIFFICULTIES)}
    return generate, run, levels


def draw_panel(screen, font, x, maze, result, finished):
    """Side panel texts: title, difficulty label and search statistics."""
    def put(text, y):
        screen.blit(font.render(text, True, TEXT_COLOR), (x, y))

    put("A* Search Visualization", MARGIN + 6)
    put("Difficulty:", MARGIN + 44 + 106)

    lines = [f"Start: {maze.start}", f"Goal: {maze.goal}", "", "Statistics"]
    if result is None:
        lines.append("Not searched yet")
    elif not finished:
        lines.append("Searching...")
    elif result["found"]:
        lines += ["Path found",
                  f"Path cost: {result['cost']}",
                  f"Nodes explored: {result['nodes_explored']}"]
    else:
        lines += [f"No path: {result['message']}",
                  f"Nodes explored: {result['nodes_explored']}"]

    y = MARGIN + 44 + 128 + 34 + 24
    for text in lines:
        put(text, y)
        y += 26


def main():
    pygame.init()
    difficulty = "medium"
    maze = generate_maze(DEFAULT_ROWS, DEFAULT_COLS, difficulty)
    result = None          # no search has been run on this maze yet
    n_explored = 0         # how many explored cells are visible so far
    n_path = 0             # how many path cells are visible so far
    width = 2 * MARGIN + offset(maze.cols) + PANEL_W
    height = 2 * MARGIN + offset(maze.rows)
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("A* Search Visualization")
    font = pygame.font.Font(None, 26)
    clock = pygame.time.Clock()
    panel_x = 2 * MARGIN + offset(maze.cols) + 10
    generate_btn, run_btn, level_btns = build_buttons(panel_x)

    def new_maze():
        """Generate a fresh maze and clear every trace of the previous search."""
        nonlocal maze, result, n_explored, n_path
        maze = generate_maze(maze.cell_rows, maze.cell_cols, difficulty, previous=maze)
        result, n_explored, n_path = None, 0, 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif generate_btn.clicked(event):
                new_maze()
            elif run_btn.clicked(event):
                # run A* now, then reveal its work step by step
                result = astar(maze.grid, maze.start, maze.goal)
                n_explored, n_path = 0, 0
            else:
                for name, button in level_btns.items():
                    if button.clicked(event) and name != difficulty:
                        difficulty = name      # changing difficulty = new maze
                        new_maze()

        # Animation: first reveal explored cells, then the final path.
        finished = True
        if result is not None:
            total_e, total_p = len(result["explored"]), len(result["path"])
            if n_explored < total_e:
                n_explored = min(total_e, n_explored + max(1, -(-total_e // ANIM_FRAMES)))
            elif n_path < total_p:
                n_path = min(total_p, n_path + max(1, -(-total_p // (ANIM_FRAMES // 3))))
            finished = n_explored >= total_e and n_path >= total_p

        screen.fill(PANEL_BG)
        draw_maze(screen, maze, result, n_explored, n_path)
        draw_panel(screen, font, panel_x, maze, result, finished)
        mouse = pygame.mouse.get_pos()
        generate_btn.draw(screen, font, mouse)
        run_btn.draw(screen, font, mouse)
        for name, button in level_btns.items():
            button.draw(screen, font, mouse, active=(name == difficulty))
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()