Algorithm/Data Modules

map_loader.py
- Loads one of five fixed dungeon maps from maps/
- Separates static grid data from dynamic objects
- Returns grid, player position, exit position, items, and enemies

pathfinding.py
- Uses BFS to check whether the exit is reachable
- Creates BFS distance map for enemy AI

enemy_ai.py
- Wagi uses BFS distance map and cannot pass through walls
- Pugi uses Manhattan distance and can pass through walls
- Returns enemy movement actions for undo system

leaderboard.py
- Uses heapq as a max heap by storing negative scores
- Saves leaderboard data in data/leaderboard.json

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not used, install Pygame directly:

```bash
pip install pygame
```

---

### 2. Run the main game

```bash
python -B main.py
```

On Linux, use:

```bash
python3 -B main.py
```

The `-B` option prevents Python from creating `__pycache__` files.

---

## Module Test Commands

Each module can be executed directly to check whether it works correctly.

### Map Loader

```bash
python -B map_loader.py
```

Linux:

```bash
python3 -B map_loader.py
```

This checks whether `map1.txt` to `map5.txt` are loaded correctly and whether map data is separated into `grid`, `player_pos`, `exit_pos`, `items`, and `enemies`.

---

### Pathfinding

```bash
python -B pathfinding.py
```

Linux:

```bash
python3 -B pathfinding.py
```

This checks whether each map is reachable from the player start position to the exit using BFS.

---

### Enemy AI

```bash
python -B enemy_ai.py
```

Linux:

```bash
python3 -B enemy_ai.py
```

This checks whether Wagi moves using the BFS distance map and Pugi moves using Manhattan distance.

---

### Leaderboard

```bash
python -B leaderboard.py
```

Linux:

```bash
python3 -B leaderboard.py
```

This checks whether the heap-based leaderboard logic works correctly.

---

## File Structure

```text
DSA_GAME/
├─ main.py
├─ game.py
├─ map_loader.py
├─ pathfinding.py
├─ enemy_ai.py
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
