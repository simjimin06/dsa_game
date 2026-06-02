# """
# entity_spawner.py

# 맵 위에 적과 아이템을 배치하는 파일.

# 역할:
# - map_generator.py가 만든 GeneratedDungeon을 입력받는다.
# - 방 내부의 빈 좌표에 적과 아이템을 배치한다.
# - 플레이어 시작 위치와 종료 위치에는 배치하지 않는다.
# - 같은 위치에 여러 객체가 겹치지 않게 한다.

# 중요:
# - 플레이어, 적, 아이템은 map grid에 직접 넣지 않는다.
# - map grid는 지형만 관리한다.
# - entity_spawner.py는 적/아이템 위치 목록만 반환한다.

# 기본 배치 규칙:
# - 각 일반 방마다 와기 1~4마리
# - 각 일반 방마다 프기 0~2마리
# - 회복 아이템, 점수 아이템, 공격 강화 아이템 배치

# 아이템 종류:
# - HEAL: 체력 회복
# - SCORE: 점수 획득
# - POWER_BOOST: n턴 동안 활 공격력 증가
# """

# from __future__ import annotations

# from dataclasses import dataclass
# from enum import Enum
# from random import Random
# from typing import Dict, List, Optional, Set, Tuple

# from map_generator import (
#     DOOR,
#     EXIT,
#     ROOM_FLOOR,
#     START,
#     WALL,
#     GeneratedDungeon,
#     Position,
#     Room,
# )


# # =========================
# # Entity constants
# # =========================
# SAFE_DISTANCE_FROM_START = 12
# SAFE_DISTANCE_FROM_EXIT = 4


# class EnemyType(str, Enum):
#     """적 종류."""

#     WAGI = "wagi"      # 지상 적. 벽을 못 넘고, 벽 너머를 인지하지 못함.
#     PEUGI = "peugi"    # 공중 적. 벽을 넘을 수 있고, 벽 너머도 인지 가능.


# class ItemType(str, Enum):
#     """아이템 종류."""

#     HEAL = "heal"
#     SCORE = "score"
#     POWER_BOOST = "power_boost"


# @dataclass(frozen=True)
# class Enemy:
#     """적 정보."""

#     id: int
#     enemy_type: EnemyType
#     position: Position
#     room_id: int
#     hp: int
#     damage: int
#     vision_range: int


# @dataclass(frozen=True)
# class Item:
#     """아이템 정보."""

#     id: int
#     item_type: ItemType
#     position: Position
#     room_id: int
#     value: int
#     duration_turns: int = 0


# @dataclass(frozen=True)
# class SpawnedEntities:
#     """배치 결과."""

#     player_position: Position
#     exit_position: Position
#     enemies: List[Enemy]
#     items: List[Item]
#     occupied_positions: Set[Position]


# class EntitySpawner:
#     """던전 위에 적과 아이템을 배치하는 클래스."""

#     def __init__(
#         self,
#         wagi_per_room: tuple[int, int] = (1, 4),
#         peugi_per_room: tuple[int, int] = (0, 2),
#         heal_item_count: int = 8,
#         score_item_count: int = 10,
#         power_boost_item_count: int = 4,
#         power_boost_duration: int = 5,
#         seed: Optional[int] = None,
#     ) -> None:
#         """
#         Args:
#             wagi_per_room:
#                 방마다 생성할 와기 수 범위. 기본 1~4.
#             peugi_per_room:
#                 방마다 생성할 프기 수 범위. 기본 0~2.
#             heal_item_count:
#                 전체 던전에 배치할 회복 아이템 수.
#             score_item_count:
#                 전체 던전에 배치할 점수 아이템 수.
#             power_boost_item_count:
#                 전체 던전에 배치할 공격 강화 아이템 수.
#             power_boost_duration:
#                 공격 강화 지속 턴 수.
#             seed:
#                 랜덤 시드. None이면 매번 다른 배치.
#         """
#         self.wagi_per_room = wagi_per_room
#         self.peugi_per_room = peugi_per_room
#         self.heal_item_count = heal_item_count
#         self.score_item_count = score_item_count
#         self.power_boost_item_count = power_boost_item_count
#         self.power_boost_duration = power_boost_duration
#         self.random = Random(seed)

