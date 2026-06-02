from pathlib import Path

ROWS = 30
COLS = 60

MAP_DIR = Path(__file__).resolve().parent / "maps"


def make_grid():
    return [["#" for _ in range(COLS)] for _ in range(ROWS)]


def carve_room(grid, top, left, height, width):
    for r in range(top, top + height):
        for c in range(left, left + width):
            if 0 < r < ROWS - 1 and 0 < c < COLS - 1:
                grid[r][c] = "."


def carve_h_corridor(grid, row, c1, c2):
    for c in range(min(c1, c2), max(c1, c2) + 1):
        if 0 < row < ROWS - 1 and 0 < c < COLS - 1:
            grid[row][c] = "."


def carve_v_corridor(grid, col, r1, r2):
    for r in range(min(r1, r2), max(r1, r2) + 1):
        if 0 < r < ROWS - 1 and 0 < col < COLS - 1:
            grid[r][col] = "."


def connect_rooms(grid, start, end, first="h"):
    r1, c1 = start
    r2, c2 = end

    if first == "h":
        carve_h_corridor(grid, r1, c1, c2)
        carve_v_corridor(grid, c2, r1, r2)
    else:
        carve_v_corridor(grid, c1, r1, r2)
        carve_h_corridor(grid, r2, c1, c2)


def place_object(grid, pos, symbol):
    r, c = pos

    if grid[r][c] != ".":
        raise ValueError(f"Cannot place {symbol} at {pos}. This position is not floor.")

    grid[r][c] = symbol


def build_map(spec):
    grid = make_grid()

    for room in spec["rooms"]:
        carve_room(grid, *room)

    centers = spec["centers"]

    for start_idx, end_idx, first in spec["connections"]:
        connect_rooms(grid, centers[start_idx], centers[end_idx], first)

    for pos, symbol in spec["objects"]:
        place_object(grid, pos, symbol)

    lines = ["".join(row) for row in grid]

    if len(lines) != ROWS:
        raise ValueError("Map row count is wrong.")

    for line in lines:
        if len(line) != COLS:
            raise ValueError("Map column count is wrong.")

    return lines


def save_map(filename, lines):
    MAP_DIR.mkdir(exist_ok=True)
    path = MAP_DIR / filename

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"{filename} created successfully.")


def main():
    map_specs = [
        {
            "rooms": [
                (1, 1, 6, 14),
                (2, 22, 7, 14),
                (12, 3, 7, 16),
                (12, 25, 6, 14),
                (21, 39, 7, 18),
            ],
            "centers": [
                (4, 8),
                (5, 29),
                (15, 11),
                (15, 32),
                (24, 48),
            ],
            "connections": [
                (0, 1, "h"),
                (1, 3, "v"),
                (3, 2, "h"),
                (3, 4, "v"),
            ],
            "objects": [
                ((4, 3), "P"),
                ((24, 54), "E"),
                ((3, 12), "I"),
                ((15, 6), "I"),
                ((14, 35), "I"),
                ((23, 44), "I"),
                ((5, 26), "W"),
                ((16, 15), "W"),
                ((23, 50), "W"),
                ((15, 29), "F"),
                ((25, 42), "F"),
            ],
        },
        {
            "rooms": [
                (1, 40, 7, 17),
                (4, 3, 6, 15),
                (12, 20, 8, 16),
                (20, 2, 7, 14),
                (21, 39, 6, 17),
                (10, 44, 7, 12),
            ],
            "centers": [
                (4, 48),
                (7, 10),
                (16, 28),
                (23, 9),
                (24, 47),
                (13, 50),
            ],
            "connections": [
                (0, 5, "v"),
                (5, 2, "h"),
                (2, 1, "h"),
                (1, 3, "v"),
                (2, 4, "v"),
            ],
            "objects": [
                ((4, 52), "P"),
                ((23, 6), "E"),
                ((6, 7), "I"),
                ((15, 23), "I"),
                ((24, 51), "I"),
                ((13, 53), "I"),
                ((7, 14), "W"),
                ((16, 32), "W"),
                ((22, 43), "W"),
                ((12, 47), "F"),
                ((5, 43), "F"),
            ],
        },
        {
            "rooms": [
                (1, 2, 7, 18),
                (1, 36, 6, 20),
                (10, 8, 7, 12),
                (11, 29, 8, 17),
                (21, 4, 7, 17),
                (21, 38, 7, 18),
            ],
            "centers": [
                (4, 11),
                (4, 46),
                (13, 14),
                (15, 37),
                (24, 12),
                (24, 47),
            ],
            "connections": [
                (4, 2, "v"),
                (2, 0, "h"),
                (0, 1, "h"),
                (1, 3, "v"),
                (3, 5, "v"),
                (2, 3, "h"),
            ],
            "objects": [
                ((24, 7), "P"),
                ((3, 52), "E"),
                ((3, 6), "I"),
                ((13, 10), "I"),
                ((17, 42), "I"),
                ((25, 16), "I"),
                ((24, 42), "I"),
                ((4, 16), "W"),
                ((14, 34), "W"),
                ((24, 50), "W"),
                ((5, 40), "F"),
                ((23, 10), "F"),
            ],
        },
        {
            "rooms": [
                (2, 2, 6, 15),
                (2, 42, 6, 15),
                (10, 20, 10, 20),
                (22, 3, 6, 16),
                (22, 41, 6, 16),
            ],
            "centers": [
                (5, 9),
                (5, 49),
                (15, 30),
                (25, 11),
                (25, 49),
            ],
            "connections": [
                (0, 2, "h"),
                (1, 2, "h"),
                (2, 3, "v"),
                (2, 4, "v"),
                (3, 4, "h"),
            ],
            "objects": [
                ((4, 5), "P"),
                ((25, 53), "E"),
                ((5, 13), "I"),
                ((4, 45), "I"),
                ((12, 24), "I"),
                ((18, 36), "I"),
                ((24, 7), "I"),
                ((5, 52), "W"),
                ((14, 32), "W"),
                ((25, 45), "W"),
                ((16, 24), "F"),
                ((23, 14), "F"),
            ],
        },
        {
            "rooms": [
                (1, 1, 5, 13),
                (1, 23, 6, 14),
                (2, 45, 5, 12),
                (10, 5, 8, 14),
                (11, 32, 6, 15),
                (21, 10, 7, 15),
                (22, 39, 6, 17),
            ],
            "centers": [
                (3, 7),
                (4, 30),
                (4, 51),
                (14, 12),
                (14, 39),
                (24, 17),
                (25, 47),
            ],
            "connections": [
                (0, 1, "h"),
                (1, 2, "h"),
                (1, 4, "v"),
                (4, 3, "h"),
                (3, 5, "v"),
                (5, 6, "h"),
            ],
            "objects": [
                ((3, 3), "P"),
                ((24, 53), "E"),
                ((3, 11), "I"),
                ((5, 26), "I"),
                ((13, 9), "I"),
                ((15, 43), "I"),
                ((25, 14), "I"),
                ((4, 33), "W"),
                ((14, 16), "W"),
                ((24, 20), "W"),
                ((23, 44), "W"),
                ((4, 48), "F"),
                ((13, 35), "F"),
            ],
        },
    ]

    for i, spec in enumerate(map_specs, start=1):
        lines = build_map(spec)
        save_map(f"map{i}.txt", lines)


if __name__ == "__main__":
    main()