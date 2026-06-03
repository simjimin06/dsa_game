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


def load_map(filename):
    """
    Load one map file and separate static map data from dynamic objects.

    Returns:
        {
            "grid": 2D list,
            "player_pos": (row, col),
            "exit_pos": (row, col),
            "items": {(row, col): item_name},
            "enemies": [enemy dict, ...]
        }
    """
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
                items[(r, c)] = "potion"
                row.append(FLOOR)

            elif ch == "W":
                enemies.append({
                    "id": enemy_id,
                    "type": "wagi",
                    "pos": (r, c),
                    "damage": 10,
                    "max_hp": 20, #추기
                    "hp": 20 #추가
                })
                enemy_id += 1
                row.append(FLOOR)

            elif ch == "F":
                enemies.append({
                    "id": enemy_id,
                    "type": "pugi",
                    "pos": (r, c),
                    "damage": 5,
                    "max_hp": 10, #추가
                    "hp": 10 #추가
                })
                enemy_id += 1
                row.append(FLOOR)

        grid.append(row)

    if player_pos is None:
        raise ValueError(f"{filename}: Player start P is missing.")

    if exit_pos is None:
        raise ValueError(f"{filename}: Exit E is missing.")

    return {
        "grid": grid,
        "player_pos": player_pos,
        "exit_pos": exit_pos,
        "items": items,
        "enemies": enemies
    }


def load_random_map():
    """
    Load one random map from map1.txt ~ map5.txt.
    """
    filename = random.choice([
        "map1.txt",
        "map2.txt",
        "map3.txt",
        "map4.txt",
        "map5.txt"
    ])
    return load_map(filename)


def validate_raw_map(lines, filename):
    """
    Check whether the raw text map has correct size and characters.
    """
    if len(lines) != ROWS:
        raise ValueError(f"{filename}: Map must have {ROWS} rows, but has {len(lines)} rows.")

    for r, line in enumerate(lines):
        if len(line) != COLS:
            raise ValueError(
                f"{filename}: Row {r} must have {COLS} columns, but has {len(line)}."
            )

        for ch in line:
            if ch not in VALID_CHARS:
                raise ValueError(f"{filename}: Invalid character found: {ch}")


def load_all_maps():
    """
    Useful for testing all five maps.
    """
    maps = []

    for i in range(1, 6):
        filename = f"map{i}.txt"
        maps.append(load_map(filename))

    return maps


if __name__ == "__main__":
    # Quick test
    for i in range(1, 6):
        data = load_map(f"map{i}.txt")
        print(f"map{i}.txt loaded successfully.")
        print("Player:", data["player_pos"])
        print("Exit:", data["exit_pos"])
        print("Items:", len(data["items"]))
        print("Enemies:", len(data["enemies"]))
        print()
        
        
def test_map_loader():
    print("Map loader test started.")
    print("-" * 40)

    for i in range(1, 6):
        filename = f"map{i}.txt"
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

    random_map = load_random_map()
    print("Random map loaded successfully.")
    print("All map loader tests finished.")


if __name__ == "__main__":
    test_map_loader()