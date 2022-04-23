facingDirections = [[-1,0],[0,1],[1,0],[0,-1]]

rows = 26
cols = 34

f = open('smoothnessGraphs.txt','w')
f = open('smoothnessGraphs.txt','a')

def new_point(loc, new_dist, new_dir, stack, emptyBoard, minToWall):
    straight_loc = [loc[0] + facingDirections[new_dir][0], loc[1] + facingDirections[new_dir][1]]
    if 0 <= straight_loc[0] < rows and 0 <= straight_loc[1] < cols:
        if straight_loc[0] == 0 or straight_loc[0] == rows-1 or straight_loc[1] == 0 or straight_loc[1] == cols-1:
            minToWall[0] = min(minToWall[0], new_dist)
        if emptyBoard[straight_loc[0]][straight_loc[1]] > new_dist:
            emptyBoard[straight_loc[0]][straight_loc[1]] = new_dist
            stack.append([straight_loc, new_dir, new_dist, True])

def smoothness_rating(headx,heady,direction):
    stack = [[[headx,heady], direction, 0, False]] # location, directionFacing, distance, can go left/right
    emptyBoard = [[float('inf') for _ in range(cols)] for _ in range(rows)]
    # print(len(emptyBoard), len(emptyBoard[0]))
    emptyBoard[stack[0][0][0]][stack[0][0][1]] = 0
    minToWall = [float('inf')]
    if headx == 0 or headx == rows-1 or heady == 0 or heady == cols-1:
        minToWall[0] = 0
    while len(stack) > 0:
        loc, dir, dist, lr = stack.pop()
        new_point(loc, dist+1, dir, stack, emptyBoard, minToWall)
        if lr == True:
            new_point(loc, dist+1, (dir + 1) % 4, stack, emptyBoard, minToWall)
            new_point(loc, dist+1, (dir - 1) % 4, stack, emptyBoard, minToWall)

    # for i in emptyBoard:
    #     print([f"{num:02}" for num in i])

    strBoard = ";".join([",".join([str(i) for i in eb]) for eb in emptyBoard])
    # print([",".join(eb2) for eb2 in emptyBoard])
    f.write(f"{headx}_{heady}_{direction}_{minToWall[0]}_{strBoard}\n")

for i in range(rows):
    for j in range(cols):
        if i == 0 and j == 0:
            smoothness_rating(i,j,1)
            smoothness_rating(i,j,2)
        elif i == 0 and j == cols-1:
            smoothness_rating(i,j,2)
            smoothness_rating(i,j,3)
        elif i == rows-1 and j == 0:
            smoothness_rating(i,j,0)
            smoothness_rating(i,j,1)
        elif i == rows-1 and j == cols-1:
            smoothness_rating(i,j,0)
            smoothness_rating(i,j,3)
        elif i == 0:
            smoothness_rating(i,j,1)
            smoothness_rating(i,j,2)
            smoothness_rating(i,j,3)
        elif i == rows-1:
            smoothness_rating(i,j,0)
            smoothness_rating(i,j,1)
            smoothness_rating(i,j,3)
        elif j == 0:
            smoothness_rating(i,j,0)
            smoothness_rating(i,j,1)
            smoothness_rating(i,j,2)
        elif j == cols-1:
            smoothness_rating(i,j,0)
            smoothness_rating(i,j,2)
            smoothness_rating(i,j,3)
        else:
            for d in range(4):
                smoothness_rating(i,j,d)