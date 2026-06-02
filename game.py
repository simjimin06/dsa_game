# game.py

import pygame

from map_loader import load_random_map
from enemy_ai import (
    move_all_enemies,
    get_enemies_at_position,
    get_total_damage,
)
from leaderboard import calculate_score, add_score, get_top_scores


WALL = -1
FLOOR = 0
EXIT = 2

CELL_SIZE = 16
ROWS = 30
COLS = 60
PANEL_HEIGHT = 110

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
    "text": (245, 245, 245),
    "black": (0, 0, 0),
    "overlay": (10, 10, 10),
}


class Game:
    def __init__(self, player_name="Player"):
        pygame.init()

        self.player_name = player_name
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dungeon Escape")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 24)
        self.big_font = pygame.font.SysFont(None, 48)

        self.running = True
        self.reset_game()

    def reset_game(self):
        map_data = load_random_map()

        self.grid = map_data["grid"]
        self.player_pos = map_data["player_pos"]
        self.exit_pos = map_data["exit_pos"]
        self.items = map_data["items"]
        self.enemies = map_data["enemies"]

        self.max_hp = 100
        self.hp = 100
        self.power = 10
        self.turn_count = 0
        self.items_collected = 0

        self.inventory = {}
        self.undo_stack = []

        self.state = "playing"  # playing, clear, dead
        self.score = None
        self.top_scores = get_top_scores(limit=10)
        self.score_saved = False

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
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

    def in_bounds(self, pos):
        row, col = pos
        return 0 <= row < ROWS and 0 <= col < COLS

    def is_walkable_for_player(self, pos):
        if not self.in_bounds(pos):
            return False

        row, col = pos
        return self.grid[row][col] != WALL

    def try_move_player(self, dr, dc):
        old_pos = self.player_pos
        new_pos = (old_pos[0] + dr, old_pos[1] + dc)

        # 벽이나 맵 밖이면 행동 실패 → turn 증가 X
        if not self.is_walkable_for_player(new_pos):
            return

        turn_actions = []

        self.player_pos = new_pos
        turn_actions.append({
            "type": "move_player",
            "from": old_pos,
            "to": new_pos,
        })

        # 아이템 획득
        if new_pos in self.items:
            item_name = self.items.pop(new_pos)
            self.add_inventory(item_name)
            self.items_collected += 1

            turn_actions.append({
                "type": "collect_item",
                "pos": new_pos,
                "item": item_name,
            })

        self.turn_count += 1

        # 출구 도착이면 enemy 이동 없이 게임 클리어
        if new_pos == self.exit_pos:
            self.undo_stack.append(turn_actions)
            self.finish_game()
            return

        # 적 이동
        enemy_actions = move_all_enemies(
            self.enemies,
            self.grid,
            self.player_pos,
        )
        turn_actions.extend(enemy_actions)

        # 적과 충돌하면 데미지
        damage_action = self.apply_enemy_damage()
        if damage_action is not None:
            turn_actions.append(damage_action)

        self.undo_stack.append(turn_actions)

        if self.hp <= 0:
            self.state = "dead"

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
        if self.inventory.get("potion", 0) <= 0:
            return

        if self.hp >= self.max_hp:
            return

        turn_actions = []

        self.remove_inventory("potion")
        turn_actions.append({
            "type": "use_item",
            "item": "potion",
        })

        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + 30)

        turn_actions.append({
            "type": "hp_change",
            "from": old_hp,
            "to": self.hp,
        })

        self.turn_count += 1

        enemy_actions = move_all_enemies(
            self.enemies,
            self.grid,
            self.player_pos,
        )
        turn_actions.extend(enemy_actions)

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
                item_name = action["item"]

                self.items[pos] = item_name
                self.remove_inventory(item_name)
                self.items_collected = max(0, self.items_collected - 1)

            elif action_type == "move_enemy":
                enemy_id = action["enemy_id"]

                for enemy in self.enemies:
                    if enemy.get("id") == enemy_id:
                        enemy["pos"] = action["from"]
                        break

            elif action_type == "hp_change":
                self.hp = action["from"]

            elif action_type == "use_item":
                self.add_inventory(action["item"])

        self.turn_count = max(0, self.turn_count - 1)

    def add_inventory(self, item_name):
        self.inventory[item_name] = self.inventory.get(item_name, 0) + 1

    def remove_inventory(self, item_name):
        if item_name not in self.inventory:
            return

        self.inventory[item_name] -= 1

        if self.inventory[item_name] <= 0:
            del self.inventory[item_name]

    def finish_game(self):
        self.state = "clear"

        if not self.score_saved:
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
        self.draw_items()
        self.draw_enemies()
        self.draw_player()

        if self.state == "clear":
            self.draw_clear_screen()

        elif self.state == "dead":
            self.draw_dead_screen()

        pygame.display.flip()

    def draw_panel(self):
        panel_rect = pygame.Rect(0, 0, SCREEN_WIDTH, PANEL_HEIGHT)
        pygame.draw.rect(self.screen, COLORS["panel"], panel_rect)

        inventory_text = ", ".join(
            f"{name} x{count}" for name, count in self.inventory.items()
        )

        if not inventory_text:
            inventory_text = "empty"

        lines = [
            f"Player: {self.player_name}   HP: {self.hp}/{self.max_hp}   Power: {self.power}   Turn: {self.turn_count}",
            f"Inventory: {inventory_text}",
            "Move: WASD / Arrow Keys   Undo: U   Use Potion: H   Restart: R   Quit: ESC",
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

    def draw_items(self):
        for pos, item_name in self.items.items():
            r, c = pos

            x = c * CELL_SIZE + CELL_SIZE // 2
            y = PANEL_HEIGHT + r * CELL_SIZE + CELL_SIZE // 2

            pygame.draw.circle(
                self.screen,
                COLORS["item"],
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
                color = COLORS["wagi"]
            else:
                color = COLORS["pugi"]

            pygame.draw.rect(self.screen, color, rect)

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