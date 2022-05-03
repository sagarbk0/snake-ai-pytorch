import pygame
import random
from enum import Enum
from collections import namedtuple
import numpy as np
import os
import math

pygame.init()
font = pygame.font.Font('arial.ttf', 25)


class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4


Point = namedtuple('Point', 'x, y')

# rgb colors
WHITE = (255, 255, 255)
RED = (200, 0, 0)
BLUE1 = (0, 0, 255)
BLUE2 = (0, 100, 255)
BLACK = (0, 0, 0)

BLOCK_SIZE = 20
SPEED = 1000

facingDirections = [[-1, 0], [0, 1], [1, 0], [0, -1]]


def norm(floatnum):
    """
    Get float location on graph, convert to integer cell number that can be referenced in smoothness graph
    :param floatnum: float
    :return: int
    """
    return int(floatnum // BLOCK_SIZE)


def point_norm(point: Point):
    """
    Return norm() for the X and Y of a point
    :param point: Point
    :return: list[int]
    """
    return [norm(point.x), norm(point.y)]


class SnakeGameAI:

    def __init__(self, w=640, h=480, speed=SPEED, visual=False, left_position=False, pygame=pygame):
        """
        w: width, h: height
        :param w: int
        :param h: int
        """
        self.w = w
        self.h = h
        self.display = None

        self.pygame = pygame
        # init display
        if visual:
            os.environ["SDL_VIDEO_WINDOW_POS"] = "%i,%i" % (200, 200)
            self.display = self.pygame.display.set_mode((self.w, self.h))
            self.pygame.display.set_caption('Snake AI')

        self.clock = self.pygame.time.Clock()
        self.total_iteration = 0
        self.frame_iteration = 0
        self.max_iteration = 0
        self.cols = w // BLOCK_SIZE
        self.rows = h // BLOCK_SIZE

        self.speed = speed

        # retrieve smoothness graphs from file
        with open('smoothnessGraphs.txt') as file:
            lines = file.readlines()

        # save smoothness graphs using dictionaries for fast access
        self.minDistToWall = dict()
        self.smoothnessRatings = dict()

        # iterate through smoothness graph file and save in dictionaries
        for line in lines:
            if len(line) > 0:
                details = line.split("_")
                x = int(details[0])
                y = int(details[1])
                direction = int(details[2])
                min_dist_to_wall = int(details[3])
                smoothness_rating = details[4]  # 2D array of smoothness ratings stored in string format
                smoothness_rating = [[int(srlNum) for srlNum in srl.split(",")] for srl in smoothness_rating.split(";")]
                self.minDistToWall[(x, y, direction)] = min_dist_to_wall
                self.smoothnessRatings[(x, y, direction)] = smoothness_rating

        self.reset()

    def reset(self):
        # initial game state
        self.direction = Direction.RIGHT

        self.head = Point(self.w / 2, self.h / 2)
        self.snake = [self.head,
                      Point(self.head.x - BLOCK_SIZE, self.head.y),
                      Point(self.head.x - (2 * BLOCK_SIZE), self.head.y)]

        self.score = 0
        self.food = None
        self._place_food()
        self.max_iteration = max(self.frame_iteration, self.max_iteration)
        self.total_iteration += self.frame_iteration
        self.frame_iteration = 0
        self.length = 0
        self.Frame1 = 0
        self.Frame2 = 0
        self.DPA = 0
        self.M = 0
        self.frame_timeout_period = 0  # Restart frame_timeout_period

    def _place_food(self):
        # place food randomly
        x = random.randint(0, (self.w - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
        y = random.randint(0, (self.h - BLOCK_SIZE) // BLOCK_SIZE) * BLOCK_SIZE
        self.food = Point(x, y)
        if self.food in self.snake:
            self._place_food()

    @staticmethod
    def distance(point1, point2):
        """
        Euclidean distance, used for smoothness rating function
        :param point1: Point()
        :param point2: Point()
        :return: float
        """
        return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    def play_step(self, action):
        """
        Given an action, call functions to update state, and deduce the reward, updated score and whether the game has
        ended. Feed back these results to be used by the neural network.
        :param action: list[int]
        :return: tuple[int, bool, int]
        """
        self.frame_iteration += 1
        self.frame_timeout_period += 1  # Update frame_timeout_period

        # 1. collect user input
        # (commented out, because it interferes when using side_by_side.py)
        # for event in self.pygame.event.get():
        #     if event.type == self.pygame.QUIT:
        #         self.pygame.quit()
        #         quit()

        possDirs, minTail, maxTail, minWall, maxWall = self.smoothness_rating()

        oldHead = self.head

        # 2. move
        old_head = self.head
        self._move(action)  # update the head
        self.snake.insert(0, self.head)

        # 3. check if game over
        game_over = False
        if self.is_collision():  # or self.frame_iteration > 100*len(self.snake):
            game_over = True
            reward = -10
            return reward, game_over, self.score

        reward = 0

        # 3.2 timeout strategy
        p_steps = (0.7 * len(self.snake)) + 10
        if self.frame_timeout_period > p_steps:
            reward += -0.5 / len(self.snake)

        # 3.3 idle too long
        if self.frame_timeout_period == 1000:
            game_over = True
            reward += -20
            return reward, game_over, self.score

        # 4. place new food or just move
        elif self.head == self.food:
            self.score += 1
            self.frame_timeout_period = 0  # Reset frame_timeout_period
            reward += 10
            self._place_food()
        else:
            # Distance reward function based on Wei et al. equation
            length = len(self.snake)
            distance_old = self.distance(old_head, self.food)
            distance_new = self.distance(self.head, self.food)
            reward += 10 * math.log((length + distance_old) / (length + distance_new), length)
            self.snake.pop()

        # smoothness/space rating rewards
        if len(possDirs) != 0:
            for poss in possDirs:
                p = poss[0]
                possHead = [oldHead.x + facingDirections[p][0], oldHead.y + facingDirections[p][1]]
                if possHead[0] == self.head.x and possHead[1] == self.head.y:
                    # negative reward (penalty) if tail rating or distance to wall are minimum
                    # positive reward if tail rating or distance to wall are maximum
                    # no reward if either are intermediate
                    tailRating = poss[1]
                    if tailRating == minTail:
                        reward -= 10
                    elif tailRating == maxTail:
                        reward += 10
                    distWall = poss[2]
                    if distWall == minWall:
                        reward -= 10
                    elif distWall == maxWall:
                        reward += 10

        self._update_ui()
        self.clock.tick(self.speed)
        # 6. return reward, game over and score
        return reward, game_over, self.score

    def smoothness_rating(self):
        """
        Retrieve stored smoothness rating graph that applies to current location and direction
        Fetch smoothness ratings from graph for the current snake
        For each direction, calculate tail rating by adding smoothness ratings of each point in the tail
        For each direction, retrieve wall rating
        Return maximum and minimum wall ratings and tail ratings, and return all wall ratings
        :return: tuple[list[list[int]], float | int | int | int | int]
        """
        ignore = [None, None]
        if len(self.snake) > 0:
            ignore = [norm(self.snake[1][1]) - norm(self.head[1]), norm(self.snake[1][0]) - norm(self.head[0])]
        possDirs = []
        minTail = float('inf')
        minWall = float('inf')
        maxTail = float('-inf')
        maxWall = float('-inf')

        normHead = [norm(self.head.y), norm(self.head.x)]
        for d in range(4):
            triple = (normHead[0], normHead[1], d)
            if facingDirections[d] != ignore and triple in self.smoothnessRatings and triple in self.minDistToWall:
                tailRating = 0
                smoothnessRatings = self.smoothnessRatings[triple]
                for t in self.snake:
                    tailRating += smoothnessRatings[norm(t.y)][norm(t.x)]
                distWall = self.minDistToWall[triple]
                minTail = min(tailRating, minTail)
                maxTail = max(tailRating, maxTail)
                minWall = min(distWall, minWall)
                maxWall = max(distWall, maxWall)
                possDirs.append([d, tailRating, distWall])
        return possDirs, minTail, maxTail, minWall, maxWall

    def is_collision(self, pt=None):
        """
        Detects if snake's head has collided with wall or with its tail
        :param pt: Point()
        :return: bool
        """
        if self.Frame2 <= (self.frame_iteration + self.M) and self.M > 0 and self.DPA == 0:
            self.DPA = 1
        else:
            self.DPA = 0

        if pt is None:
            pt = self.head
        # hits boundary
        if pt.x > self.w - BLOCK_SIZE or pt.x < 0 or pt.y > self.h - BLOCK_SIZE or pt.y < 0:
            # self.updateM()
            self.Frame1 = int(self.Frame2)
            self.Frame2 = int(self.frame_iteration)
            if self.Frame1 != 0 and self.Frame2 != 0:
                self.M = self.length - (self.Frame2 - self.Frame1) + 1
            return True
        # hits itself
        if pt in self.snake[1:]:
            self.Frame1 = int(self.Frame2)
            self.Frame2 = int(self.frame_iteration)
            if self.Frame1 != 0 and self.Frame2 != 0:
                self.M = int(self.length - (self.Frame2 - self.Frame1) + 1)

            return True

        return False

    def _update_ui(self):
        # Update game display
        if self.display:
            self.display.fill(BLACK)

            for pt in self.snake:
                self.pygame.draw.rect(self.display, BLUE1, self.pygame.Rect(pt.x, pt.y, BLOCK_SIZE, BLOCK_SIZE))
                self.pygame.draw.rect(self.display, BLUE2, self.pygame.Rect(pt.x + 4, pt.y + 4, 12, 12))

            self.pygame.draw.rect(self.display, RED, self.pygame.Rect(self.food.x, self.food.y, BLOCK_SIZE, BLOCK_SIZE))

            text = font.render("Score: " + str(self.score), True, WHITE)
            self.display.blit(text, [0, 0])
            self.pygame.display.flip()

    def _move(self, action):
        """
        Get new direction and update self.head based on direction
        :param action: list[int]
        """
        # [straight, right, left]

        clock_wise = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]
        idx = clock_wise.index(self.direction)

        if np.array_equal(action, [1, 0, 0]):
            new_dir = clock_wise[idx]  # no change
        elif np.array_equal(action, [0, 1, 0]):
            next_idx = (idx + 1) % 4
            new_dir = clock_wise[next_idx]  # right turn r -> d -> l -> u
        else:  # [0, 0, 1]
            next_idx = (idx - 1) % 4
            new_dir = clock_wise[next_idx]  # left turn r -> u -> l -> d

        self.direction = new_dir

        x = self.head.x
        y = self.head.y
        if self.direction == Direction.RIGHT:
            x += BLOCK_SIZE
        elif self.direction == Direction.LEFT:
            x -= BLOCK_SIZE
        elif self.direction == Direction.DOWN:
            y += BLOCK_SIZE
        elif self.direction == Direction.UP:
            y -= BLOCK_SIZE

        self.head = Point(x, y)
