# pathfinding.py
#BFS 구현, 맵이 격자이고 한 칸 이동 비용이 전부 동일하므로 BFS로 최단 거리 계산이 가능.
#can_reach_exit()는 출구에 도달할 수 있는지 여부를 반환하고, shortest_distance_to_exit()는 출구까지의 최단 거리를 반환. 
# make_distance_map()는 시작 위치에서 모든 셀까지의 거리를 계산하는 BFS 거리 맵을 만듦. 
# 이 거리 맵은 Wagi 적 AI에도 활용됩니다.
from collections import deque

WALL = -1

DIRECTIONS = [
    (-1, 0),  # up
    (1, 0),   # down
    (0, -1),  # left
    (0, 1)    # right
]


def in_bounds(grid, row, col):
    return 0 <= row < len(grid) and 0 <= col < len(grid[0])


def is_walkable(grid, row, col):
    return in_bounds(grid, row, col) and grid[row][col] != WALL


def can_reach_exit(grid, start_pos, exit_pos):
    """
    Return True if the player can reach the exit using BFS.
    """
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
    """
    Make BFS distance map from start_pos.

    Used for:
    1. Checking shortest distance to exit
    2. Wagi enemy AI

    Unreachable cells remain None.
    """
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
    """
    Return shortest distance from start_pos to exit_pos.
    Return None if unreachable.
    """
    distance = make_distance_map(grid, start_pos)
    er, ec = exit_pos
    return distance[er][ec]


if __name__ == "__main__":
    from map_loader import load_map

    data = load_map("map1.txt")

    result = can_reach_exit(
        data["grid"],
        data["player_pos"],
        data["exit_pos"]
    )

    print("Can reach exit:", result)

    distance = shortest_distance_to_exit(
        data["grid"],
        data["player_pos"],
        data["exit_pos"]
    )

    print("Shortest distance:", distance)

def test_pathfinding():
    from map_loader import load_map

    print("Pathfinding test started.")
    print("-" * 40)

    for i in range(1, 6):
        filename = f"map{i}.txt"
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