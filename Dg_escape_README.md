# Dungeon Escape - Project README

## 1. Project Overview

**Dungeon Escape** is a grid-based dungeon survival game implemented in Python with Pygame.

The player explores a randomly selected dungeon map, collects items, avoids or defeats enemies, and reaches the exit to clear the game.

Main features:
- Tile-based player movement
- Random valid map loading
- Enemy AI with detection ranges
- Inventory system
- Projectile attack system
- Enemy HP and enemy defeat system
- Turn-based action flow
- Undo system
- Score calculation and leaderboard saving

---

## 2. How to Run

### 2.1 Install Pygame

Use the same Python interpreter that will run `main.py`.

```bash
python -m pip install pygame
```

If you use a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install pygame
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install pygame
```

### 2.2 Run the Game

```bash
python main.py
```

On macOS/Linux:

```bash
python3 main.py
```

---

## 3. Controls

| Key | Action |
|---|---|
| `WASD` / Arrow Keys | Move player |
| `Space` / `F` | Attack with projectile |
| `H` | Use heal item |
| `B` | Toggle enemy detection range display |
| `U` | Undo previous valid turn |
| `R` | Restart game |
| `ESC` | Quit game |

---

## 4. Gameplay Rules

### Player

The player starts with:
- 100 HP
- 10 base attack power
- 3 ammo

The player moves one tile at a time. Trying to move into a wall or outside the map is an invalid action and does not consume a turn.

### Turn System

The game uses a queue-based turn system. A valid player action advances the turn order.

Valid player actions include:
- Moving
- Attacking
- Using a heal item

Invalid actions, such as walking into a wall or attacking without ammo, do not consume a turn.

### Attack System

The player attacks in the current facing direction. A projectile travels in a straight line until it:
1. Hits a wall
2. Leaves the map
3. Reaches maximum attack range
4. Hits the first enemy in its path

Attacking consumes 1 ammo.

### Items

There are three item types:

| Item | Effect |
|---|---|
| `ammo` | Adds 1 projectile shot |
| `heal` | Restores 20 HP |
| `damage_boost` | Adds +10 damage to the next attack only |

Item spawn points are written as `I` in map files. When a map is loaded, each `I` is randomly converted into one of the item types. Ammo appears more frequently than the other items.

### Enemies

There are two enemy types:

| Enemy | Description |
|---|---|
| `Wagi` | Ground enemy. Cannot pass through walls. Uses BFS path distance when the player is detected. |
| `Pugi` | Flying enemy. Can pass through walls. Uses Manhattan distance when the player is detected. |

Detection ranges:
- Wagi: 7 tiles
- Pugi: 5 tiles

Outside detection range, enemies move randomly.

Enemy stats:

| Enemy | HP | Damage |
|---|---:|---:|
| Wagi | 20 | 10 |
| Pugi | 10 | 5 |

When an enemy's HP reaches 0, it is removed from the map and the player's kill count increases.

---

## 5. Scoring System

The final score is calculated when the player reaches the exit.

```text
score = 1000 - (turn_count × 5) + (remaining_hp × 2) + (items_collected × 50) + (enemies_defeated × 100)
```

Score factors:
- Fewer turns produce a higher score.
- More remaining HP increases the score.
- More collected items increase the score.
- Defeating enemies gives bonus points.

Leaderboard data is saved in:

```text
data/leaderboard.json
```

---

## 6. Project File Descriptions

### `main.py`

Entry point of the program.

Responsibilities:
- Reads the player name from terminal input
- Creates a `Game` object
- Starts the game loop

---

### `game.py`

Main game controller.

Responsibilities:
- Initializes Pygame
- Stores game state
- Handles keyboard input
- Processes player movement
- Processes attacks and projectiles
- Applies item effects
- Updates enemy movement through the turn system
- Handles undo logic
- Draws the map, player, enemies, items, projectiles, UI panel, clear screen, and game over screen
- Calculates and saves final score

Important systems implemented here:
- Turn queue
- Projectile attack
- Enemy HP bar display
- Detection range overlay
- Undo stack
- Score trigger on game clear

---

### `inventory.py`

Inventory management module.

Responsibilities:
- Stores item counts
- Adds items
- Removes items
- Checks whether an item exists
- Returns item count
- Converts inventory contents into display text

This separates inventory logic from the main game controller.

---

### `map_loader.py`

Map loading and validation module.

Responsibilities:
- Loads map files from the `maps/` directory
- Validates map size and allowed characters
- Converts raw map symbols into game data
- Separates static grid data from dynamic objects
- Randomly selects a valid map
- Uses BFS validation to ensure the exit is reachable

Map symbols:

| Symbol | Meaning |
|---|---|
| `#` | Wall |
| `.` | Floor |
| `P` | Player start |
| `E` | Exit |
| `I` | Item spawn |
| `W` | Wagi enemy |
| `F` | Pugi enemy |

