# """
# map_generator.py

# 큰 랜덤 던전 맵 생성 전용 파일.

# 목표:
# - 3~7분 정도 플레이할 수 있는 규모의 하나의 큰 던전 생성
# - 화면 viewport보다 훨씬 큰 전체 맵 생성
# - 방은 항상 직사각형
# - 복도는 항상 직선 구간으로 생성
#   - 방이 가로/세로로 바로 맞으면 완전한 일자 복도
#   - 대각선 위치의 방은 ㄱ자 복도 사용
#   - 이때도 각 구간은 가로/세로 직선이다.
# - 방 사이 간격을 충분히 확보해서 복도 생성 오류를 줄임
# - 같은 두 방 사이에는 복도 하나만 생성
# - 복도끼리 겹치거나 교차하지 않도록 최대한 제한
# - 시작 위치와 종료 위치를 생성해서 반환

# 이 파일에서 하지 않는 것:
# - 플레이어 이동
# - 시야 처리
# - 화면 렌더링
# - 적 AI
# - 아이템 배치
# - undo system

# 타일 값 규칙:
# WALL       = -1  # 벽 / 이동 불가
# ROOM_FLOOR = 0   # 방 내부 바닥
# CORRIDOR   = 1   # 복도
# DOOR       = 2   # 방과 복도의 연결 지점
# START      = 8   # 플레이어 시작 위치
# EXIT       = 9   # 게임 종료 위치
# """

# from __future__ import annotations

# from collections import deque
# from dataclasses import dataclass
# from random import Random
# from typing import Dict, Iterable, List, Optional, Set, Tuple


# # =========================
# # Tile constants
# # =========================
# WALL = -1
# ROOM_FLOOR = 0
# CORRIDOR = 1
# DOOR = 2
# START = 8
# EXIT = 9

# # 기존 코드와 호환이 필요할 경우 EMPTY를 ROOM_FLOOR처럼 사용할 수 있다.
# EMPTY = ROOM_FLOOR

# WALKABLE_TILES = {ROOM_FLOOR, CORRIDOR, DOOR, START, EXIT}

# Position = Tuple[int, int]  # (row, col)
# MapGrid = List[List[int]]
# RoomEdge = Tuple[int, int]  # (room_id_a, room_id_b), 항상 작은 id가 앞에 온다.


# @dataclass(frozen=True)
# class Room:
#     """던전 방 정보."""

#     id: int
#     top: int
#     left: int
#     height: int
#     width: int

#     @property
#     def bottom(self) -> int:
#         return self.top + self.height - 1

#     @property
#     def right(self) -> int:
#         return self.left + self.width - 1

#     @property
#     def center(self) -> Position:
#         return (
#             self.top + self.height // 2,
#             self.left + self.width // 2,
#         )

#     @property
#     def area(self) -> int:
#         return self.height * self.width

#     def contains(self, position: Position) -> bool:
#         row, col = position
#         return self.top <= row <= self.bottom and self.left <= col <= self.right

#     def overlaps(self, other: "Room", padding: int = 8) -> bool:
#         """
#         다른 방과 겹치거나 너무 가까운지 확인한다.
#         padding이 클수록 방 사이 간격이 넓어진다.
#         """
#         return not (
#             self.right + padding < other.left
#             or self.left - padding > other.right
#             or self.bottom + padding < other.top
#             or self.top - padding > other.bottom
#         )

#     def random_inner_position(self, random: Random, margin: int = 2) -> Position:
#         """방 안쪽에서 랜덤 좌표를 반환한다."""
#         min_row = self.top + margin
#         max_row = self.bottom - margin
#         min_col = self.left + margin
#         max_col = self.right - margin

#         if min_row > max_row:
#             min_row, max_row = self.top, self.bottom
#         if min_col > max_col:
#             min_col, max_col = self.left, self.right

#         return random.randint(min_row, max_row), random.randint(min_col, max_col)


# @dataclass(frozen=True)
# class CorridorPlan:
#     """방 두 개를 연결하는 복도 계획."""

#     room_a_id: int
#     room_b_id: int
#     door_a: Position
#     door_b: Position
#     door_a_orientation: str
#     door_b_orientation: str
#     centerline: List[Position]


# @dataclass(frozen=True)
# class GeneratedDungeon:
#     """생성된 던전 전체 데이터."""

