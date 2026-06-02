# # test_map_loader.py

# from map_loader import load_map, load_random_map

# ROWS = 30
# COLS = 60
# VALID_GRID_VALUES = {-1, 0, 2}


# def check_position(name, pos):
#     assert isinstance(pos, tuple), f"{name} must be a tuple."
#     assert len(pos) == 2, f"{name} must have row and col."

#     r, c = pos
#     assert isinstance(r, int) and isinstance(c, int), f"{name} must contain integers."
#     assert 0 <= r < ROWS, f"{name} row is out of range: {pos}"
#     assert 0 <= c < COLS, f"{name} col is out of range: {pos}"


# def check_map(filename):
#     data = load_map(filename)

#     # 1. 반환값이 dictionary인지 확인
#     assert isinstance(data, dict), "load_map must return a dictionary."

#     required_keys = {"grid", "player_pos", "exit_pos", "items", "enemies"}
#     assert required_keys.issubset(data.keys()), f"Missing keys: {required_keys - set(data.keys())}"

#     grid = data["grid"]
#     player_pos = data["player_pos"]
#     exit_pos = data["exit_pos"]
#     items = data["items"]
#     enemies = data["enemies"]

#     # 2. grid 크기 확인
#     assert len(grid) == ROWS, f"{filename}: grid must have {ROWS} rows."

#     for r, row in enumerate(grid):
#         assert len(row) == COLS, f"{filename}: row {r} must have {COLS} columns."

#         for value in row:
#             assert value in VALID_GRID_VALUES, f"{filename}: invalid grid value {value}"

#     # 3. player / exit 위치 확인
#     check_position("player_pos", player_pos)
#     check_position("exit_pos", exit_pos)

#     assert player_pos != exit_pos, f"{filename}: player and exit cannot be at the same position."

#     er, ec = exit_pos
#     assert grid[er][ec] == 2, f"{filename}: exit_pos must point to EXIT value 2."

#     pr, pc = player_pos
#     assert grid[pr][pc] == 0, f"{filename}: player_pos should be on FLOOR value 0."

#     # 4. items 확인
#     assert isinstance(items, dict), f"{filename}: items must be a dictionary."

#     occupied_positions = {player_pos, exit_pos}

#     for pos, item_name in items.items():
#         check_position("item position", pos)
#         assert isinstance(item_name, str), f"{filename}: item name must be string."

#         r, c = pos
#         assert grid[r][c] == 0, f"{filename}: item must be placed on floor."
#         assert pos not in occupied_positions, f"{filename}: item overlaps with another object at {pos}"

#         occupied_positions.add(pos)

#     # 5. enemies 확인
#     assert isinstance(enemies, list), f"{filename}: enemies must be a list."

#     for enemy in enemies:
#         assert isinstance(enemy, dict), f"{filename}: each enemy must be a dictionary."
#         assert "type" in enemy, f"{filename}: enemy missing type."
#         assert "pos" in enemy, f"{filename}: enemy missing pos."

#         assert enemy["type"] in {"wagi", "pugi"}, f"{filename}: invalid enemy type {enemy['type']}"

#         pos = enemy["pos"]
#         check_position("enemy position", pos)

#         r, c = pos
#         assert grid[r][c] == 0, f"{filename}: enemy must be placed on floor."
#         assert pos not in occupied_positions, f"{filename}: enemy overlaps with another object at {pos}"

#         occupied_positions.add(pos)

#     print(f"{filename} passed.")


# def main():
#     for i in range(1, 6):
#         check_map(f"map{i}.txt")

#     # random map도 정상 작동하는지 확인
#     random_map = load_random_map()
#     assert isinstance(random_map, dict), "load_random_map must return a dictionary."

#     print("All map loader tests passed.")


# if __name__ == "__main__":
#     main()