#         self._validate_range("wagi_per_room", wagi_per_room)
#         self._validate_range("peugi_per_room", peugi_per_room)

#     def spawn(self, dungeon: GeneratedDungeon) -> SpawnedEntities:
#         """
#         던전 위에 적과 아이템을 배치한다.

#         Args:
#             dungeon:
#                 map_generator.py에서 생성된 GeneratedDungeon.

#         Returns:
#             SpawnedEntities
#         """
#         occupied: Set[Position] = set()
#         occupied.add(dungeon.start_position)
#         occupied.add(dungeon.exit_position)

#         enemies: List[Enemy] = []
#         items: List[Item] = []

#         spawnable_rooms = self._get_spawnable_rooms(dungeon)

#         enemy_id = 0
#         for room in spawnable_rooms:
#             enemy_id = self._spawn_enemies_in_room(
#                 dungeon=dungeon,
#                 room=room,
#                 occupied=occupied,
#                 enemies=enemies,
#                 next_enemy_id=enemy_id,
#             )

#         item_id = 0
#         item_id = self._spawn_items(
#             dungeon=dungeon,
#             rooms=spawnable_rooms,
#             occupied=occupied,
#             items=items,
#             next_item_id=item_id,
#             item_type=ItemType.HEAL,
#             count=self.heal_item_count,
#         )
#         item_id = self._spawn_items(
#             dungeon=dungeon,
#             rooms=spawnable_rooms,
#             occupied=occupied,
#             items=items,
#             next_item_id=item_id,
#             item_type=ItemType.SCORE,
#             count=self.score_item_count,
#         )
#         self._spawn_items(
#             dungeon=dungeon,
#             rooms=spawnable_rooms,
#             occupied=occupied,
#             items=items,
#             next_item_id=item_id,
#             item_type=ItemType.POWER_BOOST,
#             count=self.power_boost_item_count,
#         )

#         return SpawnedEntities(
#             player_position=dungeon.start_position,
#             exit_position=dungeon.exit_position,
#             enemies=enemies,
#             items=items,
#             occupied_positions=occupied,
#         )

#     def _spawn_enemies_in_room(
#         self,
#         dungeon: GeneratedDungeon,
#         room: Room,
#         occupied: Set[Position],
#         enemies: List[Enemy],
#         next_enemy_id: int,
#     ) -> int:
#         """특정 방 안에 와기와 프기를 배치한다."""
#         wagi_count = self.random.randint(*self.wagi_per_room)
#         peugi_count = self.random.randint(*self.peugi_per_room)

#         for _ in range(wagi_count):
#             position = self._find_spawn_position_in_room(dungeon, room, occupied)
#             if position is None:
#                 break

#             enemy = Enemy(
#                 id=next_enemy_id,
#                 enemy_type=EnemyType.WAGI,
#                 position=position,
#                 room_id=room.id,
#                 hp=3,
#                 damage=2,
#                 vision_range=5,
#             )
#             enemies.append(enemy)
#             occupied.add(position)
#             next_enemy_id += 1

#         for _ in range(peugi_count):
#             position = self._find_spawn_position_in_room(dungeon, room, occupied)
#             if position is None:
#                 break

#             enemy = Enemy(
#                 id=next_enemy_id,
#                 enemy_type=EnemyType.PEUGI,
#                 position=position,
#                 room_id=room.id,
#                 hp=2,
#                 damage=1,
#                 vision_range=5,
#             )
#             enemies.append(enemy)
#             occupied.add(position)
#             next_enemy_id += 1

#         return next_enemy_id

#     def _spawn_items(
#         self,
#         dungeon: GeneratedDungeon,
#         rooms: List[Room],
#         occupied: Set[Position],
#         items: List[Item],
#         next_item_id: int,
#         item_type: ItemType,
#         count: int,
#     ) -> int:
#         """아이템을 여러 방에 분산 배치한다."""
#         if count <= 0 or not rooms:
#             return next_item_id

#         for _ in range(count):
#             room = self.random.choice(rooms)
#             position = self._find_spawn_position_in_room(dungeon, room, occupied)
#             if position is None:
#                 continue

#             value, duration = self._get_item_effect(item_type)