#     grid: MapGrid
#     rooms: List[Room]
#     edges: List[RoomEdge]
#     start_position: Position
#     exit_position: Position
#     start_room_id: int
#     exit_room_id: int


# class MapGenerator:
#     """큰 랜덤 던전 맵 생성기."""

#     def __init__(
#         self,
#         rows: int = 130,
#         cols: int = 180,
#         room_count: int = 26,
#         min_room_height: int = 8,
#         max_room_height: int = 17,
#         min_room_width: int = 11,
#         max_room_width: int = 25,
#         room_padding: int = 3,
#         corridor_width: int = 3,
#         corridor_spacing: int = 0,
#         preferred_corridor_length: int = 48,
#         connection_randomness: int = 2,
#         extra_connection_probability: float = 0.0,
#         max_extra_connections: Optional[int] = 0,
#         allow_corridor_intersections: bool = True,
#         max_room_attempts: int = 6000,
#         generation_retries: int = 20,
#         seed: Optional[int] = None,
#     ) -> None:
#         """
#         Args:
#             rows, cols:
#                 전체 던전 맵 크기.
#                 기본 130 x 180은 viewport 45 x 80보다 크면서도 방이 너무 멀리 떨어지지 않는 크기다.

#             room_count:
#                 방 개수. 기본 26개는 방을 더 자주 만나게 하면서도 통로가 과하게 많아지지 않도록 잡은 값이다.

#             min_room_height, max_room_height:
#                 방 세로 크기 범위.

#             min_room_width, max_room_width:
#                 방 가로 크기 범위.

#             room_padding:
#                 방과 방 사이 최소 여유 공간.
#                 방 개수를 늘렸기 때문에 기본값은 3으로 낮춰 방 밀도를 높인다.

#             corridor_width:
#                 복도 폭. 3이면 캐릭터 이동과 시각적 구분에 무난하다.
#                 1, 3, 5 같은 홀수만 허용한다.

#             corridor_spacing:
#                 복도와 복도 사이에 남길 최소 여유.
#                 0이면 복도 실제 폭의 충돌만 막는다. 안정적인 생성을 위해 기본값은 0으로 둔다.

#             preferred_corridor_length:
#                 두 방 사이 연결에서 우선적으로 허용할 중심 거리다.
#                 이 값보다 가까운 방을 먼저 연결하고, 후보가 없을 때만 더 먼 방을 허용한다.
#                 기본 48로 두어 방이 늘어나도 긴 복도가 과도하게 생기지 않게 한다.

#             connection_randomness:
#                 연결 후보 중 가까운 몇 개를 랜덤 선택할지 결정한다.
#                 값이 너무 크면 긴 복도와 교차가 늘 수 있으므로 기본 2로 제한했다.

#             extra_connection_probability:
#                 전체 연결 후 추가 복도를 만들 확률.
#                 길 얽힘을 줄이기 위해 기본 0.0으로 둔다.

#             max_extra_connections:
#                 추가 복도 개수 상한. 기본 0.

#             seed:
#                 랜덤 시드.
#                 - seed=None: 실행할 때마다 다른 맵 생성
#                 - seed=42 같은 정수: 항상 같은 맵 생성
#         """
#         if rows <= 0 or cols <= 0:
#             raise ValueError("rows와 cols는 양수여야 한다.")
#         if room_count < 2:
#             raise ValueError("room_count는 2 이상이어야 한다.")
#         if min_room_height <= 0 or max_room_height < min_room_height:
#             raise ValueError("방 높이 범위가 잘못되었다.")
#         if min_room_width <= 0 or max_room_width < min_room_width:
#             raise ValueError("방 너비 범위가 잘못되었다.")
#         if corridor_width <= 0 or corridor_width % 2 == 0:
#             raise ValueError("corridor_width는 1, 3, 5 같은 양의 홀수여야 한다.")
#         if corridor_spacing < 0:
#             raise ValueError("corridor_spacing은 0 이상이어야 한다.")
#         if preferred_corridor_length <= 0:
#             raise ValueError("preferred_corridor_length는 양수여야 한다.")
#         if connection_randomness <= 0:
#             raise ValueError("connection_randomness는 양수여야 한다.")
#         if not 0 <= extra_connection_probability <= 1:
#             raise ValueError("extra_connection_probability는 0과 1 사이여야 한다.")

