import pygame
import numpy as np
import time
import sys

# Кольори
BACKGROUND_COLOR = (47, 79, 79)  # Темно-бірюзовий
LIVE_COLOR = (0, 255, 0)         # Зелений
DIE_COLOR = (255, 0, 0)          # Червоний
UI_COLOR = (255, 255, 255)       # Білий
UI_BG_COLOR = (25, 25, 25)       # Темно-сірий

class GameOfLife:
    def __init__(self, width=60, height=40, scale=12):
        pygame.init()
        self.width = width
        self.height = height
        self.scale = scale
        self.screen_width = width * scale
        self.screen_height = height * scale

        # Налаштування екрана
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height + 50))
        pygame.display.set_caption("Game of life")

        # Ініціалізація шрифту
        self.font = pygame.font.SysFont('Arial', 16)

        # Налаштування клітинного поля
        self.grid = np.zeros((height, width))
        self.previous_grid = np.zeros((height, width))  # Попередній стан для визначення померлих клітин
        self.generation = 0
        self.pattern_name = "Патерн"
        self.status = "Очікування"

        # Збереження попередніх станів
        self.previous_state = None
        self.cycle_detected = False
        self.stable_detected = False

    def load_pattern(self, pattern_name):
        # Очищення поля перед завантаженням
        self.grid = np.zeros((self.height, self.width))
        self.previous_grid = np.zeros((self.height, self.width))
        self.generation = 0
        self.previous_state = None
        self.cycle_detected = False
        self.stable_detected = False
        self.status = "Очікування"

        # Визначення центру поля
        center_y, center_x = self.height // 2, self.width // 2

        if pattern_name == "blinker":
            # Мигалка - Повертається у початковий стан
            pattern = np.array([
                [0, 0, 0],
                [1, 1, 1],
                [0, 0, 0]
            ])
            self.pattern_name = "Мигалка (циклічний стан, період 2)"

        elif pattern_name == "diehard":
            # Diehard (вимирає через 130 поколінь)
            pattern = np.array([
                [0, 0, 0, 0, 0, 0, 1, 0],
                [1, 1, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 1, 1, 1]
            ])
            self.pattern_name = "Diehard (вимирання популяції)"

        elif pattern_name == "beacon":
            # Маяк
            pattern = np.array([
                [1, 1, 0, 0],
                [1, 0, 0, 0],
                [0, 0, 0, 1],
                [0, 0, 1, 1]
            ])
            self.pattern_name = "Маяк"

        elif pattern_name == "snake":
            # Змія (стійкий стан)
            pattern = np.array([
                [1, 0, 1, 1],
                [1, 1, 0, 1]
            ])
            self.pattern_name = "Змія (стійкий стан)"

        # Розміщення шаблону по центру поля
        y_offset = center_y - pattern.shape[0] // 2
        x_offset = center_x - pattern.shape[1] // 2
        self.grid[y_offset:y_offset + pattern.shape[0],x_offset:x_offset + pattern.shape[1]] = pattern

    def count_neighbors(self, grid, y, x):
        #Підрахунок живих сусідів
        count = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == 0 and j == 0:
                    continue
                # Поле замкнуте, координати обчислюються за модулем розміру поля
                neighbor_y = (y + i) % self.height
                neighbor_x = (x + j) % self.width
                count += grid[neighbor_y, neighbor_x]
        return count

    def update_cells(self):
        self.previous_grid = self.grid.copy() # поточний стан
        new_grid = np.zeros((self.height, self.width)) # нове порожнє поле

        for y in range(self.height):
            for x in range(self.width):
                # Підрахунок живих сусідів з урахуванням замкнутості поля
                neighbors = self.count_neighbors(self.grid, y, x)

                # Правила гри
                if self.grid[y, x] == 1:
                    if neighbors < 2 or neighbors > 3:
                        new_grid[y, x] = 0  # Смерть від самотності або перенаселення
                    else:
                        new_grid[y, x] = 1  # Виживання
                else:
                    if neighbors == 3:
                        new_grid[y, x] = 1  # Народження

        self.check_state(new_grid) # перевірка на стійкий стан або цикл
        return new_grid

    def check_state(self, new_grid):
        # Перевірка на повне вимирання
        if np.sum(new_grid) == 0:
            self.status = "Вимирання популяції"
            return

        # Перевірка на стабільний стан (нове покоління ідентичне поточному)
        if np.array_equal(self.grid, new_grid):
            self.status = "Стійкий стан"
            self.stable_detected = True
            return

        # Перевірка циклу періоду 2
        if self.previous_state is not None:
            if np.array_equal(self.previous_state, new_grid):
                self.status = "Циклічний стан (період 2)"
                self.cycle_detected = True
                return

        # гра триває
        self.previous_state = self.grid.copy()
        self.status = "Розвиток"

    def draw_grid(self):
        #Відображення клітинного поля
        self.screen.fill(BACKGROUND_COLOR)

        # Малюємо клітини
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y, x] == 1:
                    # Жива клітина
                    cell_color = LIVE_COLOR
                else:
                    # Клітина померла на попередньому кроці
                    if self.previous_grid is not None and self.previous_grid[y, x] == 1:
                        cell_color = DIE_COLOR
                    else:
                        # Мертва клітина
                        cell_color = BACKGROUND_COLOR

                pygame.draw.rect(self.screen, cell_color,
                                 (x * self.scale, y * self.scale, self.scale-1, self.scale-1))

        # Малюємо UI панелі
        pygame.draw.rect(self.screen, UI_BG_COLOR, (0, self.screen_height, self.screen_width, 50))

        # Відображення інформації
        generation_text = self.font.render(f"Покоління: {self.generation}", True, UI_COLOR)
        pattern_text = self.font.render(f"Шаблон: {self.pattern_name}", True, UI_COLOR)
        status_text = self.font.render(f"Статус: {self.status}", True, UI_COLOR)
        population_text = self.font.render(f"Популяція: {np.sum(self.grid)}", True, UI_COLOR)

        # Розміщення тексту
        self.screen.blit(generation_text, (10, self.screen_height + 10))
        self.screen.blit(pattern_text, (10, self.screen_height + 30))
        self.screen.blit(status_text, (300, self.screen_height + 10))
        self.screen.blit(population_text, (300, self.screen_height + 30))

        # Оновлення екрана
        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                # Завантаження шаблонів
                if event.key == pygame.K_1:
                    self.load_pattern("beacon")
                elif event.key == pygame.K_2:
                    self.load_pattern("diehard")
                elif event.key == pygame.K_3:
                    self.load_pattern("blinker")
                elif event.key == pygame.K_4:
                    self.load_pattern("snake")
                elif event.key == pygame.K_SPACE: # Один крок вперед
                    self.grid = self.update_cells()
                    self.generation += 1

    def run(self):
        print("\nДОСЛІДЖЕННЯ КЛІТИННИХ АВТОМАТІВ")
        print(" Маяк - 1")
        print(" Diehard - 2")
        print(" Мигалка - 3")
        print(" Змія - 4")
        print("Пробіл - наступне покоління")

        # Відображення початкового стану
        self.draw_grid()

        while True:
            self.handle_events()
            self.draw_grid()
            time.sleep(0.1)


if __name__ == "__main__":
    game = GameOfLife()
    game.run()