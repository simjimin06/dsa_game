# test_maps.py

from map_loader import load_map
from pathfinding import can_reach_exit, shortest_distance_to_exit

for i in range(1, 6):
    filename = f"map{i}.txt"
    data = load_map(filename)

    reachable = can_reach_exit(
        data["grid"],
        data["player_pos"],
        data["exit_pos"]
    )

    distance = shortest_distance_to_exit(
        data["grid"],
        data["player_pos"],
        data["exit_pos"]
    )

    print(f"{filename}")
    print("Reachable:", reachable)
    print("Shortest distance:", distance)
    print("Player:", data["player_pos"])
    print("Exit:", data["exit_pos"])
    print("Items:", len(data["items"]))
    print("Enemies:", len(data["enemies"]))
    print("-" * 40)