#         self.rows = rows
#         self.cols = cols
#         self.room_count = room_count
#         self.min_room_height = min_room_height
#         self.max_room_height = max_room_height
#         self.min_room_width = min_room_width
#         self.max_room_width = max_room_width
#         self.room_padding = room_padding
#         self.corridor_width = corridor_width
#         self.corridor_spacing = corridor_spacing
#         self.preferred_corridor_length = preferred_corridor_length
#         self.connection_randomness = connection_randomness
#         self.extra_connection_probability = extra_connection_probability
#         self.max_extra_connections = max_extra_connections
#         self.allow_corridor_intersections = allow_corridor_intersections
#         self.max_room_attempts = max_room_attempts
#         self.generation_retries = generation_retries
#         self.random = Random(seed)

#     def generate(self) -> GeneratedDungeon:
#         """던전 하나를 생성한다."""
#         last_error: Optional[Exception] = None

#         for _ in range(self.generation_retries):
#             try:
#                 return self._generate_once()
#             except RuntimeError as error:
#                 last_error = error

#         raise RuntimeError(f"던전 생성에 실패했다: {last_error}")

#     def _generate_once(self) -> GeneratedDungeon:
#         grid = self._create_filled_map(WALL)
#         rooms = self._generate_rooms()

#         if len(rooms) < self.room_count:
#             raise RuntimeError("충분한 방을 배치하지 못했다.")

#         for room in rooms:
#             self._carve_room(grid, room)

#         edges = self._generate_and_carve_room_graph(grid, rooms)

#         start_room_id, exit_room_id = self._find_graph_diameter_rooms(rooms, edges)
#         start_position = self._place_special_tile(grid, rooms[start_room_id], START)
#         exit_position = self._place_special_tile(grid, rooms[exit_room_id], EXIT)

#         if not self._validate_walkable_connectivity(grid, start_position, exit_position):
#             raise RuntimeError("생성된 던전의 이동 가능 영역이 완전히 연결되지 않았다.")

#         return GeneratedDungeon(
#             grid=grid,
#             rooms=rooms,
#             edges=edges,
#             start_position=start_position,
#             exit_position=exit_position,
#             start_room_id=start_room_id,
#             exit_room_id=exit_room_id,
#         )

#     def _create_filled_map(self, value: int) -> MapGrid:
#         return [[value for _ in range(self.cols)] for _ in range(self.rows)]

#     def _generate_rooms(self) -> List[Room]:
#         """큰 맵 안에 겹치지 않고 충분히 떨어진 직사각형 방들을 랜덤하게 배치한다."""
#         rooms: List[Room] = []

#         for _ in range(self.max_room_attempts):
#             if len(rooms) >= self.room_count:
#                 break

#             height = self.random.randint(self.min_room_height, self.max_room_height)
#             width = self.random.randint(self.min_room_width, self.max_room_width)

#             top = self.random.randint(2, self.rows - height - 3)
#             left = self.random.randint(2, self.cols - width - 3)

#             new_room = Room(
#                 id=len(rooms),
#                 top=top,
#                 left=left,
#                 height=height,
#                 width=width,
#             )

#             if any(new_room.overlaps(room, padding=self.room_padding) for room in rooms):
#                 continue

#             rooms.append(new_room)

#         return rooms

#     def _carve_room(self, grid: MapGrid, room: Room) -> None:
#         """방 내부를 ROOM_FLOOR로 판다."""
#         for row in range(room.top, room.bottom + 1):
#             for col in range(room.left, room.right + 1):
#                 grid[row][col] = ROOM_FLOOR

#     def _generate_and_carve_room_graph(self, grid: MapGrid, rooms: List[Room]) -> List[RoomEdge]:
#         """
#         방 연결 그래프를 만들고, 동시에 복도를 판다.

#         보장 사항:
#         - 모든 방은 하나의 연결된 그래프에 포함된다.
#         - 같은 두 방 사이의 edge는 하나만 존재한다.
#         - 복도는 직선 구간만 사용한다.
#         - 복도끼리 겹치거나 교차하지 않도록 후보를 제한한다.
#         - 기본적으로 추가 연결을 만들지 않아 얽힘을 줄인다.
#         """
#         edges: Set[RoomEdge] = set()
#         connected: Set[int] = {self.random.randrange(len(rooms))}
#         unconnected: Set[int] = set(range(len(rooms))) - connected

