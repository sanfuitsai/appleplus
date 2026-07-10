"""
Python 魚菜共生版俄羅斯方塊
需要先安裝 pygame：

pip install pygame

執行方式：
python aquaponics_tetris.py

操作方式：
← →：左右移動
↑：旋轉
↓：加速下降
空白鍵：直接落下
P：暫停 / 繼續
R：重新開始
ESC：離開遊戲

魚菜共生規則：
1. 方塊不只是方塊，也代表魚菜共生系統中的資源。
2. 藍色 / 青色方塊：水循環，可提升水質。
3. 黃色 / 橘色方塊：魚飼料，提升魚健康，但會增加養分與水質壓力。
4. 紫色 / 紅色方塊：魚排泄物，增加養分，但降低水質。
5. 綠色方塊：植物吸收養分，提升植物成長。
6. 消除行數代表系統成功運作，可額外提升水質、植物成長與分數。
7. 水質太低或魚健康歸零，遊戲結束。
8. 植物成長達 100 時會收成一次，獲得額外分數。
"""

import pygame
import random
import sys

# -----------------------------
# 基本設定
# -----------------------------
COLS = 10
ROWS = 20
BLOCK_SIZE = 30
BOARD_WIDTH = COLS * BLOCK_SIZE
BOARD_HEIGHT = ROWS * BLOCK_SIZE
SIDE_WIDTH = 280
SCREEN_WIDTH = BOARD_WIDTH + SIDE_WIDTH
SCREEN_HEIGHT = BOARD_HEIGHT
FPS = 60

# 顏色設定
BLACK = (15, 23, 42)
DARK = (30, 41, 59)
GRID = (51, 65, 85)
WHITE = (248, 250, 252)
GRAY = (148, 163, 184)
CYAN = (34, 211, 238)
BLUE = (59, 130, 246)
ORANGE = (251, 146, 60)
YELLOW = (250, 204, 21)
GREEN = (74, 222, 128)
PURPLE = (168, 85, 247)
RED = (239, 68, 68)
PANEL = (2, 6, 23)

TETROMINOES = {
    "I": {"color": CYAN, "name": "水循環", "matrix": [[1, 1, 1, 1]]},
    "J": {"color": BLUE, "name": "過濾水", "matrix": [[1, 0, 0], [1, 1, 1]]},
    "L": {"color": ORANGE, "name": "魚飼料", "matrix": [[0, 0, 1], [1, 1, 1]]},
    "O": {"color": YELLOW, "name": "魚群能量", "matrix": [[1, 1], [1, 1]]},
    "S": {"color": GREEN, "name": "蔬菜吸收", "matrix": [[0, 1, 1], [1, 1, 0]]},
    "T": {"color": PURPLE, "name": "養分轉化", "matrix": [[0, 1, 0], [1, 1, 1]]},
    "Z": {"color": RED, "name": "廢物累積", "matrix": [[1, 1, 0], [0, 1, 1]]},
}


# -----------------------------
# 工具函式
# -----------------------------
def clamp(value, low=0, high=100):
    return max(low, min(high, value))


# -----------------------------
# 方塊物件
# -----------------------------
class Piece:
    def __init__(self, piece_type=None):
        self.type = piece_type or random.choice(list(TETROMINOES.keys()))
        self.matrix = [row[:] for row in TETROMINOES[self.type]["matrix"]]
        self.color = TETROMINOES[self.type]["color"]
        self.name = TETROMINOES[self.type]["name"]
        self.row = 0
        self.col = COLS // 2 - len(self.matrix[0]) // 2

    def rotate(self):
        """順時針旋轉方塊"""
        return [list(row) for row in zip(*self.matrix[::-1])]