---

### `create_maps.py`

Map generation helper.

Responsibilities:
- Defines room layouts
- Carves rooms and corridors
- Places player, exit, items, and enemies
- Saves generated text maps into the `maps/` directory

This file can regenerate `map1.txt` to `map5.txt`.

---

### `enemy_ai.py`

Enemy movement logic module.

Responsibilities:
- Defines enemy movement directions
- Defines detection ranges
- Handles random enemy movement
- Moves Wagi using BFS distance when the player is detected
- Moves Pugi using Manhattan distance when the player is detected
- Prevents enemies from overlapping each other
- Returns movement action records for the undo system

Algorithm usage:
- Wagi: BFS-based distance map
- Pugi: Manhattan-distance comparison
- Idle state: random movement

---

### `pathfinding.py`

Pathfinding utility module.

Responsibilities:
- Uses BFS to check whether the exit is reachable
- Builds BFS distance maps
- Calculates shortest distance to the exit

This module is used by:
- `map_loader.py` for valid map selection
- `enemy_ai.py` for Wagi movement

---

### `leaderboard.py`

Leaderboard and scoring module.

Responsibilities:
- Calculates final score
- Loads leaderboard data from JSON
- Saves leaderboard data to JSON
- Uses a heap-based ranking method
- Returns top scores

Data file:

```text
data/leaderboard.json
```

---

## 7. Data Structures and Algorithms Used

### Queue

Used for:
- BFS pathfinding
- Enemy distance maps
- Turn order management

### Stack

Used for:
- Undo system

Each valid turn records action data. When the player presses `U`, the most recent turn is popped and reversed.

### Heap

Used for:
- Leaderboard ranking

Python's `heapq` is a min heap, so negative scores are stored to simulate max-heap behavior.

### Dictionary

Used for:
- Inventory item counts
- Item positions
- Enemy data
- Leaderboard entries
- Detection range cell mapping

### BFS

Used for:
- Checking whether the exit is reachable
- Creating Wagi pathfinding distance maps
- Displaying Wagi detection range

### Manhattan Distance

Used for:
- Pugi movement
- Pugi detection range

---