#         while unconnected:
#             preferred_plans: List[Tuple[int, CorridorPlan]] = []
#             fallback_plans: List[Tuple[int, CorridorPlan]] = []

#             for connected_id in connected:
#                 for unconnected_id in unconnected:
#                     edge = self._normalize_edge(connected_id, unconnected_id)
#                     if edge in edges:
#                         continue

#                     distance = self._room_distance(rooms[connected_id], rooms[unconnected_id])
#                     plan = self._plan_corridor(grid, rooms[connected_id], rooms[unconnected_id])
#                     if plan is None:
#                         continue

#                     if distance <= self.preferred_corridor_length:
#                         preferred_plans.append((distance, plan))
#                     else:
#                         fallback_plans.append((distance, plan))

#             candidate_plans = preferred_plans if preferred_plans else fallback_plans

#             if not candidate_plans:
#                 raise RuntimeError("연결 가능한 비교차 직선 복도 후보를 찾지 못했다.")

#             candidate_plans.sort(key=lambda item: item[0])
#             candidate_count = min(self.connection_randomness, len(candidate_plans))
#             _, selected_plan = self.random.choice(candidate_plans[:candidate_count])

#             self._carve_corridor_plan(grid, selected_plan)
#             selected_edge = self._normalize_edge(selected_plan.room_a_id, selected_plan.room_b_id)
#             edges.add(selected_edge)

#             connected.add(selected_plan.room_a_id)
#             connected.add(selected_plan.room_b_id)
#             unconnected.discard(selected_plan.room_a_id)
#             unconnected.discard(selected_plan.room_b_id)

#         self._add_optional_extra_connections(grid, rooms, edges)
#         return sorted(edges)

#     def _add_optional_extra_connections(
#         self,
#         grid: MapGrid,
#         rooms: List[Room],
#         edges: Set[RoomEdge],
#     ) -> None:
#         """낮은 확률로 추가 연결을 만든다. 기본값에서는 실행되지 않는다."""
#         if self.extra_connection_probability <= 0:
#             return

#         max_extra = (
#             self.max_extra_connections
#             if self.max_extra_connections is not None
#             else max(1, len(rooms) // 10)
#         )

#         if max_extra <= 0:
#             return

#         extra_candidates: List[Tuple[int, int, int]] = []

#         for room_a_id in range(len(rooms)):
#             for room_b_id in range(room_a_id + 1, len(rooms)):
#                 edge = self._normalize_edge(room_a_id, room_b_id)
#                 if edge in edges:
#                     continue

#                 distance = self._room_distance(rooms[room_a_id], rooms[room_b_id])
#                 if distance > self.preferred_corridor_length:
#                     continue
#                 extra_candidates.append((distance, room_a_id, room_b_id))

#         extra_candidates.sort(key=lambda item: item[0])
#         candidate_limit = min(len(extra_candidates), len(rooms) * 2)

#         extra_count = 0
#         for _, room_a_id, room_b_id in extra_candidates[:candidate_limit]:
#             if extra_count >= max_extra:
#                 break

#             if self.random.random() > self.extra_connection_probability:
#                 continue

#             plan = self._plan_corridor(grid, rooms[room_a_id], rooms[room_b_id])
#             if plan is None:
#                 continue

#             self._carve_corridor_plan(grid, plan)
#             edges.add(self._normalize_edge(room_a_id, room_b_id))
#             extra_count += 1

#     def _plan_corridor(self, grid: MapGrid, room_a: Room, room_b: Room) -> Optional[CorridorPlan]:
#         """
#         두 방 사이의 복도 계획을 만든다.

#         후보:
#         1. 가로 먼저, 세로 나중: horizontal-first ㄱ자 복도
#         2. 세로 먼저, 가로 나중: vertical-first ㄱ자 복도

#         두 방이 같은 가로/세로 축에 있으면 결과적으로 일자 복도가 된다.
#         """
#         candidates: List[CorridorPlan] = []

#         horizontal_first = self._make_l_corridor_plan(room_a, room_b, horizontal_first=True)
#         if horizontal_first is not None and self._is_corridor_plan_clear(
#             grid, horizontal_first, allow_existing_corridor=False
#         ):
#             candidates.append(horizontal_first)

