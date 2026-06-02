# test_maps.py
#5개의 맵이 전부 클리어 가능한지, 플레이어에서 출구까지의 최단 거리가 올바르게 계산되는지 테스트하는 코드입니다.
# cli: python test_maps.py

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