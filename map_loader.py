# map_loader.py

from pathlib import Path
import random

ROWS = 30
COLS = 60

WALL = -1
FLOOR = 0
EXIT = 2

BASE_DIR = Path(__file__).resolve().parent
MAP_DIR = BASE_DIR / "maps"

VALID_CHARS = {"#", ".", "P", "E", "I", "W", "F"}

MAP_FILES = [
    "map1.txt",
    "map2.txt",
    "map3.txt",
    "map4.txt",
    "map5.txt",
]


def load_map(filename):
    path = MAP_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Map file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]

    validate_raw_map(lines, filename)

    grid = []
    player_pos = None
    exit_pos = None
    items = {}
    enemies = []

    enemy_id = 1

    for r, line in enumerate(lines):
        row = []

        for c, ch in enumerate(line):
            if ch == "#":
                row.append(WALL)

            elif ch == ".":
                row.append(FLOOR)

            elif ch == "P":
                if player_pos is not None:
                    raise ValueError(f"{filename}: Player start P appears more than once.")
                player_pos = (r, c)
                row.append(FLOOR)

            elif ch == "E":
                if exit_pos is not None:
                    raise ValueError(f"{filename}: Exit E appears more than once.")
                exit_pos = (r, c)
                row.append(EXIT)

            elif ch == "I":
                items[(r, c)] = random.choice([
                    "ammo",
                    "ammo",
                    "ammo",
                    "heal",
                    "damage_boost",
                ])
                row.append(FLOOR)

            elif ch == "W":
                enemies.append({
                    "id": enemy_id,
                    "type": "wagi",
                    "pos": (r, c),
                    "damage": 10,
                    "max_hp": 20,
                    "hp": 20
                })
                enemy_id += 1
                row.append(FLOOR)

            elif ch == "F":
                enemies.append({
                    "id": enemy_id,
                    "type": "pugi",
                    "pos": (r, c),
                    "damage": 5,
                    "max_hp": 10,
                    "hp": 10
                })
                enemy_id += 1
                row.append(FLOOR)

        grid.append(row)

    if player_pos is None:
        raise ValueError(f"{filename}: Player start P is missing.")

    if exit_pos is None:
        raise ValueError(f"{filename}: Exit E is missing.")

    return {
        "filename": filename,
        "grid": grid,
        "player_pos": player_pos,
        "exit_pos": exit_pos,
        "items": items,
        "enemies": enemies
    }


def load_random_map():
    filename = random.choice(MAP_FILES)
    return load_map(filename)


def load_valid_random_map(max_attempts=20):
    """
    Pick a random map and validate it with BFS before starting the game.
    If the exit is unreachable, another map is selected.
    """
    from pathfinding import can_reach_exit

    for _ in range(max_attempts):
        filename = random.choice(MAP_FILES)
        data = load_map(filename)

        if can_reach_exit(data["grid"], data["player_pos"], data["exit_pos"]):
            return data

    raise ValueError("No valid reachable map found.")


def validate_raw_map(lines, filename):
    if len(lines) != ROWS:
        raise ValueError(f"{filename}: Map must have {ROWS} rows, but has {len(lines)} rows.")

    player_count = 0
    exit_count = 0

    for r, line in enumerate(lines):
        if len(line) != COLS:
            raise ValueError(
                f"{filename}: Row {r} must have {COLS} columns, but has {len(line)}."
            )

        for ch in line:
            if ch not in VALID_CHARS:
                raise ValueError(f"{filename}: Invalid character found: {ch}")

            if ch == "P":
                player_count += 1
            elif ch == "E":
                exit_count += 1

    if player_count != 1:
        raise ValueError(f"{filename}: Map must have exactly one P, but has {player_count}.")

    if exit_count != 1:
        raise ValueError(f"{filename}: Map must have exactly one E, but has {exit_count}.")


def load_all_maps():
    maps = []

    for filename in MAP_FILES:
        maps.append(load_map(filename))

    return maps


def test_map_loader():
    print("Map loader test started.")
    print("-" * 40)

    for filename in MAP_FILES:
        data = load_map(filename)

        grid = data["grid"]
        player_pos = data["player_pos"]
        exit_pos = data["exit_pos"]
        items = data["items"]
        enemies = data["enemies"]

        print(f"{filename} loaded successfully.")
        print(f"Grid size: {len(grid)} x {len(grid[0])}")
        print(f"Player position: {player_pos}")
        print(f"Exit position: {exit_pos}")
        print(f"Items: {len(items)}")
        print(f"Enemies: {len(enemies)}")
        print("-" * 40)

    valid_map = load_valid_random_map()
    print("Valid random map loaded successfully.")
    print(f"Selected map: {valid_map['filename']}")
    print("All map loader tests finished.")


if __name__ == "__main__":
    test_map_loader()