#         vertical_first = self._make_l_corridor_plan(room_a, room_b, horizontal_first=False)
#         if vertical_first is not None and self._is_corridor_plan_clear(
#             grid, vertical_first, allow_existing_corridor=False
#         ):
#             candidates.append(vertical_first)

#         if candidates:
#             return self.random.choice(candidates)

#         # 엄격 조건으로는 후보가 없을 때만 기존 복도와의 교차/합류를 허용한다.
#         # 방 내부 관통은 여전히 금지된다.
#         if not self.allow_corridor_intersections:
#             return None

#         relaxed_candidates: List[CorridorPlan] = []

#         if horizontal_first is not None and self._is_corridor_plan_clear(
#             grid, horizontal_first, allow_existing_corridor=True
#         ):
#             relaxed_candidates.append(horizontal_first)

#         if vertical_first is not None and self._is_corridor_plan_clear(
#             grid, vertical_first, allow_existing_corridor=True
#         ):
#             relaxed_candidates.append(vertical_first)

#         if not relaxed_candidates:
#             return None

#         return self.random.choice(relaxed_candidates)

#     def _make_l_corridor_plan(
#         self,
#         room_a: Room,
#         room_b: Room,
#         horizontal_first: bool,
#     ) -> Optional[CorridorPlan]:
#         """직선 구간으로만 이루어진 복도 계획을 만든다."""
#         if horizontal_first:
#             door_a, outside_a = self._horizontal_door_from_to(room_a, room_b)
#             door_b, outside_b = self._vertical_door_from_to(room_b, room_a)
#             turn = (outside_a[0], outside_b[1])
#             centerline = self._line_positions(outside_a, turn) + self._line_positions(turn, outside_b)[1:]
#             orientation_a = "vertical"
#             orientation_b = "horizontal"
#         else:
#             door_a, outside_a = self._vertical_door_from_to(room_a, room_b)
#             door_b, outside_b = self._horizontal_door_from_to(room_b, room_a)
#             turn = (outside_b[0], outside_a[1])
#             centerline = self._line_positions(outside_a, turn) + self._line_positions(turn, outside_b)[1:]
#             orientation_a = "horizontal"
#             orientation_b = "vertical"

#         if not centerline:
#             return None

#         return CorridorPlan(
#             room_a_id=room_a.id,
#             room_b_id=room_b.id,
#             door_a=door_a,
#             door_b=door_b,
#             door_a_orientation=orientation_a,
#             door_b_orientation=orientation_b,
#             centerline=centerline,
#         )

#     def _horizontal_door_from_to(self, source: Room, target: Room) -> Tuple[Position, Position]:
#         """source에서 target 방향으로 좌/우 문과 문 바깥 좌표를 잡는다."""
#         target_row, target_col = target.center
#         door_row = self._clamp(target_row, source.top + 2, source.bottom - 2)

#         if target_col >= source.center[1]:
#             door = (door_row, source.right)
#             outside = (door_row, source.right + 1)
#         else:
#             door = (door_row, source.left)
#             outside = (door_row, source.left - 1)

#         return door, outside

#     def _vertical_door_from_to(self, source: Room, target: Room) -> Tuple[Position, Position]:
#         """source에서 target 방향으로 상/하 문과 문 바깥 좌표를 잡는다."""
#         target_row, target_col = target.center
#         door_col = self._clamp(target_col, source.left + 2, source.right - 2)

#         if target_row >= source.center[0]:
#             door = (source.bottom, door_col)
#             outside = (source.bottom + 1, door_col)
#         else:
#             door = (source.top, door_col)
#             outside = (source.top - 1, door_col)

#         return door, outside

#     def _line_positions(self, start: Position, end: Position) -> List[Position]:
#         """가로 또는 세로 직선 좌표 목록을 만든다."""
#         start_row, start_col = start
#         end_row, end_col = end

#         if start_row == end_row:
#             col_start = min(start_col, end_col)
#             col_end = max(start_col, end_col)
#             return [(start_row, col) for col in range(col_start, col_end + 1)]

#         if start_col == end_col:
#             row_start = min(start_row, end_row)
#             row_end = max(start_row, end_row)
#             return [(row, start_col) for row in range(row_start, row_end + 1)]

#         raise ValueError("직선 좌표는 가로 또는 세로일 때만 만들 수 있다.")

