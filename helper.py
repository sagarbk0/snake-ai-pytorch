import matplotlib.pyplot as plt
from IPython import display

plt.ion()


def plot(scores, mean_scores, title=None):
    """
    displays and saves plot of scores (blue line) and mean scores (orange line)
    :param scores: list[int]
    :param mean_scores: list[float]
    :param title: str
    """
    display.clear_output(wait=True)
    display.display(plt.gcf())
    plt.clf()
    if title:
        plt.title(title)
    else:
        plt.title('Training...')
    plt.xlabel('Number of Games')
    plt.ylabel('Score')
    plt.plot(scores)
    plt.plot(mean_scores)
    plt.ylim(ymin=0)
    plt.text(len(scores) - 1, scores[-1], str(scores[-1]))
    plt.text(len(mean_scores) - 1, mean_scores[-1], str(mean_scores[-1]))
    plt.show(block=False)
    if title:
        plt.savefig(f'results/{title}.png')
    plt.pause(.1)