#             item = Item(
#                 id=next_item_id,
#                 item_type=item_type,
#                 position=position,
#                 room_id=room.id,
#                 value=value,
#                 duration_turns=duration,
#             )
#             items.append(item)
#             occupied.add(position)
#             next_item_id += 1

#         return next_item_id

#     def _get_spawnable_rooms(self, dungeon: GeneratedDungeon) -> List[Room]:
#         """
#         적과 아이템을 배치할 수 있는 방 목록을 반환한다.

#         시작 방은 제외한다.
#         종료 방은 완전히 비워두면 너무 안전해질 수 있으므로 포함한다.
#         단, exit_position 근처에는 직접 배치하지 않는다.
#         """
#         return [room for room in dungeon.rooms if room.id != dungeon.start_room_id]

#     def _find_spawn_position_in_room(
#         self,
#         dungeon: GeneratedDungeon,
#         room: Room,
#         occupied: Set[Position],
#         max_attempts: int = 100,
#     ) -> Optional[Position]:
#         """방 내부에서 배치 가능한 좌표를 찾는다."""
#         for _ in range(max_attempts):
#             position = room.random_inner_position(self.random, margin=2)
#             row, col = position

#             if position in occupied:
#                 continue

#             if dungeon.grid[row][col] != ROOM_FLOOR:
#                 continue

#             if self._manhattan(position, dungeon.start_position) < SAFE_DISTANCE_FROM_START:
#                 continue

#             if self._manhattan(position, dungeon.exit_position) < SAFE_DISTANCE_FROM_EXIT:
#                 continue

#             return position

#         return None

#     def _get_item_effect(self, item_type: ItemType) -> tuple[int, int]:
#         """아이템 효과값을 반환한다."""
#         if item_type == ItemType.HEAL:
#             return 3, 0

#         if item_type == ItemType.SCORE:
#             return 100, 0

#         if item_type == ItemType.POWER_BOOST:
#             # value는 추가 공격력, duration은 지속 턴 수.
#             return 2, self.power_boost_duration

#         raise ValueError(f"알 수 없는 아이템 종류: {item_type}")

#     def _validate_range(self, name: str, value: tuple[int, int]) -> None:
#         low, high = value
#         if low < 0 or high < low:
#             raise ValueError(f"{name} 범위가 잘못되었다: {value}")

#     def _manhattan(self, a: Position, b: Position) -> int:
#         return abs(a[0] - b[0]) + abs(a[1] - b[1])


# def summarize_entities(spawned: SpawnedEntities) -> Dict[str, int]:
#     """배치 결과 요약을 dict로 반환한다."""
#     wagi_count = sum(1 for enemy in spawned.enemies if enemy.enemy_type == EnemyType.WAGI)
#     peugi_count = sum(1 for enemy in spawned.enemies if enemy.enemy_type == EnemyType.PEUGI)
#     heal_count = sum(1 for item in spawned.items if item.item_type == ItemType.HEAL)
#     score_count = sum(1 for item in spawned.items if item.item_type == ItemType.SCORE)
#     power_boost_count = sum(
#         1 for item in spawned.items if item.item_type == ItemType.POWER_BOOST
#     )

#     return {
#         "wagi": wagi_count,
#         "peugi": peugi_count,
#         "heal_items": heal_count,
#         "score_items": score_count,
#         "power_boost_items": power_boost_count,
#         "total_enemies": len(spawned.enemies),
#         "total_items": len(spawned.items),
#     }


# if __name__ == "__main__":
#     from map_generator import MapGenerator

#     generator = MapGenerator(seed=None)
#     dungeon = generator.generate()

#     spawner = EntitySpawner(seed=None)
#     spawned = spawner.spawn(dungeon)

#     print("=== Entity Spawn Summary ===")
#     summary = summarize_entities(spawned)
#     for key, value in summary.items():
#         print(f"{key}: {value}")

#     print(f"Player position: {spawned.player_position}")
#     print(f"Exit position: {spawned.exit_position}")

#     print("\nFirst 10 enemies:")
#     for enemy in spawned.enemies[:10]:
#         print(enemy)

#     print("\nFirst 10 items:")
#     for item in spawned.items[:10]:
#         print(item)
