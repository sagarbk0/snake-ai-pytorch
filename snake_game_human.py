import pygame
import random
from enum import Enum
from collections import namedtuple
from pygame._sdl2 import Window, Renderer, Texture

pygame.init()
font = pygame.font.Font('arial.ttf', 25)


class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4


Point = namedtuple('Point', 'x, y')

# rgb colors
WHITE = (255, 255, 255, 255)
RED = (200, 0, 0, 255)
BLUE1 = (0, 0, 255, 255)
BLUE2 = (0, 100, 255, 255)
BLACK = (0, 0, 0, 255)
BLACK_RGB = (0, 0, 0)

BLOCK_SIZE = 20
SPEED = 10


class SnakeGame:

    def __init__(self, w=640, h=480, pygame=pygame, rightPosition=False):
        self.w = w
        self.h = h

        # Create a window using SDL2 API so that it can be used side-by-side with game.py (AI game window)
        win = Window("Snake Human", resizable=True, position=[900, 200])
        renderer = Renderer(win)
        surface = pygame.Surface([w, h])
        surface.fill(BLACK_RGB)
        tex = Texture.from_surface(renderer, surface)

        renderer.clear()
        tex.draw()
        renderer.present()

        renderer.draw_color = BLACK

        self.renderer = renderer
        self.window = win

        self.pygame = pygame
        self.clock = self.pygame.time.Clock()

        # init game state
        self.direction = Direction.RIGHT

        self.head = Point(self.w / 2, self.h / 2)
        self.snake = [self.head,
                      Point(self.head.x - BLOCK_SIZE, self.head.y),
                      Point(self.head.x - (2 * BLOCK_SIZE), self.head.y)]

        self.score = 0
        self.food = None
        self._place_food()

    def _place_food(self):
        x = random.randint(0, (self.w - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
        y = random.randint(0, (self.h - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
        self.food = Point(x, y)
        if self.food in self.snake:
            self._place_food()

    def play_step(self):
        # 1. collect user input
        for event in self.pygame.event.get():
            if event.type == self.pygame.QUIT:
                self.pygame.quit()
                quit()
            if event.type == self.pygame.KEYDOWN:
                if event.key == self.pygame.K_LEFT:
                    self.direction = Direction.LEFT
                elif event.key == self.pygame.K_RIGHT:
                    self.direction = Direction.RIGHT
                elif event.key == self.pygame.K_UP:
                    self.direction = Direction.UP
                elif event.key == self.pygame.K_DOWN:
                    self.direction = Direction.DOWN

        # 2. move
        self._move(self.direction)  # update the head
        self.snake.insert(0, self.head)

        # 3. check if game over
        game_over = False
        if self._is_collision():
            game_over = True
            return game_over, self.score

        # 4. place new food or just move
        if self.head == self.food:
            self.score += 1
            print(f'Human score: {self.score}')
            self._place_food()
        else:
            self.snake.pop()

        # 5. update ui and clock
        self._update_ui()
        self.clock.tick(SPEED)
        # 6. return game over and score
        return game_over, self.score

    def _is_collision(self):
        # hits boundary
        if self.head.x > self.w - BLOCK_SIZE or self.head.x < 0 or self.head.y > self.h - BLOCK_SIZE or self.head.y < 0:
            return True
        # hits itself
        if self.head in self.snake[1:]:
            return True

        return False

    def _update_ui(self):
        # self.display.fill(BLACK)

        self.renderer.clear()

        for pt in self.snake:
            self.renderer.draw_color = BLUE1
            self.renderer.draw_rect(self.pygame.Rect(pt.x, pt.y, BLOCK_SIZE, BLOCK_SIZE))
            self.renderer.draw_color = BLUE2
            self.renderer.fill_rect(self.pygame.Rect(pt.x + 4, pt.y + 4, 12, 12))

        self.renderer.draw_color = RED
        self.renderer.fill_rect(self.pygame.Rect(self.food.x, self.food.y, BLOCK_SIZE, BLOCK_SIZE))

        self.renderer.draw_color = BLACK

        self.renderer.present()

        # Unsuccesfully attempted to add text to SDL surface:
        # text = font.render("Score: " + str(self.score), True, WHITE)
        # image = pygame.image.frombuffer(f"Score: {str(self.score)}", [10,10], 'RGB', True)
        # self.renderer.blit(image, self.pygame.Rect(0,0,10,10))
        # self.display.blit(text, [0, 0])
        # self.pygame.display.flip()

    def _move(self, direction):
        x = self.head.x
        y = self.head.y
        if direction == Direction.RIGHT:
            x += BLOCK_SIZE
        elif direction == Direction.LEFT:
            x -= BLOCK_SIZE
        elif direction == Direction.DOWN:
            y += BLOCK_SIZE
        elif direction == Direction.UP:
            y -= BLOCK_SIZE

        self.head = Point(x, y)


if __name__ == '__main__':
    game = SnakeGame()

    # game loop
    while True:
        game_over, score = game.play_step()

        if game_over:
            break

    print('Final Score', score)

    pygame.quit()
