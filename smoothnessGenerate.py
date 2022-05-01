facingDirections = [[-1, 0], [0, 1], [1, 0], [0, -1]]

rows = 26
cols = 34

f = open('smoothnessGraphs.txt', 'w')
f = open('smoothnessGraphs.txt', 'a')


def new_point(loc, new_dist, new_dir, stack, empty_board, min_to_wall):
    """
    Updates one point of the graph.
    Adds neighbouring points to stack if they have a lower score.
    Also saves min_to_wall score.
    :param loc: list[int]
    :param new_dist: int
    :param new_dir: int
    :param stack: bool
    :param empty_board: list[list[int]]
    :param min_to_wall: list[int]
    """
    straight_loc = [loc[0] + facingDirections[new_dir][0], loc[1] + facingDirections[new_dir][1]]
    if 0 <= straight_loc[0] < rows and 0 <= straight_loc[1] < cols:
        if straight_loc[0] == 0 or straight_loc[0] == rows - 1 or straight_loc[1] == 0 or straight_loc[1] == cols - 1:
            min_to_wall[0] = min(min_to_wall[0], new_dist)
        if empty_board[straight_loc[0]][straight_loc[1]] > new_dist:
            empty_board[straight_loc[0]][straight_loc[1]] = new_dist
            stack.append([straight_loc, new_dir, new_dist, True])


def smoothness_rating(headx, heady, direction):
    """
    Receives starting point (headx, heady) and direction to travel.
    Creates empty graph with each point initialized to infinity smoothness score.
    Uses stack to repeatedly call new_point function to update graph, 
    till the full smoothness graph has been generated.
    :param headx: int
    :param heady: int
    :param direction: int
    """
    stack = [[[headx, heady], direction, 0, False]]  # location, directionFacing, distance, can go left/right
    emptyBoard = [[float('inf') for _ in range(cols)] for _ in range(rows)]
    emptyBoard[stack[0][0][0]][stack[0][0][1]] = 0
    minToWall = [float('inf')]
    if headx == 0 or headx == rows - 1 or heady == 0 or heady == cols - 1:
        minToWall[0] = 0
    while len(stack) > 0:
        loc, dir, dist, lr = stack.pop()
        new_point(loc, dist + 1, dir, stack, emptyBoard, minToWall)
        if lr:
            new_point(loc, dist + 1, (dir + 1) % 4, stack, emptyBoard, minToWall)
            new_point(loc, dist + 1, (dir - 1) % 4, stack, emptyBoard, minToWall)

    strBoard = ";".join([",".join([str(i) for i in eb]) for eb in emptyBoard])
    f.write(f"{headx}_{heady}_{direction}_{minToWall[0]}_{strBoard}\n")


if __name__ == "__main__":
    # Generates smoothness graphs
    # The cells located near walls have either 2 or 3 smoothness graphs, based on the provided conditions
    # Other cells have 4 smoothness graphs, one for each direction

    for i in range(rows):
        for j in range(cols):
            if i == 0 and j == 0:
                smoothness_rating(i, j, 1)
                smoothness_rating(i, j, 2)
            elif i == 0 and j == cols - 1:
                smoothness_rating(i, j, 2)
                smoothness_rating(i, j, 3)
            elif i == rows - 1 and j == 0:
                smoothness_rating(i, j, 0)
                smoothness_rating(i, j, 1)
            elif i == rows - 1 and j == cols - 1:
                smoothness_rating(i, j, 0)
                smoothness_rating(i, j, 3)
            elif i == 0:
                smoothness_rating(i, j, 1)
                smoothness_rating(i, j, 2)
                smoothness_rating(i, j, 3)
            elif i == rows - 1:
                smoothness_rating(i, j, 0)
                smoothness_rating(i, j, 1)
                smoothness_rating(i, j, 3)
            elif j == 0:
                smoothness_rating(i, j, 0)
                smoothness_rating(i, j, 1)
                smoothness_rating(i, j, 2)
            elif j == cols - 1:
                smoothness_rating(i, j, 0)
                smoothness_rating(i, j, 2)
                smoothness_rating(i, j, 3)
            else:
                for d in range(4):
                    smoothness_rating(i, j, d)