#     def _is_corridor_plan_clear(
#         self,
#         grid: MapGrid,
#         plan: CorridorPlan,
#         allow_existing_corridor: bool = False,
#     ) -> bool:
#         """
#         복도 계획이 다른 방이나 기존 복도와 충돌하지 않는지 검사한다.

#         이번 버전의 핵심:
#         - ROOM_FLOOR 침범 금지
#         - 기존 DOOR 침범 금지
#         - 기존 CORRIDOR와 겹침/교차 금지
#         - corridor_spacing 범위 안에 기존 복도가 있으면 금지
#         - 단, 이번 계획에서 새로 만들 두 문 위치는 허용
#         """
#         allowed_door_positions = set()
#         allowed_door_positions.update(
#             self._doorway_positions(plan.door_a, plan.door_a_orientation)
#         )
#         allowed_door_positions.update(
#             self._doorway_positions(plan.door_b, plan.door_b_orientation)
#         )

#         corridor_radius = self.corridor_width // 2
#         spacing_radius = corridor_radius + self.corridor_spacing

#         for center_row, center_col in plan.centerline:
#             if not self._is_inside_inner_map(center_row, center_col):
#                 return False

#             for row in range(center_row - spacing_radius, center_row + spacing_radius + 1):
#                 for col in range(center_col - spacing_radius, center_col + spacing_radius + 1):
#                     if not self._is_inside_inner_map(row, col):
#                         return False

#                     position = (row, col)
#                     tile = grid[row][col]

#                     if position in allowed_door_positions:
#                         continue

#                     # 복도 실제 폭 내부에서는 방/문/기존 복도 모두 금지한다.
#                     inside_corridor_width = (
#                         abs(row - center_row) <= corridor_radius
#                         and abs(col - center_col) <= corridor_radius
#                     )

#                     if inside_corridor_width:
#                         if tile in {ROOM_FLOOR, DOOR, START, EXIT}:
#                             return False
#                         if tile == CORRIDOR and not allow_existing_corridor:
#                             return False

#                     # 복도 주변 여유 범위에서는 기존 문과 특수 타일은 항상 피한다.
#                     if tile in {DOOR, START, EXIT}:
#                         return False

#                     # 엄격 모드에서는 복도 주변의 기존 복도도 피한다.
#                     if tile == CORRIDOR and not allow_existing_corridor:
#                         return False

#         return True

#     def _carve_corridor_plan(self, grid: MapGrid, plan: CorridorPlan) -> None:
#         """복도 계획에 따라 문과 복도를 실제 맵에 반영한다."""
#         self._carve_doorway(grid, plan.door_a, plan.door_a_orientation)
#         self._carve_doorway(grid, plan.door_b, plan.door_b_orientation)

#         for row, col in plan.centerline:
#             self._carve_corridor_tile(grid, row, col)

#     def _carve_corridor_tile(self, grid: MapGrid, center_row: int, center_col: int) -> None:
#         """복도 한 칸을 corridor_width만큼 넓게 판다."""
#         radius = self.corridor_width // 2

#         for row in range(center_row - radius, center_row + radius + 1):
#             for col in range(center_col - radius, center_col + radius + 1):
#                 if not self._is_inside_inner_map(row, col):
#                     continue

#                 # 방 내부와 특수 타일은 복도 타일로 덮어쓰지 않는다.
#                 if grid[row][col] in {ROOM_FLOOR, DOOR, START, EXIT}:
#                     continue

#                 grid[row][col] = CORRIDOR

#     def _carve_doorway(self, grid: MapGrid, center: Position, orientation: str) -> None:
#         """복도 폭에 맞춰 문을 만든다."""
#         for row, col in self._doorway_positions(center, orientation):
#             if self._is_inside_inner_map(row, col):
#                 grid[row][col] = DOOR

#     def _doorway_positions(self, center: Position, orientation: str) -> List[Position]:
#         """문 중심과 방향을 바탕으로 문 좌표 목록을 만든다."""
#         radius = self.corridor_width // 2
#         center_row, center_col = center

#         if orientation == "vertical":
#             return [
#                 (center_row + offset, center_col)
#                 for offset in range(-radius, radius + 1)
#             ]

