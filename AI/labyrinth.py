import pygame
import random
import sys
import time
from collections import deque

# Кольори
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
GRAY = (210, 210, 210)
WALL_COLOR = (20, 20, 20)

class Cell:
    """Клас клітинки, що визначає кожну прохідну клітинку на сітці"""
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.visited = False
        # Стіни: Ліва, Права, Верхня, Нижня
        self.walls = [True, True, True, True]

    def get_children(self, grid: list) -> list:
        """Перевіряє, чи має клітинка сусідні невідвідані прохідні клітинки"""
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # Праворуч, Ліворуч, Вниз, Вгору
        children = []

        for x, y in directions:
            # Перевіряє, чи сусідня клітинка знаходиться в межах сітки
            if self.x + x in [len(grid[0]), -1] or self.y + y in [-1, len(grid)]:
                continue

            child = grid[self.y + y][self.x + x]  # Отримуємо дочірню клітинку

            if child.visited:  # Перевіряємо, чи була клітинка вже відвідана
                continue

            children.append(child)

        return children

    def show(self, screen, cell_width: int, cell_height: int):
        """Відображає існуючі стіни клітинки"""
        x = self.x * (cell_width * 2)
        y = self.y * (cell_height * 2)

        # Відображаємо стіни, якщо вони існують
        if self.walls[0]:  # Ліва
            pygame.draw.rect(screen, WALL_COLOR, (x, y, cell_width, cell_height * 3))
        if self.walls[1]:  # Права
            pygame.draw.rect(screen, WALL_COLOR, (x + cell_width * 2, y, cell_width, cell_height * 3))
        if self.walls[2]:  # Верхня
            pygame.draw.rect(screen, WALL_COLOR, (x, y, cell_width * 3, cell_height))
        if self.walls[3]:  # Нижня
            pygame.draw.rect(screen, WALL_COLOR, (x, y + cell_height * 2, cell_width * 3, cell_height))

    def mark(self, screen, cell_width: int, cell_height: int, color=(134, 46, 222)):
        """Позначає поточну клітинку вказаним кольором"""
        x = self.x * (cell_width * 2) + cell_width
        y = self.y * (cell_height * 2) + cell_height
        pygame.draw.rect(screen, color, (x, y, cell_width, cell_height))


def remove_walls(current: Cell, choice: Cell):
    """Видаляє стіну між двома клітинками"""
    if choice.x > current.x:  # Вибір праворуч
        current.walls[1] = False
        choice.walls[0] = False
    elif choice.x < current.x:  # Вибір ліворуч
        current.walls[0] = False
        choice.walls[1] = False
    elif choice.y > current.y:  # Вибір внизу
        current.walls[3] = False
        choice.walls[2] = False
    elif choice.y < current.y:  # Вибір вгорі
        current.walls[2] = False
        choice.walls[3] = False


def corner_fill(screen, grid, cell_width, cell_height):
    """Заповнює 'кути' сітки (через те, що стіни квадратні)"""
    for x in range(len(grid[0]) + 1):
        for y in range(len(grid) + 1):
            pygame.draw.rect(screen, WALL_COLOR,
                             (x * cell_width * 2, y * cell_height * 2,
                              cell_width, cell_height))


def convert_grid_to_binary_maze(grid, width, height):
    """Конвертує сітку клітинок типу Cell у двовимірний масив для алгоритму пошуку шляху"""
    # Створюємо більший масив з урахуванням того, що кожна клітинка Cell займає 2x2 клітинки в бінарному представленні
    maze = [[1 for _ in range(width * 2 + 1)] for _ in range(height * 2 + 1)]

    for y in range(height):
        for x in range(width):
            cell = grid[y][x]
            # Центр клітинки завжди прохідний
            maze[y * 2 + 1][x * 2 + 1] = 0

            # Прибираємо стіни там, де їх немає в оригінальній клітинці
            if not cell.walls[0]:  # Ліва стіна
                maze[y * 2 + 1][x * 2] = 0
            if not cell.walls[1]:  # Права стіна
                maze[y * 2 + 1][x * 2 + 2] = 0
            if not cell.walls[2]:  # Верхня стіна
                maze[y * 2][x * 2 + 1] = 0
            if not cell.walls[3]:  # Нижня стіна
                maze[y * 2 + 2][x * 2 + 1] = 0

    return maze


