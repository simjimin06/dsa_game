# pathfinding.py

from collections import deque

WALL = -1

DIRECTIONS = [
    (-1, 0),
    (1, 0),
    (0, -1),
    (0, 1)
]


def in_bounds(grid, row, col):
    return 0 <= row < len(grid) and 0 <= col < len(grid[0])


def is_walkable(grid, row, col):
    return in_bounds(grid, row, col) and grid[row][col] != WALL


def can_reach_exit(grid, start_pos, exit_pos):
    queue = deque([start_pos])
    visited = {start_pos}

    while queue:
        row, col = queue.popleft()

        if (row, col) == exit_pos:
            return True

        for dr, dc in DIRECTIONS:
            nr = row + dr
            nc = col + dc
            next_pos = (nr, nc)

            if is_walkable(grid, nr, nc) and next_pos not in visited:
                visited.add(next_pos)
                queue.append(next_pos)

    return False


def make_distance_map(grid, start_pos):
    rows = len(grid)
    cols = len(grid[0])

    distance = [[None for _ in range(cols)] for _ in range(rows)]

    queue = deque([start_pos])
    distance[start_pos[0]][start_pos[1]] = 0

    while queue:
        row, col = queue.popleft()

        for dr, dc in DIRECTIONS:
            nr = row + dr
            nc = col + dc

            if not is_walkable(grid, nr, nc):
                continue

            if distance[nr][nc] is not None:
                continue

            distance[nr][nc] = distance[row][col] + 1
            queue.append((nr, nc))

    return distance


def shortest_distance_to_exit(grid, start_pos, exit_pos):
    distance = make_distance_map(grid, start_pos)
    er, ec = exit_pos
    return distance[er][ec]


def test_pathfinding():
    from map_loader import load_map, MAP_FILES

    print("Pathfinding test started.")
    print("-" * 40)

    for filename in MAP_FILES:
        data = load_map(filename)

        grid = data["grid"]
        player_pos = data["player_pos"]
        exit_pos = data["exit_pos"]

        reachable = can_reach_exit(grid, player_pos, exit_pos)
        distance = shortest_distance_to_exit(grid, player_pos, exit_pos)

        print(f"{filename}")
        print(f"Player position: {player_pos}")
        print(f"Exit position: {exit_pos}")
        print(f"Reachable: {reachable}")
        print(f"Shortest distance: {distance}")

        if reachable:
            print("Result: passed")
        else:
            print("Result: failed")

        print("-" * 40)

    print("All pathfinding tests finished.")


if __name__ == "__main__":
    test_pathfinding()