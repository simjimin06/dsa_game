# Dungeon Escape

Dungeon Escape is a grid-based dungeon survival game implemented in Python with Pygame.

The player explores a dungeon map, collects items, avoids or defeats enemies, and reaches the exit to clear the game. This project was developed for a Data Structures and Algorithms team project, so each core game feature is connected to a specific data structure or algorithm.

---

## 1. How to Run

### Install dependencies

```bash
pip install -r requirements.txt
```

If needed, install Pygame directly:

```bash
pip install pygame
```

### Run the game

Windows:

```bash
python -B main.py
```

Linux / macOS:

```bash
python3 -B main.py
```

The `-B` option prevents Python from creating `__pycache__` files.

---

## 2. Controls

| Key                 | Action                               |
| ------------------- | ------------------------------------ |
| `WASD` / Arrow Keys | Move player                          |
| `Space` / `F`       | Attack with projectile               |
| `H`                 | Use heal item                        |
| `B`                 | Toggle enemy detection range display |
| `U`                 | Undo previous valid turn             |
| `R`                 | Restart game                         |
| `ESC`               | Quit game                            |

---

## 3. Gameplay Rules

The goal is to move the player to the green exit tile.

The player starts with:

* 100 HP
* 10 base attack power
* 3 ammo

Trying to move into a wall or outside the map is an invalid action and does not consume a turn.

### Items

Item spawn points are written as `I` in map files. When a map is loaded, each item spawn point is randomly converted into one of the item types.

| Item           | Effect                                  |
| -------------- | --------------------------------------- |
| `ammo`         | Adds 1 projectile shot                  |
| `heal`         | Restores 20 HP                          |
| `damage_boost` | Adds +10 damage to the next attack only |

The current inventory is displayed at the top of the game screen.

### Attack

The player attacks in the current facing direction. A projectile travels in a straight line until it:

1. Hits a wall
2. Leaves the map
3. Reaches maximum attack range
4. Hits the first enemy in its path

Attacking consumes 1 ammo and counts as a valid turn.

### Enemies

There are two enemy types.

| Enemy  | Description                                                                                          |
| ------ | ---------------------------------------------------------------------------------------------------- |
| `Wagi` | Ground enemy. It cannot pass through walls. When the player is detected, it uses BFS-based movement. |
| `Pugi` | Flying enemy. It can pass through walls. When the player is detected, it uses Manhattan distance.    |

Detection ranges:

| Enemy | Detection Range |
| ----- | --------------: |
| Wagi  |         7 tiles |
| Pugi  |         5 tiles |

Outside detection range, enemies move randomly.

Enemy stats:

| Enemy | HP | Damage |
| ----- | -: | -----: |
| Wagi  | 20 |     10 |
| Pugi  | 10 |      5 |

---

## 4. Scoring System

The final score is calculated when the player reaches the exit.

```text
score = 1000 - (turn_count × 5) + (remaining_hp × 2) + (items_collected × 50) + (enemies_defeated × 100)
```

Score factors:

* Fewer turns produce a higher score.
* More remaining HP increases the score.
* More collected items increase the score.
* Defeating enemies gives bonus points.

Leaderboard data is saved in:

```text
data/leaderboard.json
```

---

## 5. Main Files

| File             | Role                                                                                                |
| ---------------- | --------------------------------------------------------------------------------------------------- |
| `main.py`        | Program entry point. Reads player name and starts the game.                                         |
| `game.py`        | Main game controller. Handles Pygame loop, movement, turns, attacks, undo, drawing, and game state. |
| `inventory.py`   | Manages item counts using a dictionary-based inventory.                                             |
| `map_loader.py`  | Loads map files, separates static grid data from dynamic objects, and validates selected maps.      |
| `pathfinding.py` | Provides BFS reachability checks and BFS distance maps.                                             |
| `enemy_ai.py`    | Handles Wagi and Pugi movement logic.                                                               |
| `leaderboard.py` | Calculates scores and manages heap-based leaderboard ranking.                                       |
| `create_maps.py` | Helper script used to generate `map1.txt` to `map5.txt`.                                            |

---

## 6. Data Structures and Algorithms Summary

| Core Feature    | Data Structure / Algorithm                            | Main File                         |
| --------------- | ----------------------------------------------------- | --------------------------------- |
| Dungeon Map     | 2D grid, graph adjacency, BFS validation              | `map_loader.py`, `pathfinding.py` |
| Undo System     | Stack / LIFO                                          | `game.py`                         |
| Turn Management | Queue / deque                                         | `game.py`                         |
| Item Inventory  | Dictionary                                            | `inventory.py`, `game.py`         |
| Enemy AI        | BFS distance map, Manhattan distance, random movement | `enemy_ai.py`, `pathfinding.py`   |
| Leaderboard     | Heap / top-k ranking                                  | `leaderboard.py`                  |

### Dungeon Map

The dungeon is stored as a 30 by 60 grid. Each cell can be treated as a graph node connected to its up, down, left, and right neighbors.

All provided maps are designed to be reachable. Before a selected map is used, BFS validation is used as a safety check to confirm that the exit is reachable from the player start position.

### Undo System

The undo system uses a stack. Each valid turn stores action records, and pressing `U` restores the most recent turn first.

### Turn Management

The turn system uses a queue with `collections.deque`. A valid player action advances the turn order. Invalid actions, such as walking into a wall, do not consume a turn.

### Inventory

The inventory uses a dictionary. Item names are stored as keys and item counts are stored as values.

### Enemy AI

Wagi uses BFS-based movement because it cannot pass through walls. Pugi uses Manhattan distance because it can pass through walls. When the player is outside detection range, enemies move randomly.

### Leaderboard

The leaderboard uses Python `heapq`. Since `heapq` is a min heap, negative scores are stored to simulate max-heap behavior.

---

## 7. Folder Structure

```text
DSA_GAME/
├─ main.py
├─ game.py
├─ inventory.py
├─ map_loader.py
├─ create_maps.py
├─ enemy_ai.py
├─ pathfinding.py
├─ leaderboard.py
├─ maps/
│  ├─ map1.txt
│  ├─ map2.txt
│  ├─ map3.txt
│  ├─ map4.txt
│  └─ map5.txt
├─ data/
│  └─ leaderboard.json
├─ requirements.txt
└─ README.md
```

Development folders such as `.venv/`, `__pycache__/`, and `legacy/` are not required to run the game.

---

## 8. Module Test Commands

Each module can be run directly for basic testing.

Windows:

```bash
python -B map_loader.py
python -B pathfinding.py
python -B enemy_ai.py
python -B leaderboard.py
```

Linux / macOS:

```bash
python3 -B map_loader.py
python3 -B pathfinding.py
python3 -B enemy_ai.py
python3 -B leaderboard.py
```

---

## 9. Notes

* All Python files should remain in the same project folder.
* The `maps/` folder must contain `map1.txt` to `map5.txt`.
* The `data/` folder stores leaderboard data.
* If the project is moved to another computer, install Pygame for the Python interpreter used to run `main.py`.
