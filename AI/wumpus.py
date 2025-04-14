import heapq
import random

class WumpusWorld:
    def __init__(self):
        # Визначаємо карту печери: кожна кімната має 3 сусідні кімнати (додекаедр)
        self.rooms = {
            1: [2, 5, 8], 2: [1, 3, 10], 3: [2, 4, 12], 4: [3, 5, 14], 5: [1, 4, 6],
            6: [5, 7, 15], 7: [6, 8, 17], 8: [1, 7, 9], 9: [8, 10, 18], 10: [2, 9, 11],
            11: [10, 12, 19], 12: [3, 11, 13], 13: [12, 14, 20], 14: [4, 13, 15],
            15: [6, 14, 16], 16: [15, 17, 20], 17: [7, 16, 18], 18: [9, 17, 19],
            19: [11, 18, 20], 20: [13, 16, 19]
        }

        # Випадково розміщуємо Вампуса, ями та кажанів
        self.wumpus = random.choice(list(self.rooms.keys()))
        self.pits = random.sample([r for r in self.rooms if r != self.wumpus], 2)
        self.bats = random.sample([r for r in self.rooms if r not in self.pits and r != self.wumpus], 2)

        # Вибираємо початкову позицію агента так, щоб вона була безпечною
        self.agent = random.choice([r for r in self.rooms if r not in self.pits and r != self.wumpus and r not in self.bats])
        self.arrows = 5
        self.visited = set()
        print(f"Game initialized: Wumpus at {self.wumpus}, Pits at {self.pits}, Bats at {self.bats}, Agent at {self.agent}")

    def perceive(self):
        # Агент отримує підказки про небезпеку навколо
        perceptions = []
        if any(adj in self.pits for adj in self.rooms[self.agent]):
            perceptions.append("breeze")
        if any(adj in self.bats for adj in self.rooms[self.agent]):
            perceptions.append("bat noises")
        if any(adj == self.wumpus for adj in self.rooms[self.agent]):
            perceptions.append("stench")
        return perceptions

    def heuristic(self, current_room, goal_room):
        # Евристика оцінює відстань і наявність небезпеки
        danger_score = sum([
            3 if current_room in self.pits else 0,
            2 if current_room in self.bats else 0,
            5 if current_room == self.wumpus else 0
        ])
        return abs(current_room - goal_room) + danger_score

    def a_star(self):
        # Використовуємо алгоритм A* для пошуку шляху
        open_list = []
        closed_list = set()
        came_from = {}
        g_score = {self.agent: 0} #словник, що містить найменшу відому вартість шляху
        # (тобто, скільки кроків або скільки небезпеки було пройдено).
        f_score = {self.agent: self.heuristic(self.agent, self.wumpus)} #словник, що містить евристичну оцінку,
        # яка є сумою реальної вартості шляху та евристичної оцінки небезпеки.


        heapq.heappush(open_list, (f_score[self.agent], self.agent))

        while open_list:
            current_f_score, current_room = heapq.heappop(open_list)

            if current_room == self.wumpus:
                # Відновлюємо шлях, якщо знайдено
                path = []
                while current_room in came_from:
                    path.append(current_room)
                    current_room = came_from[current_room]
                path.reverse()
                return path

            closed_list.add(current_room)

            for neighbor in self.rooms[current_room]:
                if neighbor in closed_list:
                    continue
                tentative_g_score = g_score.get(current_room, float('inf')) + 1

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current_room
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, self.wumpus)
                    heapq.heappush(open_list, (f_score[neighbor], neighbor))

        return []

    def move_agent(self, new_pos):
        # Агент здійснює перехід до нової кімнати
        if new_pos in self.rooms[self.agent]:
            print(f"Agent moves from {self.agent} to {new_pos}")
            self.agent = new_pos
            self.visited.add(new_pos)
            if new_pos in self.bats:
                self.agent = random.choice(list(self.rooms.keys()))
                print("Agent encountered bats and was teleported to", self.agent)

    def shoot_arrow(self, target):
        # Агент стріляє в підозрілу кімнату
        if target in self.rooms[self.agent]:
            self.arrows -= 1
            if target == self.wumpus:
                print("Agent shoots and kills the Wumpus!")
                return "Wumpus killed!"
            print("Agent shoots but misses.")
            return "Missed!"
        return "Cannot shoot there!"

    def run(self):
        # Головний цикл роботи агента
        while True:
            perceptions = self.perceive()
            print(f"Agent at {self.agent}, perceptions: {perceptions}")
            if self.agent == self.wumpus:
                print("Eaten by Wumpus! Game Over.")
                break
            if self.agent in self.pits:
                print("Fell into a pit! Game Over.")
                break
            if "stench" in perceptions and self.arrows > 0:
                print("Agent senses Wumpus nearby! Shooting...")
                result = self.shoot_arrow(random.choice(self.rooms[self.agent]))
                if result == "Wumpus killed!":
                    break
            else:
                path = self.a_star()
                if path:
                    next_room = path[0]
                    print(f"Agent plans to move to {next_room} avoiding dangers.")
                    self.move_agent(next_room)
                else:
                    print("No safe path found! Moving randomly.")
                    self.move_agent(random.choice(self.rooms[self.agent]))

world = WumpusWorld()
world.run()
