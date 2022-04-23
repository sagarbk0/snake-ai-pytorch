import pygame
import random
from enum import Enum
from collections import namedtuple
import numpy as np
import math

pygame.init()
font = pygame.font.Font('arial.ttf', 25)
#font = pygame.font.SysFont('arial', 25)

class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4

Point = namedtuple('Point', 'x, y')

# rgb colors
WHITE = (255, 255, 255)
RED = (200,0,0)
BLUE1 = (0, 0, 255)
BLUE2 = (0, 100, 255)
BLACK = (0,0,0)

BLOCK_SIZE = 20
SPEED = 1000

facingDirections = [[-1,0],[0,1],[1,0],[0,-1]]

def norm(floatnum):
    return int(floatnum//BLOCK_SIZE)

def pointNorm(point: Point):
    return [norm(point.x), norm(point.y)]

class SnakeGameAI:

    def __init__(self, w=640, h=480):
        """

        :param w: int
        :param h: int
        """
        self.w = w
        self.h = h
        # init display
        # self.display = pygame.display.set_mode((self.w, self.h))
        # pygame.display.set_caption('Snake')
        self.clock = pygame.time.Clock()
        self.total_iteration = 0
        self.frame_iteration = 0
        self.max_iteration = 0
        self.cols = w//BLOCK_SIZE
        self.rows = h//BLOCK_SIZE
        with open('smoothnessGraphs.txt') as file:
            lines = file.readlines()
        self.minDistToWall = dict()
        self.smoothnessRatings = dict()
        for l in lines:
            if len(l) > 0:
                details = l.split("_")
                x = int(details[0])
                y = int(details[1])
                direction = int(details[2])
                minDistToWall = int(details[3])
                smoothnessRating = details[4] # string
                smoothnessRating = [[int(srlNum) for srlNum in srl.split(",")] for srl in smoothnessRating.split(";")]
                self.minDistToWall[(x,y,direction)] = minDistToWall
                self.smoothnessRatings[(x,y,direction)] = smoothnessRating
        
        # for i in range(4):
        #     f = open(f'{i}.txt', 'w')
        #     f = open(f'{i}.txt', 'a')
        #     for x in self.smoothnessRatings[(11,15,i)]:
        #         stringArr = [str(y) for y in x]
        #         stringArr = [y if len(y) == 2 else '0'+y for y in stringArr]
        #         f.write(' '.join(stringArr) + '\n')
        
        self.reset()

    def reset(self):
        # init game state
        self.direction = Direction.RIGHT

        self.head = Point(self.w/2, self.h/2)
        self.snake = [self.head,
                      Point(self.head.x-BLOCK_SIZE, self.head.y),
                      Point(self.head.x-(2*BLOCK_SIZE), self.head.y)]

        self.score = 0
        self.food = None
        self._place_food()
        self.max_iteration = max(self.frame_iteration, self.max_iteration)
        self.total_iteration += self.frame_iteration
        self.frame_iteration = 0
        self.length= 0
        self.Frame1 = 0
        self.Frame2 = 0
        self.DPA = 0
        self.M=0
        self.frame_timeout_period = 0        # Restart frame_timeout_period


    def _place_food(self):
        x = random.randint(0, (self.w-BLOCK_SIZE )//BLOCK_SIZE )*BLOCK_SIZE
        y = random.randint(0, (self.h-BLOCK_SIZE )//BLOCK_SIZE )*BLOCK_SIZE
        self.food = Point(x, y)
        if self.food in self.snake:
            self._place_food()

    def distance(self, point1, point2):
        return math.sqrt((point1[0]-point2[0])**2+(point1[1]-point2[1])**2)

    def play_step(self, action):
        self.frame_iteration += 1
        self.frame_timeout_period += 1           # Update frame_timeout_period

        # 1. collect user input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        
        possDirs, minTail, maxTail, minWall, maxWall = self.smoothness_rating()
        
        # print([pointNorm(i) for i in self.snake])
        # print(minTail, maxTail, minWall, maxWall)
        oldHead = self.head

        # 2. move
        old_head = self.head
        self._move(action) # update the head
        self.snake.insert(0, self.head)
        
        # 3. check if game over
        reward = 0
        game_over = False
        if self.is_collision():# or self.frame_iteration > 100*len(self.snake):
            game_over = True
            reward = -10
            return reward, game_over, self.score

                    # 3.2 timeout strategy
        p_steps = ( 0.7*len(self.snake) ) + 10
        # print("Frame Iteration = {f}, P steps = {p}".format( p = p_steps, f = self.frame_timeout_period ))
        if self.frame_timeout_period > p_steps:
            reward = -0.5 / len(self.snake)

        # 3.3 idle too long
        if self.frame_timeout_period == 1000:
            game_over = True
            reward = -20
            return reward, game_over, self.score

        # 4. place new food or just move
        elif self.head == self.food:
            self.score += 1
            self.frame_timeout_period = 0        # Reset frame_timeout_period
            reward = 10
            self._place_food()
        else:
            # pt = self.head
            # if pt.x == self.w - BLOCK_SIZE or pt.x == 0 or pt.y == self.h-BLOCK_SIZE or pt.y == 0:
            #     reward = -0.5
            # else:
            Lt = len(self.snake)
            Dt = self.distance(old_head, self.food)
            Dt1 = self.distance(self.head, self.food)
            reward = 10*math.log((Lt+Dt)/(Lt+Dt1), Lt)
            self.snake.pop()
        
        # print(self.head)
        # print(int(self.head.y))
        # print(int(self.head.x))

        if len(possDirs) != 0:
            for poss in possDirs:
                # print(poss)
                p = poss[0]
                possHead = [oldHead.x + facingDirections[p][0], oldHead.y + facingDirections[p][1]]
                if possHead[0] == self.head.x and possHead[1] == self.head.y:
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
        # if norm(self.head.x) in [0, self.cols] or norm(self.head.y) in [0, self.rows]:
        #     reward -= 10

        # if self.head.x

        # 5. update ui and clock
        # self._update_ui()
        self.clock.tick(SPEED)
        # 6. return game over and score
        return reward, game_over, self.score

    def smoothness_rating(self):
        ignore = [None, None]
        if len(self.snake) > 0:
            ignore = [norm(self.snake[1][1])-norm(self.head[1]),norm(self.snake[1][0])-norm(self.head[0])]
        possDirs = []
        minTail = float('inf')
        minWall = float('inf')
        maxTail = float('-inf')
        maxWall = float('-inf')

        normHead = [norm(self.head.y), norm(self.head.x)]
        # print(len(self.smoothnessRatings[list(self.smoothnessRatings.keys())[0]]))
        # print(len(self.smoothnessRatings[list(self.smoothnessRatings.keys())[0]][0]))
        for d in range(4):
            triple = (normHead[0], normHead[1], d)
            # print(self.head.x//BLOCK_SIZE, self.head.y//BLOCK_SIZE, d)
            if facingDirections[d] != ignore and triple in self.smoothnessRatings and triple in self.minDistToWall:
                tailRating = 0
                smoothnessRatings = self.smoothnessRatings[triple]
                for t in self.snake:
                    # print(len(smoothnessRatings))
                    # print(t, norm(t.x), norm(t.y))
                    # if not 0 <= norm(t.x) <= 24 or not 0 <= norm(t.y) <= 32:
                    # print(t, norm(t.x), norm(t.y))
                    tailRating += smoothnessRatings[norm(t.y)][norm(t.x)]
                distWall = self.minDistToWall[triple]
                minTail = min(tailRating, minTail)
                maxTail = max(tailRating, maxTail)
                minWall = min(distWall, minWall)
                maxWall = max(distWall, maxWall)
                possDirs.append([d, tailRating, distWall])
        return [possDirs, minTail, maxTail, minWall, maxWall]

    # def new_point(self, loc, new_dist, new_dir, stack, emptyBoard):
    #     straight_loc = [loc[0] + facingDirections[new_dir][0], loc[1] + facingDirections[new_dir][1]]
    #     if 0 <= straight_loc[0] < self.rows and 0 <= straight_loc[1] < self.cols:
    #         if emptyBoard[straight_loc[0]][straight_loc[1]] > new_dist:
    #             emptyBoard[straight_loc[0]][straight_loc[1]] = new_dist
    #             stack.append([straight_loc, new_dir, new_dist, True])
    
    # def smoothness_rating(self):
    #     ignore = [None, None]
    #     if len(self.tail) > 0:
    #         len(self.tail)
    #     stack = [[[int(self.head.x//BLOCK_SIZE),int(self.head.y//BLOCK_SIZE)], 3, 0, False]] # location, directionFacing, distance, can go left/right
    #     emptyBoard = [[float('inf') for _ in range(self.cols)] for _ in range(self.rows)]
    #     print(len(emptyBoard), len(emptyBoard[0]))
    #     emptyBoard[stack[0][0][0]][stack[0][0][1]] = 0

    #     while len(stack) > 0:
    #         loc, dir, dist, lr = stack.pop()
    #         self.new_point(loc, dist+1, dir, stack, emptyBoard)
    #         if lr == True:
    #             self.new_point(loc, dist+1, (dir + 1) % 4, stack, emptyBoard)
    #             self.new_point(loc, dist+1, (dir - 1) % 4, stack, emptyBoard)

    #     for i in emptyBoard:
    #         print([f"{num:02}" for num in i])

    #     return emptyBoard

    def is_collision(self, pt=None):
        if self.Frame2 <= (self.frame_iteration + self.M) and self.M > 0 and self.DPA == 0:
            self.DPA = 1
        else:
            self.DPA = 0
            

        if pt is None:
            pt = self.head
        # hits boundary
        if pt.x > self.w - BLOCK_SIZE or pt.x < 0 or pt.y > self.h - BLOCK_SIZE or pt.y < 0:
                        #self.updateM()
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
        self.display.fill(BLACK)

        for pt in self.snake:
            pygame.draw.rect(self.display, BLUE1, pygame.Rect(pt.x, pt.y, BLOCK_SIZE, BLOCK_SIZE))
            pygame.draw.rect(self.display, BLUE2, pygame.Rect(pt.x+4, pt.y+4, 12, 12))

        pygame.draw.rect(self.display, RED, pygame.Rect(self.food.x, self.food.y, BLOCK_SIZE, BLOCK_SIZE))

        text = font.render("Score: " + str(self.score), True, WHITE)
        self.display.blit(text, [0, 0])
        pygame.display.flip()
        None


    def _move(self, action):
        # [straight, right, left]

        clock_wise = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]
        idx = clock_wise.index(self.direction)

        if np.array_equal(action, [1, 0, 0]):
            new_dir = clock_wise[idx] # no change
        elif np.array_equal(action, [0, 1, 0]):
            next_idx = (idx + 1) % 4
            new_dir = clock_wise[next_idx] # right turn r -> d -> l -> u
        else: # [0, 0, 1]
            next_idx = (idx - 1) % 4
            new_dir = clock_wise[next_idx] # left turn r -> u -> l -> d

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