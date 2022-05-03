from agent import Agent, train
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
    # saved_model = Linear_QNet(11, 256, 3)
    # saved_model.load_state_dict(torch.load('model/model_new.pth'))  # load a pretrained AI model (didn't work, have to use model in-memory)
    # saved_model.eval()
    print('Training AI. Please wait for 2-5 minutes...')
    agent = train(n_games=100)
    # game_human = threading.Thread(target=SnakeGameHuman, args={"rightPosition": True})

    user_input = input('Play game? Y/N\n')

    while user_input != 'N':
        pygame.init()
        game_ai = SnakeGameAI(visual=True)
        game_human = SnakeGameHuman(rightPosition=True)

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
                print("Want a real challenge? Try higher speeds, or increase the AI's epochs so that it has more than 2 minutes to learn.")
                break

            if done_human:
                print("AI won")
                print("No surprises here.")
                break
        
        agent.train_long_memory()

        user_input = input('Play game again? Y/N\n')
        
        # pygame.quit()

if __name__ == '__main__':
    play()
