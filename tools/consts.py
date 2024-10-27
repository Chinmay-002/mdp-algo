from tools.movement import Direction


# algo costs: HYPERPARAMETERS
TURN_FACTOR = 6  # robot moves 8 units per turn
HALF_TURN_FACTOR = 5 * 2  # robot moves 5 units per half turn, wieghted by 2
REVERSE_FACTOR = 3  # prefer to move forward than reverse
SAFE_COST = 1000  # the cost for the turn in case there is a chance that the robot is touch some obstacle
SCREENSHOT_COST = 100  # the cost for the place where the picture is taken
TOO_CLOSE_COST = (
    50  # the cost for the place where the robot is too close to the obstacle
)
# collision consts
TURN_PADDING = 2
MID_TURN_PADDING = 2

# turning consts
TURN_RADIUS = 1
TURNS = [5 * TURN_RADIUS, 3 * TURN_RADIUS]
HALF_TURNS = [4 * TURN_RADIUS, 1 * TURN_RADIUS]

# consts
MOVE_DIRECTION = [
    (1, 0, Direction.EAST),
    (-1, 0, Direction.WEST),
    (0, 1, Direction.NORTH),
    (0, -1, Direction.SOUTH),
]  # move direction is a list of the possible directions the robot can move for forward/backward motion

ITERATIONS = 2000  # number of iterations


# grid consts
EXPANDED_CELL = 1  # for both agent and obstacles
