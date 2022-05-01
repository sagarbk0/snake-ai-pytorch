import math

import torch
import random
import numpy as np
from collections import deque
from game import SnakeGameAI, Direction, Point
from model import Linear_QNet, QTrainer
from helper import plot

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001


class Agent:

    def __init__(self, model=Linear_QNet(11, 256, 3)):
        """
        Initializes hyperparameters, memory deque, model and trainer
        """
        self.n_games = 0
        self.epsilon = 0  # randomness
        self.gamma = 0.5  # discount rate
        self.memory = deque(maxlen=MAX_MEMORY)  # popleft()
        self.model = model
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)

    @staticmethod
    def get_state(game):
        """
        Get current state of game instance.
        :param game: SnakeGameAI()
        :return: ndarray
        """
        head = game.snake[0]

        # left, right, up, down points relative to current point
        point_l = Point(head.x - 20, head.y)
        point_r = Point(head.x + 20, head.y)
        point_u = Point(head.x, head.y - 20)
        point_d = Point(head.x, head.y + 20)

        # boolean values which indicate which direction the snake is facing
        dir_l = game.direction == Direction.LEFT
        dir_r = game.direction == Direction.RIGHT
        dir_u = game.direction == Direction.UP
        dir_d = game.direction == Direction.DOWN

        state = [
            # Danger straight
            (dir_r and game.is_collision(point_r)) or
            (dir_l and game.is_collision(point_l)) or
            (dir_u and game.is_collision(point_u)) or
            (dir_d and game.is_collision(point_d)),

            # Danger right
            (dir_u and game.is_collision(point_r)) or
            (dir_d and game.is_collision(point_l)) or
            (dir_l and game.is_collision(point_u)) or
            (dir_r and game.is_collision(point_d)),

            # Danger left
            (dir_d and game.is_collision(point_r)) or
            (dir_u and game.is_collision(point_l)) or
            (dir_r and game.is_collision(point_u)) or
            (dir_l and game.is_collision(point_d)),

            # Move direction
            dir_l,
            dir_r,
            dir_u,
            dir_d,

            # Food location 
            game.food.x < game.head.x,  # food left
            game.food.x > game.head.x,  # food right
            game.food.y < game.head.y,  # food up
            game.food.y > game.head.y  # food down
        ]

        return np.array(state, dtype=int)

    def remember(self, state, action, reward, next_state, done):
        """
        Store old state, new state and corresponding game results in memory deque
        :param state: ndarray
        :param action: list[int]
        :param reward: int
        :param next_state: ndarray
        :param done: bool
        """
        self.memory.append((state, action, reward, next_state, done))  # popleft if MAX_MEMORY is reached

    def train_long_memory(self):
        # Train based on a sample of memory that is batch size, or on full memory if memory is less than batch size.
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)  # list of tuples
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    def train_short_memory(self, game, state, action, reward, next_state, done):
        """
        Train based on the single instance represented by the given parameters
        :param game: SnakeGameAI()
        :param state: ndarray
        :param action: list[int]
        :param reward: int
        :param next_state: ndarray
        :param done: bool
        """
        release_frame = 0
        if reward == 10:
            frame_number = game.frame_iteration
            length = game.length
            if length <= 10:
                m = 6
            else:
                m = math.floor(0.6 * length + 2)
            y = False
            release_frame = frame_number + m
            self.trainer.train_step(state, action, reward, next_state, done)
        if game.frame_iteration >= release_frame:
            y = True
        if y:
            self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        """
        Get random value, compare it to epsilon (exploration-exploitation trade-off) to determine whether the next
        action is random or NN-based.
        :param state: ndarray
        :return: list[int]
        """
        # random moves: tradeoff exploration / exploitation
        self.epsilon = 80 - self.n_games
        final_move = [0, 0, 0]
        if random.randint(0, 200) < self.epsilon:
            move = random.randint(0, 2)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move


def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    # game = SnakeGameAI(visual=True, speed=10) # standard
    game = SnakeGameAI(speed=10) #
    while True:
        # get old state
        state_old = agent.get_state(game)

        # get move
        final_move = agent.get_action(state_old)

        # perform move and get new state
        reward, done, score = game.play_step(final_move)
        state_new = agent.get_state(game)

        # train short memory
        agent.train_short_memory(game, state_old, final_move, reward, state_new, done)

        # remember
        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            # train long memory, plot result
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if score > record:
                record = score
                agent.model.save()

            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games

            # plot_mean_scores.append(mean_score)
            # plot(plot_scores, plot_mean_scores)

            if agent.n_games == 250:
                agent.model.save()
                title = 'Combined Model, Speed 10 (250 epochs)'
                f = open(f'results/{title}.txt', 'w')
                f.write(
                    f'{agent.n_games}\n{record}\n{mean_score}\n{game.max_iteration}\n'
                    f'{game.total_iteration / agent.n_games}\n')
                f.write(",".join([str(i) for i in plot_scores]))
                f.close()
                plot(plot_scores, plot_mean_scores, title)
                break


if __name__ == '__main__':
    train()