## 8. Folder Structure

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
└─ README.md
```

---

## 9. Module Test Commands

Each module can be run directly for basic testing.

```bash
python map_loader.py
python pathfinding.py
python enemy_ai.py
python leaderboard.py
```

On macOS/Linux:

```bash
python3 map_loader.py
python3 pathfinding.py
python3 enemy_ai.py
python3 leaderboard.py
```

---

## 10. Notes

- All Python files should remain in the same project folder.
- The `maps/` folder must exist and contain `map1.txt` to `map5.txt`.
- The `data/` folder is created automatically when leaderboard data is saved.
- If the project is moved to another computer, install Pygame for the same Python interpreter used to run `main.py`.


---

# Dungeon Escape - 프로젝트 README 한국어 버전

## 1. 프로젝트 개요

**Dungeon Escape**는 Python과 Pygame으로 구현한 격자 기반 던전 생존 게임입니다.

플레이어는 무작위로 선택된 던전 맵을 탐험하면서 아이템을 수집하고, 적을 피하거나 처치하며, 출구에 도달하면 게임을 클리어합니다.

주요 기능은 다음과 같습니다.

* 타일 기반 플레이어 이동
* 무작위 유효 맵 로딩
* 감지 반경을 가진 적 AI
* 인벤토리 시스템
* 투사체 공격 시스템
* 적 HP 및 적 처치 시스템
* 턴 기반 행동 흐름
* 되돌리기 시스템
* 점수 계산 및 리더보드 저장

## 2. 실행 방법

### 2.1 Pygame 설치

`main.py`를 실행할 때 사용할 Python 인터프리터와 같은 환경에 Pygame을 설치해야 합니다.

```bash
python -m pip install pygame
```

### 2.2 게임 실행

```bash
python main.py
```

## 3. 조작 방법

| 키             | 기능               |
| ------------- | ---------------- |
| `WASD` / 방향키  | 플레이어 이동          |
| `Space` / `F` | 투사체 공격           |
| `H`           | 회복 아이템 사용        |
| `B`           | 적 감지 반경 표시 켜기/끄기 |
| `U`           | 이전 유효 턴 되돌리기     |
| `R`           | 게임 재시작           |
| `ESC`         | 게임 종료            |

## 4. 게임 규칙

플레이어는 HP 100, 기본 공격력 10, 탄약 3개를 가지고 시작합니다. 벽이나 맵 밖으로 이동하려는 행동은 유효하지 않은 행동으로 처리되며 턴을 소모하지 않습니다.

공격은 현재 바라보는 방향으로 이루어지며, 투사체는 벽에 부딪히거나 맵 밖으로 나가거나 최대 사거리에 도달하거나 첫 번째 적에게 명중하면 멈춥니다. 공격할 때마다 탄약 1개를 소모합니다.

아이템은 총 세 종류입니다.

| 아이템            | 효과                   |
| -------------- | -------------------- |
| `ammo`         | 투사체 공격 가능 횟수 1회 추가   |
| `heal`         | HP 20 회복             |
| `damage_boost` | 다음 공격 1회에 한해 데미지 +10 |

적은 두 종류입니다.

| 적      | 설명                                                    |
| ------ | ----------------------------------------------------- |
| `Wagi` | 지상 적입니다. 벽을 통과하지 못하며, 플레이어를 감지하면 BFS 기반 경로 거리로 추적합니다. |
| `Pugi` | 비행 적입니다. 벽을 통과할 수 있으며, 플레이어를 감지하면 맨해튼 거리를 기준으로 추적합니다. |

감지 반경은 Wagi가 7칸, Pugi가 5칸입니다. 플레이어가 감지 반경 밖에 있으면 적은 무작위로 이동합니다.

## 5. 점수 시스템

최종 점수는 플레이어가 출구에 도달했을 때 계산됩니다.

```text
score = 1000 - (turn_count × 5) + (remaining_hp × 2) + (items_collected × 50) + (enemies_defeated × 100)
```

턴 수가 적을수록, 남은 HP가 많을수록, 수집한 아이템이 많을수록, 처치한 적이 많을수록 점수가 높아집니다.

## 6. 주요 파일 설명

`main.py`는 프로그램의 시작점이며, 플레이어 이름을 입력받고 `Game` 객체를 생성해 게임을 실행합니다.

`game.py`는 게임 전체를 제어하는 핵심 파일입니다. Pygame 초기화, 키 입력 처리, 이동, 공격, 아이템 사용, 적 이동, 되돌리기, 화면 출력, 점수 계산을 담당합니다.

`inventory.py`는 인벤토리 관리 모듈입니다. 아이템 개수 저장, 추가, 제거, 보유 여부 확인, 화면 표시용 문자열 생성을 담당합니다.

`map_loader.py`는 맵 파일을 불러오고 검증합니다. 텍스트 맵의 기호를 실제 게임 데이터로 변환하고, BFS 검증을 통해 출구에 도달 가능한 맵인지 확인합니다.

`create_maps.py`는 방 구조와 복도를 만들고, 플레이어, 출구, 아이템, 적을 배치하여 `map1.txt`부터 `map5.txt`까지 생성하는 보조 파일입니다.

`enemy_ai.py`는 적 이동 로직을 담당합니다. Wagi는 BFS 거리 맵을 사용하고, Pugi는 맨해튼 거리를 사용합니다.

`pathfinding.py`는 BFS를 사용하여 출구 도달 가능 여부와 최단 거리, 거리 맵 생성을 처리합니다.

`leaderboard.py`는 점수 계산과 리더보드 저장을 담당합니다. 리더보드는 `data/leaderboard.json`에 저장됩니다.

## 7. 사용한 자료구조와 알고리즘

* Queue: BFS 경로 탐색, 거리 맵 생성, 턴 순서 관리
* Stack: 되돌리기 시스템
* Heap: 리더보드 순위 계산
* Dictionary: 인벤토리, 아이템 위치, 적 데이터, 감지 반경 정보 저장
* BFS: 출구 도달 가능 여부 확인, Wagi 이동, Wagi 감지 반경 표시
* Manhattan Distance: Pugi 이동 및 감지 반경 계산

## 8. 폴더 구조

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
└─ README.md
```

## 9. 모듈 테스트 명령어

각 모듈은 직접 실행하여 기본 동작을 테스트할 수 있습니다.

```bash
python map_loader.py
python pathfinding.py
python enemy_ai.py
python leaderboard.py
```

## 10. 참고 사항

모든 Python 파일은 같은 프로젝트 폴더 안에 있어야 합니다. `maps/` 폴더에는 `map1.txt`부터 `map5.txt`까지의 맵 파일이 있어야 합니다. `data/` 폴더는 리더보드 데이터를 저장할 때 자동으로 생성됩니다. 프로젝트를 다른 컴퓨터로 옮길 경우, `main.py`를 실행할 Python 인터프리터에 Pygame을 설치해야 합니다.