#         if orientation == "horizontal":
#             return [
#                 (center_row, center_col + offset)
#                 for offset in range(-radius, radius + 1)
#             ]

#         raise ValueError("orientation은 vertical 또는 horizontal이어야 한다.")

#     def _place_special_tile(self, grid: MapGrid, room: Room, tile: int) -> Position:
#         """START 또는 EXIT를 특정 방 내부에 배치한다."""
#         for _ in range(100):
#             row, col = room.random_inner_position(self.random, margin=2)
#             if grid[row][col] == ROOM_FLOOR:
#                 grid[row][col] = tile
#                 return (row, col)

#         row, col = room.center
#         grid[row][col] = tile
#         return (row, col)

#     def _find_graph_diameter_rooms(
#         self,
#         rooms: List[Room],
#         edges: Iterable[RoomEdge],
#     ) -> Tuple[int, int]:
#         """
#         방 그래프에서 가장 멀리 떨어진 두 방을 찾는다.
#         이 두 방을 START 방과 EXIT 방으로 사용한다.
#         """
#         adjacency = self._build_adjacency(len(rooms), edges)

#         best_pair = (0, 0)
#         best_score = (-1, -1)

#         for start_room_id in range(len(rooms)):
#             distances = self._bfs_room_distances(start_room_id, adjacency)

#             for end_room_id, graph_distance in distances.items():
#                 geometric_distance = self._room_distance(
#                     rooms[start_room_id], rooms[end_room_id]
#                 )
#                 score = (graph_distance, geometric_distance)

#                 if score > best_score:
#                     best_score = score
#                     best_pair = (start_room_id, end_room_id)

#         return best_pair

#     def _build_adjacency(
#         self,
#         room_count: int,
#         edges: Iterable[RoomEdge],
#     ) -> List[List[int]]:
#         adjacency = [[] for _ in range(room_count)]

#         for room_a_id, room_b_id in edges:
#             adjacency[room_a_id].append(room_b_id)
#             adjacency[room_b_id].append(room_a_id)

#         return adjacency

#     def _bfs_room_distances(
#         self,
#         start_room_id: int,
#         adjacency: List[List[int]],
#     ) -> Dict[int, int]:
#         distances = {start_room_id: 0}
#         queue = deque([start_room_id])

#         while queue:
#             current_room_id = queue.popleft()

#             for next_room_id in adjacency[current_room_id]:
#                 if next_room_id in distances:
#                     continue

#                 distances[next_room_id] = distances[current_room_id] + 1
#                 queue.append(next_room_id)

#         return distances

#     def _validate_walkable_connectivity(
#         self,
#         grid: MapGrid,
#         start: Position,
#         exit_position: Position,
#     ) -> bool:
#         """
#         생성된 맵의 이동 가능 영역이 하나로 연결되어 있는지 검증한다.

#         True 조건:
#         - START에서 EXIT까지 갈 수 있어야 한다.
#         - 모든 walkable tile이 START에서 도달 가능해야 한다.
#         """
#         queue = deque([start])
#         visited = {start}
#         directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

#         while queue:
#             row, col = queue.popleft()

#             for dr, dc in directions:
#                 next_row = row + dr
#                 next_col = col + dc

#                 if not (0 <= next_row < len(grid) and 0 <= next_col < len(grid[0])):
#                     continue

#                 next_position = (next_row, next_col)

#                 if next_position in visited:
#                     continue

#                 if grid[next_row][next_col] not in WALKABLE_TILES:
#                     continue

#                 visited.add(next_position)
#                 queue.append(next_position)

#         if exit_position not in visited:
#             return False

#         for row_index, row in enumerate(grid):
#             for col_index, tile in enumerate(row):
#                 if tile in WALKABLE_TILES and (row_index, col_index) not in visited:
#                     return False

#         return True

#     def _room_distance(self, room_a: Room, room_b: Room) -> int:
#         return self._manhattan(room_a.center, room_b.center)

#     def _manhattan(self, a: Position, b: Position) -> int:
#         return abs(a[0] - b[0]) + abs(a[1] - b[1])

#     def _normalize_edge(self, room_a_id: int, room_b_id: int) -> RoomEdge:
#         return (
#             (room_a_id, room_b_id)
#             if room_a_id < room_b_id
#             else (room_b_id, room_a_id)
#         )

