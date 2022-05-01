from agent import Agent
from game import SnakeGameAI
import torch
from enum import Enum
from model import Linear_QNet
import pygame
from snake_game_human import SnakeGame as SnakeGameHuman


class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4


def play():
    """
    Displays two game boards, AI and human, which play side by side. When the first one loses, both games are ended
    and the opposite player wins.
    """
    pygame.init()
    saved_model = Linear_QNet(11, 256, 3)
    saved_model.load_state_dict(torch.load('model/model_combined_speed10.pth'))  # load a pretrained AI model
    saved_model.eval()
    agent = Agent(saved_model)
    game_ai = SnakeGameAI(visual=True)
    game_human = SnakeGameHuman(rightPosition=True)
    # game_human = threading.Thread(target=SnakeGameHuman, args={"rightPosition": True})

    while True:
        # get old state
        state_old = agent.get_state(game_ai)

        # get move
        final_move = agent.get_action(state_old)

        # perform move and get new state
        reward_ai, done_ai, score_ai = game_ai.play_step(final_move)

        state_new = agent.get_state(game_ai)

        agent.train_short_memory(game_ai, state_old, final_move, reward_ai, state_new, done_ai)

        agent.remember(state_old, final_move, reward_ai, state_new, done_ai)

        # human
        done_human, score_human = game_human.play_step()

        if done_ai:
            print("Human won")
            break

        if done_human:
            print("AI won")
            break

    pygame.quit()


if __name__ == '__main__':
    play()