# -----------------------------
# 遊戲主程式
# -----------------------------
class TetrisGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("魚菜共生版俄羅斯方塊")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("microsoftjhenghei", 32)
        self.font = pygame.font.SysFont("microsoftjhenghei", 21)
        self.font_small = pygame.font.SysFont("microsoftjhenghei", 16)
        self.reset()

    def reset(self):
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.current = Piece()
        self.next_piece = Piece()
        self.score = 0
        self.lines = 0
        self.level = 1
        self.paused = False
        self.game_over = False
        self.drop_timer = 0

        # 魚菜共生系統數值
        self.water_quality = 75
        self.fish_health = 80
        self.nutrients = 25
        self.plant_growth = 0
        self.harvest = 0
        self.message = "平衡水質、魚、養分與植物！"

    def drop_speed(self):
        """等級越高，下降越快"""
        return max(100, 760 - (self.level - 1) * 60)

    def is_valid(self, piece, next_row=None, next_col=None, next_matrix=None):
        next_row = piece.row if next_row is None else next_row
        next_col = piece.col if next_col is None else next_col
        next_matrix = piece.matrix if next_matrix is None else next_matrix

        for r, row in enumerate(next_matrix):
            for c, cell in enumerate(row):
                if not cell:
                    continue
                board_row = next_row + r
                board_col = next_col + c

                if board_col < 0 or board_col >= COLS:
                    return False
                if board_row >= ROWS:
                    return False
                if board_row >= 0 and self.board[board_row][board_col] is not None:
                    return False
        return True

    def move(self, delta_col):
        if self.game_over or self.paused:
            return
        if self.is_valid(self.current, next_col=self.current.col + delta_col):
            self.current.col += delta_col

    def rotate_current(self):
        if self.game_over or self.paused:
            return
        rotated = self.current.rotate()

        # 簡易 wall kick：碰牆時嘗試左右微調
        for kick in [0, -1, 1, -2, 2]:
            if self.is_valid(self.current, next_col=self.current.col + kick, next_matrix=rotated):
                self.current.matrix = rotated
                self.current.col += kick
                return

    def soft_drop(self):
        if self.game_over or self.paused:
            return
        if self.is_valid(self.current, next_row=self.current.row + 1):
            self.current.row += 1
        else:
            self.lock_piece()

    def hard_drop(self):
        if self.game_over or self.paused:
            return
        distance = 0
        while self.is_valid(self.current, next_row=self.current.row + 1):
            self.current.row += 1
            distance += 1
        self.score += distance * 2
        self.lock_piece()

    def lock_piece(self):
        """把目前方塊固定到棋盤上，並套用魚菜共生效果"""
        placed_type = self.current.type

        for r, row in enumerate(self.current.matrix):
            for c, cell in enumerate(row):
                if cell:
                    board_row = self.current.row + r
                    board_col = self.current.col + c
                    if 0 <= board_row < ROWS and 0 <= board_col < COLS:
                        # 棋盤儲存的是方塊類型，不是顏色，方便判斷資源效果
                        self.board[board_row][board_col] = placed_type

        self.apply_piece_effect(placed_type)
        cleared = self.clear_lines()

        if cleared > 0:
            self.add_score(cleared)
            self.apply_clear_line_bonus(cleared)

        self.check_ecosystem()
        if not self.game_over:
            self.spawn_piece()

    def apply_piece_effect(self, piece_type):
        """不同方塊代表不同的魚菜共生資源效果"""
        if piece_type in ["I", "J"]:
            # 水循環與過濾水
            self.water_quality += 6
            self.fish_health += 1
            self.nutrients -= 1
            self.message = "水循環改善，水質提升！"

        elif piece_type in ["L", "O"]:
            # 魚飼料與魚群能量
            self.fish_health += 5
            self.nutrients += 6
            self.water_quality -= 2
            self.message = "魚獲得能量，但水質壓力增加。"

        elif piece_type == "S":
            # 植物吸收養分
            absorbed = min(self.nutrients, 8)
            self.nutrients -= absorbed
            self.plant_growth += absorbed * 2
            self.water_quality += 2
            self.message = "植物吸收養分，蔬菜成長！"

        elif piece_type == "T":
            # 養分轉化
            self.nutrients += 5
            self.plant_growth += 3
            self.water_quality -= 2
            self.message = "養分開始轉化，可供植物利用。"

        elif piece_type == "Z":
            # 廢物累積
            self.nutrients += 8
            self.water_quality -= 7
            self.fish_health -= 2
            self.message = "廢物累積，水質下降！需要水循環或植物吸收。"

        # 每放下一個方塊，系統都會有一點自然消耗
        self.water_quality -= 1
        if self.water_quality < 45:
            self.fish_health -= 3
        elif self.water_quality > 70:
            self.fish_health += 1

        self.normalize_ecosystem()
        self.try_harvest()

    def apply_clear_line_bonus(self, cleared):
        """消行代表系統順利循環，給予生態獎勵"""
        self.water_quality += cleared * 4
        self.plant_growth += cleared * 8
        self.score += cleared * 50
        self.message = f"系統循環成功！消除 {cleared} 行，植物加速成長。"
        self.normalize_ecosystem()
        self.try_harvest()

    def try_harvest(self):
        """植物成長達 100 就收成"""
        while self.plant_growth >= 100:
            self.plant_growth -= 100
            self.harvest += 1
            self.score += 500
            self.message = f"蔬菜收成！目前收成 {self.harvest} 次。"

    def normalize_ecosystem(self):
        self.water_quality = clamp(self.water_quality)
        self.fish_health = clamp(self.fish_health)
        self.nutrients = clamp(self.nutrients)
        self.plant_growth = clamp(self.plant_growth)

    def check_ecosystem(self):
        """魚菜共生失衡時遊戲結束"""
        if self.water_quality <= 0:
            self.game_over = True
            self.message = "水質崩壞！遊戲結束，按 R 重新開始。"
        elif self.fish_health <= 0:
            self.game_over = True
            self.message = "魚群健康歸零！遊戲結束，按 R 重新開始。"

    def clear_lines(self):
        """消除已填滿的行"""
        new_board = []
        cleared = 0

        for row in self.board:
            if all(cell is not None for cell in row):
                cleared += 1
            else:
                new_board.append(row)

        while len(new_board) < ROWS:
            new_board.insert(0, [None for _ in range(COLS)])

        self.board = new_board
        self.lines += cleared
        self.level = self.lines // 10 + 1
        return cleared

    def add_score(self, cleared):
        score_table = {1: 100, 2: 300, 3: 500, 4: 800}
        self.score += score_table.get(cleared, cleared * 250) * self.level

    def spawn_piece(self):
        self.current = self.next_piece
        self.next_piece = Piece()

        if not self.is_valid(self.current):
            self.game_over = True
            self.message = "方塊堆滿了！按 R 重新開始。"

    def draw_block(self, x, y, color):
        pygame.draw.rect(self.screen, color, (x, y, BLOCK_SIZE, BLOCK_SIZE), border_radius=6)
        pygame.draw.rect(self.screen, WHITE, (x + 2, y + 2, BLOCK_SIZE - 4, BLOCK_SIZE - 4), 1, border_radius=5)

    def draw_board(self):
        self.screen.fill(BLACK)
        pygame.draw.rect(self.screen, DARK, (0, 0, BOARD_WIDTH, BOARD_HEIGHT))

        # 已固定的方塊
        for r in range(ROWS):
            for c in range(COLS):
                x = c * BLOCK_SIZE
                y = r * BLOCK_SIZE
                pygame.draw.rect(self.screen, GRID, (x, y, BLOCK_SIZE, BLOCK_SIZE), 1)
                cell = self.board[r][c]
                if cell is not None:
                    self.draw_block(x, y, TETROMINOES[cell]["color"])

        # 目前正在掉落的方塊
        if not self.game_over:
            for r, row in enumerate(self.current.matrix):
                for c, cell in enumerate(row):
                    if cell:
                        x = (self.current.col + c) * BLOCK_SIZE
                        y = (self.current.row + r) * BLOCK_SIZE
                        self.draw_block(x, y, self.current.color)

    def draw_text(self, text, x, y, font, color=WHITE):
        image = font.render(text, True, color)
        self.screen.blit(image, (x, y))

    def draw_meter(self, label, value, x, y, color):
        """畫出魚菜共生狀態條"""
        self.draw_text(f"{label}：{int(value)}", x, y, self.font_small, WHITE)
        pygame.draw.rect(self.screen, GRID, (x, y + 22, 200, 14), border_radius=7)
        pygame.draw.rect(self.screen, color, (x, y + 22, int(200 * value / 100), 14), border_radius=7)

    def draw_side_panel(self):
        panel_x = BOARD_WIDTH
        pygame.draw.rect(self.screen, PANEL, (panel_x, 0, SIDE_WIDTH, SCREEN_HEIGHT))

        self.draw_text("魚菜共生方塊", panel_x + 20, 25, self.font_big, WHITE)
        self.draw_text(f"分數：{self.score}", panel_x + 20, 75, self.font, WHITE)
        self.draw_text(f"消行：{self.lines}", panel_x + 20, 105, self.font, WHITE)
        self.draw_text(f"等級：{self.level}", panel_x + 20, 135, self.font, WHITE)
        self.draw_text(f"收成：{self.harvest}", panel_x + 20, 165, self.font, GREEN)

        self.draw_text("生態系統狀態", panel_x + 20, 205, self.font, WHITE)
        self.draw_meter("水質", self.water_quality, panel_x + 20, 240, CYAN)
        self.draw_meter("魚健康", self.fish_health, panel_x + 20, 285, YELLOW)
        self.draw_meter("養分", self.nutrients, panel_x + 20, 330, PURPLE)
        self.draw_meter("植物成長", self.plant_growth, panel_x + 20, 375, GREEN)

        self.draw_text("下一個：", panel_x + 20, 430, self.font, WHITE)
        self.draw_text(self.next_piece.name, panel_x + 110, 430, self.font_small, GRAY)
        self.draw_next_piece(panel_x + 50, 465)

        self.draw_text("規則提示", panel_x + 20, 540, self.font, WHITE)
        tips = [
            "藍/青：提升水質",
            "黃/橘：餵魚但增養分",
            "綠：植物吸收養分",
            "紫/紅：養分多但傷水質",
            "水質太低會傷魚",
        ]
        for i, line in enumerate(tips):
            self.draw_text(line, panel_x + 20, 570 + i * 22, self.font_small, GRAY)

        # 訊息可能很長，簡單分兩行顯示
        self.draw_text(self.message[:18], panel_x + 20, 690, self.font_small, CYAN)
        self.draw_text(self.message[18:36], panel_x + 20, 712, self.font_small, CYAN)

    def draw_next_piece(self, start_x, start_y):
        mini_size = 24
        matrix = self.next_piece.matrix
        color = self.next_piece.color

        for r, row in enumerate(matrix):
            for c, cell in enumerate(row):
                if cell:
                    x = start_x + c * mini_size
                    y = start_y + r * mini_size
                    pygame.draw.rect(self.screen, color, (x, y, mini_size, mini_size), border_radius=5)
                    pygame.draw.rect(self.screen, WHITE, (x + 2, y + 2, mini_size - 4, mini_size - 4), 1, border_radius=4)

    def draw_overlay(self):
        if self.paused or self.game_over:
            overlay = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            self.screen.blit(overlay, (0, 0))

            title = "遊戲暫停" if self.paused else "Game Over"
            hint = "按 P 繼續" if self.paused else "按 R 重新開始"

            title_img = self.font_big.render(title, True, WHITE)
            hint_img = self.font.render(hint, True, CYAN)
            self.screen.blit(title_img, (BOARD_WIDTH // 2 - title_img.get_width() // 2, 250))
            self.screen.blit(hint_img, (BOARD_WIDTH // 2 - hint_img.get_width() // 2, 305))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_r:
                    self.reset()
                elif event.key == pygame.K_p:
                    if not self.game_over:
                        self.paused = not self.paused
                elif event.key == pygame.K_LEFT:
                    self.move(-1)
                elif event.key == pygame.K_RIGHT:
                    self.move(1)
                elif event.key == pygame.K_UP:
                    self.rotate_current()
                elif event.key == pygame.K_DOWN:
                    self.soft_drop()
                elif event.key == pygame.K_SPACE:
                    self.hard_drop()

    def update(self, delta_time):
        if self.game_over or self.paused:
            return

        self.drop_timer += delta_time
        if self.drop_timer >= self.drop_speed():
            self.soft_drop()
            self.drop_timer = 0

    def draw(self):
        self.draw_board()
        self.draw_side_panel()
        self.draw_overlay()
        pygame.display.flip()

    def run(self):
        while True:
            delta_time = self.clock.tick(FPS)
            self.handle_events()
            self.update(delta_time)
            self.draw()


if __name__ == "__main__":
    game = TetrisGame()
    game.run()