#     def _clamp(self, value: int, low: int, high: int) -> int:
#         if low > high:
#             return value
#         return max(low, min(value, high))

#     def _is_inside_inner_map(self, row: int, col: int) -> bool:
#         """외벽 한 칸을 제외한 내부 영역인지 확인한다."""
#         return 1 <= row < self.rows - 1 and 1 <= col < self.cols - 1

#     def get_walkable_ratio(self, grid: MapGrid) -> float:
#         """전체 맵에서 이동 가능한 타일 비율을 계산한다."""
#         total_tiles = len(grid) * len(grid[0])
#         walkable_tiles = sum(
#             1 for row in grid for tile in row if tile in WALKABLE_TILES
#         )
#         return walkable_tiles / total_tiles

#     def get_floor_ratio(self, grid: MapGrid) -> float:
#         """이전 코드와의 호환을 위한 별칭."""
#         return self.get_walkable_ratio(grid)


# def is_walkable(tile: int) -> bool:
#     """해당 타일이 이동 가능한 타일인지 확인한다."""
#     return tile in WALKABLE_TILES


# def map_to_string(grid: MapGrid) -> str:
#     """
#     전체 맵을 문자열로 바꾼다.

#     # : 벽
#     . : 방 내부
#     = : 복도
#     + : 문
#     S : 시작 위치
#     E : 종료 위치
#     """
#     symbols = {
#         WALL: "#",
#         ROOM_FLOOR: ".",
#         CORRIDOR: "=",
#         DOOR: "+",
#         START: "S",
#         EXIT: "E",
#     }

#     return "\n".join(
#         "".join(symbols.get(tile, "?") for tile in row)
#         for row in grid
#     )


# def viewport_to_string(
#     grid: MapGrid,
#     center: Position,
#     viewport_rows: int = 45,
#     viewport_cols: int = 80,
# ) -> str:
#     """
#     전체 맵 중 일부만 잘라 문자열로 만든다.

#     나중에 main.py에서 Pygame 카메라/시야 시스템을 만들 때도
#     비슷한 개념을 사용하면 된다.
#     """
#     rows = len(grid)
#     cols = len(grid[0])
#     center_row, center_col = center

#     top = center_row - viewport_rows // 2
#     left = center_col - viewport_cols // 2

#     top = max(0, min(top, rows - viewport_rows))
#     left = max(0, min(left, cols - viewport_cols))

#     bottom = min(rows, top + viewport_rows)
#     right = min(cols, left + viewport_cols)

#     sliced_grid = [row[left:right] for row in grid[top:bottom]]
#     return map_to_string(sliced_grid)


# def save_map_to_txt(grid: MapGrid, filename: str = "generated_dungeon.txt") -> None:
#     """생성된 전체 맵을 txt 파일로 저장한다."""
#     with open(filename, "w", encoding="utf-8") as file:
#         file.write(map_to_string(grid))


# if __name__ == "__main__":
#     generator = MapGenerator(
#         rows=130,
#         cols=180,
#         room_count=26,
#         min_room_height=8,
#         max_room_height=17,
#         min_room_width=11,
#         max_room_width=25,
#         room_padding=3,
#         corridor_width=3,
#         corridor_spacing=0,
#         preferred_corridor_length=48,
#         connection_randomness=2,
#         extra_connection_probability=0.0,
#         max_extra_connections=0,
#         allow_corridor_intersections=True,
#         seed=None,  # None이면 실행할 때마다 다른 맵이 나온다.
#     )

#     dungeon = generator.generate()

#     print("=== Dungeon Summary ===")
#     print(f"Map size: {len(dungeon.grid)} x {len(dungeon.grid[0])}")
#     print(f"Room count: {len(dungeon.rooms)}")
#     print(f"Room graph edge count: {len(dungeon.edges)}")
#     print(f"Start room: {dungeon.start_room_id}, position: {dungeon.start_position}")
#     print(f"Exit room: {dungeon.exit_room_id}, position: {dungeon.exit_position}")
#     print(f"Walkable ratio: {generator.get_walkable_ratio(dungeon.grid):.2%}")

#     print("\n=== Start Viewport Preview ===")
#     print(viewport_to_string(dungeon.grid, dungeon.start_position))

#     save_map_to_txt(dungeon.grid, "generated_dungeon.txt")
#     print("\nFull map saved to generated_dungeon.txt")