def generate_maze(width, height, cell_size=15):
    """Генерує лабіринт із вказаними розмірами і повертає його для подальшого вирішення"""
    # Ініціалізація pygame
    pygame.init()

    cell_width = cell_height = cell_size

    # Розрахунок розміру екрана на основі розмірів лабіринту
    screen_width = width * cell_width * 2 + cell_width
    screen_height = height * cell_height * 2 + cell_height

    # Створення екрана
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption('Генератор лабіринту')

    # Створення сітки клітинок
    grid = [[Cell(x, y) for x in range(width)] for y in range(height)]

    # Встановлюємо початкову клітинку та ініціалізуємо стек
    current = grid[0][0]
    stack = []

    # Встановлюємо колір фону
    screen.fill(GRAY)

    # Позначаємо вхід та вихід
    entrance = grid[0][0]
    exit_cell = grid[height-1][width-1]

    # Прапорець для відстеження завершення генерації лабіринту
    maze_complete = False

    # Годинник для контролю частоти кадрів
    clock = pygame.time.Clock()

    # Головний цикл генерації лабіринту
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Заповнюємо фон
        screen.fill(GRAY)

        # Відображаємо всі клітинки
        for row in grid:
            for cell in row:
                cell.show(screen, cell_width, cell_height)

        # Заповнюємо кути
        corner_fill(screen, grid, cell_width, cell_height)

        # Якщо лабіринт не завершено, продовжуємо генерацію
        if not maze_complete:
            current.visited = True
            current.mark(screen, cell_width, cell_height)  # Виділяємо поточну клітинку

            # Отримуємо невідвідані сусідні клітинки
            children = current.get_children(grid)

            if children:
                # Вибираємо випадкову невідвідану сусідню клітинку
                choice = random.choice(children)
                choice.visited = True

                # Додаємо поточну клітинку до стеку
                stack.append(current)

                # Видаляємо стіни між поточною та вибраною клітинками
                remove_walls(current, choice)

                # Переходимо до вибраної клітинки
                current = choice
            elif stack:
                # Якщо немає невідвіданих сусідів, повертаємося назад
                current = stack.pop()
            else:
                # Якщо стек порожній, лабіринт завершено
                maze_complete = True
                # При завершенні генерації, зачекаємо коротку паузу
                time.sleep(1)
                pygame.display.update()

                # Чекаємо, поки користувач натисне пробіл
                waiting_for_space = True
                while waiting_for_space:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                            waiting_for_space = False
                            running = False  # Виходимо з циклу генерації

        # Позначаємо вхід та вихід
        entrance.mark(screen, cell_width, cell_height, color=GREEN)  # Зелений для входу
        exit_cell.mark(screen, cell_width, cell_height, color=RED)  # Червоний для виходу

        # Оновлюємо дисплей
        pygame.display.update()
        clock.tick(60)  # Обмежуємо до 60 кадрів на секунду

    # Перетворюємо сітку клітинок у бінарний лабіринт для вирішення
    binary_maze = convert_grid_to_binary_maze(grid, width, height)

    return binary_maze, screen_width, screen_height


