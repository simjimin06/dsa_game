# enemy_ai.py

from pathfinding import make_distance_map

WALL = -1

DIRECTIONS = [
    (-1, 0),  # up
    (1, 0),   # down
    (0, -1),  # left
    (0, 1)    # right
]


def in_bounds(grid, pos):
    row, col = pos
    return 0 <= row < len(grid) and 0 <= col < len(grid[0])


def is_walkable_for_wagi(grid, pos):
    """
    Wagi is a ground enemy.
    It cannot pass through walls.
    """
    row, col = pos
    return in_bounds(grid, pos) and grid[row][col] != WALL


def manhattan_distance(pos1, pos2):
    """
    Manhattan distance for grid movement.
    Used by pugi because pugi can pass through walls.
    """
    r1, c1 = pos1
    r2, c2 = pos2
    return abs(r1 - r2) + abs(c1 - c2)


def get_enemy_positions(enemies):
    return {enemy["pos"] for enemy in enemies}


def choose_wagi_next_pos(enemy_pos, distance_map, grid, occupied_positions=None):
    """
    Wagi follows the BFS distance map.

    distance_map is created from the player's position.
    Therefore, a smaller distance value means closer to the player.
    """
    if occupied_positions is None:
        occupied_positions = set()

    current_row, current_col = enemy_pos
    current_distance = distance_map[current_row][current_col]

    best_pos = enemy_pos
    best_distance = current_distance

    for dr, dc in DIRECTIONS:
        next_pos = (current_row + dr, current_col + dc)
        nr, nc = next_pos

        if not is_walkable_for_wagi(grid, next_pos):
            continue

        if next_pos in occupied_positions:
            continue

        next_distance = distance_map[nr][nc]

        if next_distance is None:
            continue

        if best_distance is None or next_distance < best_distance:
            best_distance = next_distance
            best_pos = next_pos

    return best_pos


def choose_pugi_next_pos(enemy_pos, player_pos, grid, occupied_positions=None):
    """
    Pugi is a flying enemy.
    It can pass through walls, so it uses Manhattan distance.
    """
    if occupied_positions is None:
        occupied_positions = set()

    current_distance = manhattan_distance(enemy_pos, player_pos)

    best_pos = enemy_pos
    best_distance = current_distance

    row, col = enemy_pos

    for dr, dc in DIRECTIONS:
        next_pos = (row + dr, col + dc)

        if not in_bounds(grid, next_pos):
            continue

        if next_pos in occupied_positions:
            continue

        next_distance = manhattan_distance(next_pos, player_pos)

        if next_distance < best_distance:
            best_distance = next_distance
            best_pos = next_pos

    return best_pos


def move_all_enemies(enemies, grid, player_pos):
    """
    Move every enemy one step.

    This function mutates the enemies list directly.

    Returns:
        actions: list of enemy movement records
        This can be used later for the undo system.
    """
    distance_map = make_distance_map(grid, player_pos)
    occupied_positions = get_enemy_positions(enemies)

    actions = []

    for enemy in enemies:
        old_pos = enemy["pos"]
        occupied_positions.remove(old_pos)

        if enemy["type"] == "wagi":
            new_pos = choose_wagi_next_pos(
                old_pos,
                distance_map,
                grid,
                occupied_positions
            )

        elif enemy["type"] == "pugi":
            new_pos = choose_pugi_next_pos(
                old_pos,
                player_pos,
                grid,
                occupied_positions
            )

        else:
            new_pos = old_pos

        enemy["pos"] = new_pos
        occupied_positions.add(new_pos)

        if old_pos != new_pos:
            actions.append({
                "type": "move_enemy",
                "enemy_id": enemy.get("id"),
                "enemy_type": enemy["type"],
                "from": old_pos,
                "to": new_pos
            })

    return actions


def get_enemies_at_position(enemies, pos):
    """
    Return enemies currently located at a specific position.
    Useful for checking collision with the player.
    """
    return [enemy for enemy in enemies if enemy["pos"] == pos]


def get_total_damage(enemies):
    """
    Calculate total damage from a list of enemies.
    """
    return sum(enemy.get("damage", 0) for enemy in enemies)


def test_enemy_ai():
    from copy import deepcopy
    from map_loader import load_map
    from pathfinding import make_distance_map

    print("Enemy AI test started.")
    print("-" * 40)

    for i in range(1, 6):
        filename = f"map{i}.txt"
        data = load_map(filename)

        grid = data["grid"]
        player_pos = data["player_pos"]
        enemies = data["enemies"]

        old_enemies = deepcopy(enemies)
        distance_map = make_distance_map(grid, player_pos)

        actions = move_all_enemies(enemies, grid, player_pos)

        print(f"{filename}")
        print(f"Player position: {player_pos}")
        print(f"Enemy count: {len(enemies)}")
        print(f"Moved enemies: {len(actions)}")

        for old_enemy, new_enemy in zip(old_enemies, enemies):
            enemy_type = new_enemy["type"]
            old_pos = old_enemy["pos"]
            new_pos = new_enemy["pos"]

            if enemy_type == "wagi":
                old_distance = distance_map[old_pos[0]][old_pos[1]]
                new_distance = distance_map[new_pos[0]][new_pos[1]]

                print(
                    f"  Wagi {new_enemy.get('id')}: "
                    f"{old_pos} -> {new_pos} "
                    f"BFS distance {old_distance} -> {new_distance}"
                )

            elif enemy_type == "pugi":
                old_distance = manhattan_distance(old_pos, player_pos)
                new_distance = manhattan_distance(new_pos, player_pos)

                print(
                    f"  Pugi {new_enemy.get('id')}: "
                    f"{old_pos} -> {new_pos} "
                    f"Manhattan distance {old_distance} -> {new_distance}"
                )

        print("-" * 40)

    print("All enemy AI tests finished.")


if __name__ == "__main__":
    test_enemy_ai()