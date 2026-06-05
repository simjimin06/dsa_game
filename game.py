# game.py

from inventory import Inventory
from copy import deepcopy
from collections import deque

import pygame

from map_loader import load_valid_random_map
from enemy_ai import (
    move_all_enemies,
    get_enemies_at_position,
    get_total_damage,
)

# Detection range constants.
# If enemy_ai.py already defines these values, use them.
# If not, use default values here to prevent import errors.
try:
    from enemy_ai import WAGI_DETECTION_RANGE, PUGI_DETECTION_RANGE
except ImportError:
    WAGI_DETECTION_RANGE = 6
    PUGI_DETECTION_RANGE = 8

from leaderboard import calculate_score, add_score, get_top_scores


WALL = -1
FLOOR = 0
EXIT = 2

CELL_SIZE = 24
ROWS = 30
COLS = 60
PANEL_HEIGHT = 130

SCREEN_WIDTH = COLS * CELL_SIZE
SCREEN_HEIGHT = ROWS * CELL_SIZE + PANEL_HEIGHT

FPS = 60

COLORS = {
    "background": (20, 20, 24),
    "panel": (35, 35, 42),
    "wall": (80, 80, 90),
    "floor": (215, 215, 205),
    "exit": (60, 170, 90),
    "player": (40, 100, 220),
    "item": (230, 190, 40),
    "wagi": (210, 60, 60),
    "pugi": (150, 70, 210),
    "arrow": (120, 80, 35),
    "enemy_hp_back": (30, 30, 30),
    "enemy_hp": (60, 200, 90),
    "text": (245, 245, 245),
    "black": (0, 0, 0),
    "overlay": (10, 10, 10),

    "detection_wagi": (150, 90, 90, 95),
    "detection_pugi": (125, 100, 155, 95),
    "detection_overlap": (145, 85, 135, 125),
    "wagi_detection_tile": (150, 85, 85),
    "pugi_detection_tile": (120, 90, 145),

    "ammo": (90, 90, 90),
    "heal": (60, 190, 90),
    "potion": (60, 190, 90),
    "damage_boost": (230, 140, 40),
}