class MazeSolver:
    def __init__(self, maze, screen_width, screen_height, delay=0.1):
        """
        Ініціалізація вирішувача лабіринту

        :param maze: Двовимірний масив, де 1 - стіна, 0 - прохід
        :param screen_width: Ширина екрану
        :param screen_height: Висота екрану
        :param delay: Затримка між кроками алгоритму (для візуалізації)
        """
        self.maze = maze
        self.height = len(maze)
        self.width = len(maze[0])
        self.delay = delay

        # Ініціалізація pygame (уже має бути ініціалізований)
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Пошук шляху в лабіринті")

        # Розраховуємо розмір клітинки
        self.cell_size = min(self.screen_width // self.width, self.screen_height // self.height)

        # Запам'ятовування кадрів для створення GIF
        self.frames = []

        # Знаходимо вхід та вихід у бінарному лабіринті (перша та остання прохідні клітинки у верхньому та нижньому рядках)
        # Шукаємо вхід (перша прохідна клітинка у першому рядку)
        self.start = None
        for x in range(self.width):
            if self.maze[1][x] == 0:
                self.start = (1, x)
                break

        # Шукаємо вихід (остання прохідна клітинка в останньому рядку)
        self.end = None
        for x in range(self.width - 1, -1, -1):
            if self.maze[self.height - 2][x] == 0:
                self.end = (self.height - 2, x)
                break

        # Якщо не знайдено, використовуємо стандартні значення
        if not self.start:
            self.start = (1, 1)
        if not self.end:
            self.end = (self.height - 2, self.width - 2)

        # Матриця для відстеження відвіданих клітинок і відстаней
        self.distance_matrix = [[0 for _ in range(self.width)] for _ in range(self.height)]

    def draw_maze(self, path=None, visited=None):
        """
        Відображення лабіринту та шляху

        :param path: Список координат, що утворюють шлях від початку до кінця
        :param visited: Набір відвіданих координат
        """
        self.screen.fill(WHITE)

        # Малюємо лабіринт
        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(x * self.cell_size, y * self.cell_size,
                                   self.cell_size, self.cell_size)

                # Стіни
                if self.maze[y][x] == 1:
                    pygame.draw.rect(self.screen, BLACK, rect)

                # Відвідані клітинки
                elif visited and (y, x) in visited and (y, x) != self.start and (y, x) != self.end:
                    pygame.draw.rect(self.screen, YELLOW, rect)

                    # Відображення відстані від початку (для візуалізації)
                    if self.distance_matrix[y][x] > 0:
                        font = pygame.font.SysFont(None, 20)
                        dist_text = font.render(str(self.distance_matrix[y][x]), True, BLUE)
                        text_rect = dist_text.get_rect(center=(x * self.cell_size + self.cell_size // 2,
                                                               y * self.cell_size + self.cell_size // 2))
                        self.screen.blit(dist_text, text_rect)

        # Малюємо початкову точку
        start_rect = pygame.Rect(self.start[1] * self.cell_size, self.start[0] * self.cell_size,
                                 self.cell_size, self.cell_size)
        pygame.draw.rect(self.screen, GREEN, start_rect)

        # Малюємо кінцеву точку
        end_rect = pygame.Rect(self.end[1] * self.cell_size, self.end[0] * self.cell_size,
                               self.cell_size, self.cell_size)
        pygame.draw.rect(self.screen, RED, end_rect)

        # Малюємо шлях
        if path:
            for i in range(len(path) - 1):
                # Звертаємо увагу, що координати у формі (row, col), але для малювання потрібно (x, y) = (col, row)
                start_pos = (path[i][1] * self.cell_size + self.cell_size // 2,
                             path[i][0] * self.cell_size + self.cell_size // 2)
                end_pos = (path[i+1][1] * self.cell_size + self.cell_size // 2,
                           path[i+1][0] * self.cell_size + self.cell_size // 2)
                pygame.draw.line(self.screen, GREEN, start_pos, end_pos, 5)

                # Малюємо кружечки у точках шляху (крім початку і кінця)
                if i > 0 and i < len(path) - 1:
                    pygame.draw.circle(self.screen, BLUE, start_pos, self.cell_size // 4)

        # Оновлюємо екран
        pygame.display.flip()

        # Перевіряємо події
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Затримка для візуалізації
        time.sleep(self.delay)

    def bfs(self):
        """
        Алгоритм пошуку в ширину (BFS) для знаходження найкоротшого шляху

        :return: Шлях від початку до кінця або None, якщо шлях не існує
        """
        # Напрямки руху (вгору, вправо, вниз, вліво)
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]

        # Черга для BFS
        queue = deque([self.start])

        # Словник для відстеження попередників
        came_from = {self.start: None}

        # Набір відвіданих клітинок для візуалізації
        visited = set([self.start])

        # Ініціалізація матриці відстаней
        self.distance_matrix = [[0 for _ in range(self.width)] for _ in range(self.height)]
        self.distance_matrix[self.start[0]][self.start[1]] = 1

        # Викликаємо функцію малювання початкового стану
        self.draw_maze(visited=visited)

        while queue:
            current = queue.popleft()

            # Якщо досягли кінця
            if current == self.end:
                # Відновлення шляху від кінця до початку
                path = []
                while current:
                    path.append(current)
                    current = came_from[current]
                path.reverse()  # Перевертаємо для отримання шляху від початку до кінця

                # Фінальна візуалізація шляху
                self.draw_maze(path=path, visited=visited)
                return path

            # Перевіряємо сусідні клітинки
            for dy, dx in directions:
                next_y, next_x = current[0] + dy, current[1] + dx

                # Перевіряємо, чи знаходиться наступна клітинка в межах лабіринту
                if self.height > next_y >= 0 == self.maze[next_y][next_x] and 0 <= next_x < self.width and (next_y, next_x) not in visited:

                    # Додаємо до черги і відмічаємо як відвідану
                    queue.append((next_y, next_x))
                    visited.add((next_y, next_x))
                    came_from[(next_y, next_x)] = current

                    # Оновлюємо матрицю відстаней
                    self.distance_matrix[next_y][next_x] = self.distance_matrix[current[0]][current[1]] + 1

                    # Оновлюємо візуалізацію
                    self.draw_maze(visited=visited)

        # Якщо шлях не знайдено
        return None

    def solve(self):
        """Основний метод для вирішення лабіринту і візуалізації"""
        print("Пошук шляху...")
        path = self.bfs()

        if path:
            print(f"Шлях знайдено! Довжина: {len(path)}")
            # Додаємо додаткову затримку для кінцевого результату
            time.sleep(1)

            # Затемнюємо фон для кращої видимості тексту
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 150))
            self.screen.blit(overlay, (0, 0))
            pygame.display.flip()
        else:
            print("Шлях не знайдено!")

        # Чекаємо, поки користувач закриє вікно
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

        pygame.quit()


def main():
    """Головна функція для запуску додатка"""
    # Стандартні розміри
    default_width = 10
    default_height = 8
    default_cell_size = 20
    default_delay = 0.05  # Стандартна затримка візуалізації

    # Отримуємо користувацькі розміри, якщо вони надані
    if len(sys.argv) > 2:
        try:
            width = int(sys.argv[1])
            height = int(sys.argv[2])

            # Переконуємося, що розміри додатні
            if width <= 0 or height <= 0:
                print("Розміри повинні бути додатними цілими числами.")
                return

            # Опціональний параметр розміру клітинки
            cell_size = default_cell_size
            if len(sys.argv) > 3:
                cell_size = int(sys.argv[3])
                if cell_size <= 0:
                    print("Розмір клітинки повинен бути додатнім цілим числом.")
                    return
        except ValueError:
            print("Будь ласка, вкажіть коректні цілі числа для розмірів.")
            return
    else:
        # Використовуємо стандартні розміри
        width = default_width
        height = default_height
        cell_size = default_cell_size

    print(f"Генерація лабіринту з розмірами {width}x{height} та розміром клітинки {cell_size}")

    # Крок 1: Генеруємо лабіринт
    maze, screen_width, screen_height = generate_maze(width, height, cell_size)

    # Крок 2: Запускаємо алгоритм пошуку шляху
    print("Лабіринт згенеровано! Переходимо до пошуку шляху...")

    # Створюємо і запускаємо вирішувач лабіринту
    solver = MazeSolver(maze, screen_width, screen_height, delay=default_delay)
    solver.solve()


if __name__ == "__main__":
    main()