class Game:
    def __init__(self, player_name="Player"):
        pygame.init()

        self.player_name = player_name
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dungeon Escape")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 28)
        self.big_font = pygame.font.SysFont(None, 60)

        self.running = True
        self.reset_game()

    def reset_game(self):
        map_data = load_valid_random_map()

        self.grid = map_data["grid"]
        self.player_pos = map_data["player_pos"]
        self.exit_pos = map_data["exit_pos"]
        self.items = map_data["items"]
        self.enemies = map_data["enemies"]

        self.max_hp = 100
        self.hp = 100
        self.power = 10
        self.attack_range = 8
        self.facing = (0, 1)

        self.turn_count = 0

        # Turn Management:
        # Queue is used to manage the actor order.
        # A valid player action processes the queue in the order:
        # player -> enemy -> player -> enemy ...
        self.turn_queue = deque(["player", "enemy"])

        # Enemy moves once every 2 valid player turns.
        # This makes the game easier while still keeping queue-based turn order.
        self.enemy_move_interval = 2

        self.items_collected = 0
        self.projectiles = []
        self.enemies_defeated = 0

        self.prepare_enemies()

        self.inventory = Inventory({
            "ammo": 3,
        })

        # Undo System:
        # Stack is used to store each valid turn.
        # Each turn contains a list of action records.
        self.undo_stack = []

        self.show_detection_range = False

        self.state = "playing"  # playing, clear, dead
        self.score = None
        self.top_scores = get_top_scores(limit=10)
        self.score_saved = False

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update_projectiles()
            self.draw()

        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            self.running = False
            return

        if key == pygame.K_r:
            self.reset_game()
            return

        if key == pygame.K_b:
            self.show_detection_range = not self.show_detection_range
            return

        if self.state != "playing":
            return

        if key in (pygame.K_UP, pygame.K_w):
            self.try_move_player(-1, 0)

        elif key in (pygame.K_DOWN, pygame.K_s):
            self.try_move_player(1, 0)

        elif key in (pygame.K_LEFT, pygame.K_a):
            self.try_move_player(0, -1)

        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.try_move_player(0, 1)

        elif key == pygame.K_u:
            self.undo()

        elif key == pygame.K_h:
            self.use_potion()

        elif key in (pygame.K_SPACE, pygame.K_f):
            self.attack()

    def prepare_enemies(self):
        for enemy in self.enemies:
            if enemy["type"] == "wagi":
                enemy.setdefault("max_hp", 20)
                enemy.setdefault("hp", enemy["max_hp"])

            elif enemy["type"] == "pugi":
                enemy.setdefault("max_hp", 10)
                enemy.setdefault("hp", enemy["max_hp"])

            else:
                enemy.setdefault("max_hp", 10)
                enemy.setdefault("hp", enemy["max_hp"])

    def in_bounds(self, pos):
        row, col = pos
        return 0 <= row < ROWS and 0 <= col < COLS

    def is_walkable_for_player(self, pos):
        if not self.in_bounds(pos):
            return False

        row, col = pos
        return self.grid[row][col] != WALL

    def normalize_inventory_item(self, item_name):
        """
        Map item symbols/names from the map into inventory item names.
        This keeps old maps using 'potion' compatible with the current 'heal' item.
        """
        if item_name == "potion":
            return "heal"

        return item_name

    def process_turn_queue(self, turn_actions):
        """
        Turn Management using Queue.

        The queue controls actor order:
        player -> enemy -> player -> enemy ...

        This function is called only after a valid player action.
        Invalid actions, such as walking into a wall, do not call this function.
        Therefore, invalid actions do not increase the turn count and do not advance the queue.
        """
        # Player turn finished.
        current_actor = self.turn_queue.popleft()
        self.turn_queue.append(current_actor)

        # Enemy turn.
        current_actor = self.turn_queue.popleft()

        if current_actor == "enemy":
            if self.turn_count % self.enemy_move_interval == 0:
                enemy_actions = move_all_enemies(
                    self.enemies,
                    self.grid,
                    self.player_pos,
                )
                turn_actions.extend(enemy_actions)

        self.turn_queue.append(current_actor)

    def try_move_player(self, dr, dc):
        self.facing = (dr, dc)

        old_pos = self.player_pos
        new_pos = (old_pos[0] + dr, old_pos[1] + dc)

        # Invalid action:
        # If the player tries to move into a wall or outside the map,
        # the position does not change and the turn count does not increase.
        if not self.is_walkable_for_player(new_pos):
            return

        turn_actions = []

        self.player_pos = new_pos
        turn_actions.append({
            "type": "move_player",
            "from": old_pos,
            "to": new_pos,
        })

        # Item collection.
        if new_pos in self.items:
            map_item_name = self.items.pop(new_pos)
            inventory_item_name = self.normalize_inventory_item(map_item_name)

            self.add_inventory(inventory_item_name, 1)
            self.items_collected += 1

            turn_actions.append({
                "type": "collect_item",
                "pos": new_pos,
                "map_item": map_item_name,
                "inventory_item": inventory_item_name,
            })

        self.turn_count += 1

        # If the player reaches the exit, finish the game before enemies move.
        if new_pos == self.exit_pos:
            self.undo_stack.append(turn_actions)
            self.finish_game()
            return

        # Queue-based turn management.
        self.process_turn_queue(turn_actions)

        # Apply damage if an enemy is on the player's position.
        damage_action = self.apply_enemy_damage()
        if damage_action is not None:
            turn_actions.append(damage_action)

        self.undo_stack.append(turn_actions)

        if self.hp <= 0:
            self.state = "dead"

    def attack(self):
        """
        Fire one arrow in the current facing direction.
        Attacking consumes one valid turn.
        """
        if self.inventory.get("ammo", 0) <= 0:
            return

        turn_actions = []

        self.remove_inventory("ammo")
        turn_actions.append({
            "type": "use_item",
            "item": "ammo",
        })

        path, target_enemy = self.make_arrow_attack()

        if path:
            self.projectiles.append({
                "path": path,
                "index": 0,
                "timer": 0,
            })

        turn_actions.append({
            "type": "attack",
            "from": self.player_pos,
            "direction": self.facing,
            "path": path,
            "hit_enemy_id": None if target_enemy is None else target_enemy.get("id"),
        })

        if target_enemy is not None:
            attack_power = self.power

            if self.inventory.get("damage_boost", 0) > 0:
                attack_power += 10
                self.remove_inventory("damage_boost")
                turn_actions.append({
                    "type": "use_item",
                    "item": "damage_boost",
                })

            old_hp = target_enemy.get("hp", target_enemy.get("max_hp", 10))
            new_hp = max(0, old_hp - attack_power)
            target_enemy["hp"] = new_hp

            turn_actions.append({
                "type": "enemy_hp_change",
                "enemy_id": target_enemy.get("id"),
                "from": old_hp,
                "to": new_hp,
            })

            if new_hp <= 0:
                defeated_enemy = deepcopy(target_enemy)
                self.enemies.remove(target_enemy)

                turn_actions.append({
                    "type": "defeat_enemy",
                    "enemy": defeated_enemy,
                })

                old_defeated_count = self.enemies_defeated
                self.enemies_defeated += 1

                turn_actions.append({
                    "type": "enemy_defeated_count_change",
                    "from": old_defeated_count,
                    "to": self.enemies_defeated,
                })

        self.turn_count += 1

        # Queue-based turn management.
        self.process_turn_queue(turn_actions)

        damage_action = self.apply_enemy_damage()
        if damage_action is not None:
            turn_actions.append(damage_action)

        self.undo_stack.append(turn_actions)

        if self.hp <= 0:
            self.state = "dead"

    def make_arrow_attack(self):
        """
        Return the arrow path and the first enemy hit.
        The arrow travels straight until it hits a wall, leaves the map,
        reaches max range, or hits the first enemy.
        """
        dr, dc = self.facing
        row, col = self.player_pos
        path = []

        for _ in range(self.attack_range):
            row += dr
            col += dc
            pos = (row, col)

            if not self.in_bounds(pos):
                break

            if self.grid[row][col] == WALL:
                break

            path.append(pos)

            target_enemy = self.get_enemy_at(pos)
            if target_enemy is not None:
                return path, target_enemy

        return path, None

    def get_enemy_at(self, pos):
        for enemy in self.enemies:
            if enemy["pos"] == pos:
                return enemy

        return None

    def update_projectiles(self):
        alive_projectiles = []

        for projectile in self.projectiles:
            if not projectile["path"]:
                continue

            projectile["timer"] += 1

            if projectile["timer"] >= 3:
                projectile["timer"] = 0
                projectile["index"] += 1

            if projectile["index"] < len(projectile["path"]):
                alive_projectiles.append(projectile)

        self.projectiles = alive_projectiles

    def apply_enemy_damage(self):
        collided_enemies = get_enemies_at_position(self.enemies, self.player_pos)

        if not collided_enemies:
            return None

        damage = get_total_damage(collided_enemies)
        old_hp = self.hp
        self.hp = max(0, self.hp - damage)

        return {
            "type": "hp_change",
            "from": old_hp,
            "to": self.hp,
        }

    def use_potion(self):
        if self.inventory.get("heal", 0) <= 0:
            return

        if self.hp >= self.max_hp:
            return

        turn_actions = []

        self.remove_inventory("heal")
        turn_actions.append({
            "type": "use_item",
            "item": "heal",
        })

        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + 20)

        turn_actions.append({
            "type": "hp_change",
            "from": old_hp,
            "to": self.hp,
        })

        self.turn_count += 1

        # Queue-based turn management.
        self.process_turn_queue(turn_actions)

        damage_action = self.apply_enemy_damage()
        if damage_action is not None:
            turn_actions.append(damage_action)

        self.undo_stack.append(turn_actions)

        if self.hp <= 0:
            self.state = "dead"

    def undo(self):
        if not self.undo_stack:
            return

        last_turn = self.undo_stack.pop()

        for action in reversed(last_turn):
            action_type = action["type"]

            if action_type == "move_player":
                self.player_pos = action["from"]

            elif action_type == "collect_item":
                pos = action["pos"]
                map_item_name = action.get("map_item", action.get("item"))
                inventory_item_name = action.get(
                    "inventory_item",
                    self.normalize_inventory_item(map_item_name)
                )

                self.items[pos] = map_item_name
                self.remove_inventory(inventory_item_name)
                self.items_collected = max(0, self.items_collected - 1)

            elif action_type == "move_enemy":
                enemy_id = action["enemy_id"]

                for enemy in self.enemies:
                    if enemy.get("id") == enemy_id:
                        enemy["pos"] = action["from"]
                        break

            elif action_type == "hp_change":
                self.hp = action["from"]

            elif action_type == "enemy_hp_change":
                enemy_id = action["enemy_id"]

                for enemy in self.enemies:
                    if enemy.get("id") == enemy_id:
                        enemy["hp"] = action["from"]
                        break

            elif action_type == "defeat_enemy":
                enemy_to_restore = deepcopy(action["enemy"])

                if not any(
                    enemy.get("id") == enemy_to_restore.get("id")
                    for enemy in self.enemies
                ):
                    self.enemies.append(enemy_to_restore)
                    self.enemies.sort(key=lambda enemy: enemy.get("id", 0))

            elif action_type == "enemy_defeated_count_change":
                self.enemies_defeated = action["from"]

            elif action_type == "use_item":
                self.add_inventory(action["item"])

        self.turn_count = max(0, self.turn_count - 1)

    def add_inventory(self, item_name, amount=1):
        self.inventory.add(item_name, amount)

    def remove_inventory(self, item_name, amount=1):
        return self.inventory.remove(item_name, amount)

    def finish_game(self):
        self.state = "clear"

        if not self.score_saved:
            try:
                self.score = calculate_score(
                    turn_count=self.turn_count,
                    hp=self.hp,
                    items_collected=self.items_collected,
                    enemies_defeated=self.enemies_defeated,
                )
            except TypeError:
                self.score = calculate_score(
                    turn_count=self.turn_count,
                    hp=self.hp,
                    items_collected=self.items_collected,
                )

            self.top_scores = add_score(
                name=self.player_name,
                score=self.score,
                turns=self.turn_count,
            )

            self.score_saved = True

    def draw(self):
        self.screen.fill(COLORS["background"])

        self.draw_panel()
        self.draw_map()

        if self.show_detection_range:
            self.draw_detection_ranges()

        self.draw_items()
        self.draw_enemies()
        self.draw_player()
        self.draw_projectiles()

        if self.state == "clear":
            self.draw_clear_screen()

        elif self.state == "dead":
            self.draw_dead_screen()

        pygame.display.flip()

    def draw_panel(self):
        panel_rect = pygame.Rect(0, 0, SCREEN_WIDTH, PANEL_HEIGHT)
        pygame.draw.rect(self.screen, COLORS["panel"], panel_rect)

        inventory_text = self.inventory.to_text()

        lines = [
            f"Player: {self.player_name}   HP: {self.hp}/{self.max_hp}   Power: {self.power}   Ammo: {self.inventory.get('ammo', 0)}   Kills: {self.enemies_defeated}   Turn: {self.turn_count}",
            f"Inventory: {inventory_text}",
            "Move: WASD / Arrow Keys   Attack: Space/F   Range: B   Undo: U   Heal: H   Restart: R   Quit: ESC",
        ]

        for i, line in enumerate(lines):
            text = self.font.render(line, True, COLORS["text"])
            self.screen.blit(text, (12, 12 + i * 30))

    def draw_map(self):
        for r in range(ROWS):
            for c in range(COLS):
                value = self.grid[r][c]

                x = c * CELL_SIZE
                y = PANEL_HEIGHT + r * CELL_SIZE

                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

                if value == WALL:
                    color = COLORS["wall"]
                elif value == EXIT:
                    color = COLORS["exit"]
                else:
                    color = COLORS["floor"]

                pygame.draw.rect(self.screen, color, rect)

                pygame.draw.rect(
                    self.screen,
                    COLORS["background"],
                    rect,
                    1,
                )

    def get_wagi_detection_cells(self, start_pos, max_distance):
        visited = {start_pos: 0}
        queue = deque([start_pos])

        while queue:
            row, col = queue.popleft()
            current_distance = visited[(row, col)]

            if current_distance >= max_distance:
                continue

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                next_pos = (row + dr, col + dc)
                nr, nc = next_pos

                if not self.in_bounds(next_pos):
                    continue

                if self.grid[nr][nc] == WALL:
                    continue

                if next_pos in visited:
                    continue

                visited[next_pos] = current_distance + 1
                queue.append(next_pos)

        return visited.keys()

    def get_pugi_detection_cells(self, start_pos, max_distance):
        start_row, start_col = start_pos
        cells = []

        for dr in range(-max_distance, max_distance + 1):
            for dc in range(-max_distance, max_distance + 1):
                if abs(dr) + abs(dc) > max_distance:
                    continue

                pos = (start_row + dr, start_col + dc)

                if not self.in_bounds(pos):
                    continue

                cells.append(pos)

        return cells

    def draw_detection_ranges(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        range_map = {}

        for enemy in self.enemies:
            enemy_type = enemy["type"]
            enemy_pos = enemy["pos"]

            if enemy_type == "wagi":
                detection_cells = self.get_wagi_detection_cells(
                    enemy_pos,
                    WAGI_DETECTION_RANGE
                )

            elif enemy_type == "pugi":
                detection_cells = self.get_pugi_detection_cells(
                    enemy_pos,
                    PUGI_DETECTION_RANGE
                )

            else:
                continue

            for pos in detection_cells:
                if pos not in range_map:
                    range_map[pos] = {
                        "wagi": False,
                        "pugi": False,
                    }

                range_map[pos][enemy_type] = True

        for pos, types in range_map.items():
            r, c = pos

            if types["wagi"] and types["pugi"]:
                color = COLORS["detection_overlap"]
            elif types["wagi"]:
                color = COLORS["detection_wagi"]
            elif types["pugi"]:
                color = COLORS["detection_pugi"]
            else:
                continue

            x = c * CELL_SIZE
            y = PANEL_HEIGHT + r * CELL_SIZE

            rect = pygame.Rect(
                x + 2,
                y + 2,
                CELL_SIZE - 4,
                CELL_SIZE - 4
            )

            pygame.draw.rect(overlay, color, rect)

        self.screen.blit(overlay, (0, 0))

    def draw_items(self):
        for pos, item_name in self.items.items():
            r, c = pos

            x = c * CELL_SIZE + CELL_SIZE // 2
            y = PANEL_HEIGHT + r * CELL_SIZE + CELL_SIZE // 2

            color = COLORS.get(item_name, COLORS["item"])

            pygame.draw.circle(
                self.screen,
                color,
                (x, y),
                CELL_SIZE // 3,
            )

    def draw_enemies(self):
        for enemy in self.enemies:
            r, c = enemy["pos"]

            x = c * CELL_SIZE
            y = PANEL_HEIGHT + r * CELL_SIZE

            rect = pygame.Rect(x + 2, y + 2, CELL_SIZE - 4, CELL_SIZE - 4)

            if enemy["type"] == "wagi":
                if self.show_detection_range:
                    color = COLORS["wagi_detection_tile"]
                else:
                    color = COLORS["wagi"]
            else:
                if self.show_detection_range:
                    color = COLORS["pugi_detection_tile"]
                else:
                    color = COLORS["pugi"]

            pygame.draw.rect(self.screen, color, rect)
            self.draw_enemy_hp_bar(enemy, x, y)

    def draw_enemy_hp_bar(self, enemy, x, y):
        max_hp = max(1, enemy.get("max_hp", 10))
        hp = max(0, enemy.get("hp", max_hp))

        bar_width = CELL_SIZE - 4
        bar_height = 3
        bar_x = x + 2
        bar_y = y

        back_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        hp_rect = pygame.Rect(
            bar_x,
            bar_y,
            int(bar_width * hp / max_hp),
            bar_height,
        )

        pygame.draw.rect(self.screen, COLORS["enemy_hp_back"], back_rect)
        pygame.draw.rect(self.screen, COLORS["enemy_hp"], hp_rect)

    def draw_projectiles(self):
        for projectile in self.projectiles:
            if not projectile["path"]:
                continue

            index = min(projectile["index"], len(projectile["path"]) - 1)
            r, c = projectile["path"][index]

            x = c * CELL_SIZE + CELL_SIZE // 2
            y = PANEL_HEIGHT + r * CELL_SIZE + CELL_SIZE // 2

            pygame.draw.circle(
                self.screen,
                COLORS["arrow"],
                (x, y),
                CELL_SIZE // 4,
            )

    def draw_player(self):
        r, c = self.player_pos

        x = c * CELL_SIZE + CELL_SIZE // 2
        y = PANEL_HEIGHT + r * CELL_SIZE + CELL_SIZE // 2

        pygame.draw.circle(
            self.screen,
            COLORS["player"],
            (x, y),
            CELL_SIZE // 2 - 2,
        )

    def draw_center_message(self, title, subtitle):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        title_text = self.big_font.render(title, True, COLORS["text"])
        subtitle_text = self.font.render(subtitle, True, COLORS["text"])

        self.screen.blit(
            title_text,
            (
                SCREEN_WIDTH // 2 - title_text.get_width() // 2,
                SCREEN_HEIGHT // 2 - 90,
            ),
        )

        self.screen.blit(
            subtitle_text,
            (
                SCREEN_WIDTH // 2 - subtitle_text.get_width() // 2,
                SCREEN_HEIGHT // 2 - 40,
            ),
        )

    def draw_clear_screen(self):
        self.draw_center_message(
            "Dungeon Cleared!",
            f"Score: {self.score}   Press R to restart or ESC to quit",
        )

        y = SCREEN_HEIGHT // 2 + 10
        title = self.font.render("Top Scores", True, COLORS["text"])
        self.screen.blit(
            title,
            (SCREEN_WIDTH // 2 - title.get_width() // 2, y),
        )

        for i, entry in enumerate(self.top_scores[:5]):
            line = (
                f"{entry['rank']}. {entry['name']} "
                f"- {entry['score']} pts / {entry['turns']} turns"
            )
            text = self.font.render(line, True, COLORS["text"])
            self.screen.blit(
                text,
                (SCREEN_WIDTH // 2 - text.get_width() // 2, y + 30 + i * 24),
            )

    def draw_dead_screen(self):
        self.draw_center_message(
            "Game Over",
            "Press R to restart or ESC to quit",
        )