from tools.consts import (
    EXPANDED_CELL,
    SCREENSHOT_COST,
    TOO_CLOSE_COST,
    TURN_PADDING,
    MID_TURN_PADDING,
)
from tools.movement import Direction

import math

from typing import List
from warnings import warn


class CellState:
    """Base class for all objects on the arena, such as cells, obstacles, etc"""

    def __init__(
        self,
        x,
        y,
        direction: Direction = Direction.NORTH,
        screenshot_id: List = None,
        penalty=0,
    ):
        self.x = x
        self.y = y
        self.direction = direction
        # If screenshot_od is not None, the snapshot is taken at that position is for the obstacle with id = screenshot_id for every obstacle id in the list
        self.screenshot_id = screenshot_id if screenshot_id is not None else []
        self.penalty = penalty  # Penalty for the view point of taking picture

    def __repr__(self):
        return "Cellstate(x: {}, y: {}, direction: {}, screenshot: {})".format(
            self.x, self.y, self.direction, self.screenshot_id
        )

    def cmp_position(self, x, y) -> bool:
        """Compare given (x,y) position with cell state's position

        Args:
            x (int): x coordinate
            y (int): y coordinate

        Returns:
            bool: True if same, False otherwise
        """
        return self.x == x and self.y == y

    def is_eq(self, x, y, direction):
        """Compare given x, y, direction with cell state's position and direction

        Args:
            x (int): x coordinate
            y (int): y coordinate
            direction (Direction): direction of cell

        Returns:
            bool: True if same, False otherwise
        """
        return self.x == x and self.y == y and self.direction == direction

    def add_screenshot(self, screenshot_id: str):
        """Set screenshot id for cell

        Args:
            screenshot_id (str): screenshot ids of a cell
        """
        self.screenshot_id.append(screenshot_id)

    def get_dict(self):
        """Returns a dictionary representation of the cell

        Returns:
            dict: {x,y,direction,screeshot_id}
        """
        return {"x": self.x, "y": self.y, "d": self.direction, "s": self.screenshot_id}


class Obstacle(CellState):
    """Obstacle class, inherited from CellState"""

    def __init__(self, x: int, y: int, direction: Direction, obstacle_id: int):
        super().__init__(x, y, direction)
        self.obstacle_id = obstacle_id

    def __eq__(self, other):
        """Checks if this obstacle is the same as input in terms of x, y, and direction

        Args:
            other (Obstacle): input obstacle to compare to

        Returns:
            bool: True if same, False otherwise
        """
        return (
            self.x == other.x
            and self.y == other.y
            and self.direction == other.direction
        )

    def get_view_state(self) -> List[CellState]:
        """
        Constructs the list of CellStates from which the robot can view the image on the obstacle properly.
        Currently checks a T shape of grids in front of the image
        "TODO: tune the grid values based on testing

        Returns:
            List[CellState]: Valid cell states where robot can be positioned to view the symbol on the obstacle
        """
        cells = []
        offset = 2 * EXPANDED_CELL

        # If the obstacle is facing north, then robot's cell state must be facing south
        if self.direction == Direction.NORTH:
            positions = [
                (self.x, self.y + offset),
                (self.x - 1, self.y + 2 + offset),
                (self.x + 1, self.y + 2 + offset),
                (self.x, self.y + 1 + offset),
                (self.x, self.y + 2 + offset),
            ]
            costs = [
                TOO_CLOSE_COST,
                SCREENSHOT_COST,
                SCREENSHOT_COST,
                TOO_CLOSE_COST // 2,
                0,
            ]

            for idx, pos in enumerate(positions):
                if Grid.is_valid_grid_position(*pos):
                    cells.append(
                        CellState(*pos, Direction.SOUTH, self.obstacle_id, costs[idx])
                    )

        # If obstacle is facing south, then robot's cell state must be facing north
        elif self.direction == Direction.SOUTH:

            positions = [
                (self.x, self.y - offset),
                (self.x + 1, self.y - 2 - offset),
                (self.x - 1, self.y - 2 - offset),
                (self.x, self.y - 1 - offset),
                (self.x, self.y - 2 - offset),
            ]
            costs = [
                TOO_CLOSE_COST,
                SCREENSHOT_COST,
                SCREENSHOT_COST,
                TOO_CLOSE_COST // 2,
                0,
            ]

            for idx, pos in enumerate(positions):
                if Grid.is_valid_grid_position(*pos):
                    cells.append(
                        CellState(*pos, Direction.NORTH, self.obstacle_id, costs[idx])
                    )

        # If obstacle is facing east, then robot's cell state must be facing west
        elif self.direction == Direction.EAST:
            positions = [
                (self.x + offset, self.y),
                (self.x + 2 + offset, self.y + 1),
                (self.x + 2 + offset, self.y - 1),
                (self.x + 1 + offset, self.y),
                (self.x + 2 + offset, self.y),
            ]
            costs = [
                TOO_CLOSE_COST,
                SCREENSHOT_COST,
                SCREENSHOT_COST,
                TOO_CLOSE_COST // 2,
                0,
            ]

            for idx, pos in enumerate(positions):
                if Grid.is_valid_grid_position(*pos):
                    cells.append(
                        CellState(*pos, Direction.WEST, self.obstacle_id, costs[idx])
                    )

        # If obstacle is facing west, then robot's cell state must be facing east
        elif self.direction == Direction.WEST:
            positions = [
                (self.x - offset, self.y),
                (self.x - 2 - offset, self.y + 1),
                (self.x - 2 - offset, self.y - 1),
                (self.x - 1 - offset, self.y),
                (self.x - 2 - offset, self.y),
            ]
            costs = [
                TOO_CLOSE_COST,
                SCREENSHOT_COST,
                SCREENSHOT_COST,
                TOO_CLOSE_COST // 2,
                0,
            ]

            for idx, pos in enumerate(positions):
                if Grid.is_valid_grid_position(*pos):
                    cells.append(
                        CellState(*pos, Direction.EAST, self.obstacle_id, costs[idx])
                    )
        return cells

    def get_obstacle_id(self):
        return self.obstacle_id


class Grid:
    """
    Grid object that contains the size of the grid and a list of obstacles
    """

    size_x: int = 20
    size_y: int = 20

    def __init__(self, size_x: int, size_y: int):
        """
        Args:
            size_x (int): Size of the grid in the x direction
            size_y (int): Size of the grid in the y direction
        """
        self.size_x = size_x
        self.size_y = size_y
        self.obstacles: List[Obstacle] = []

    def add_obstacle(self, obstacle: Obstacle):
        """Add a new obstacle to the Grid object, ignores if duplicate obstacle

        Args:
            obstacle (Obstacle): Obstacle to be added
        """
        # Loop through the existing obstacles to check for duplicates
        to_add = True
        for ob in self.obstacles:
            if ob == obstacle:
                to_add = False
                break

        if to_add:
            self.obstacles.append(obstacle)

    def reset_obstacles(self):
        """
        Resets the obstacles in the grid
        """
        self.obstacles = []

    def get_obstacles(self):
        """
        Returns the list of obstacles in the grid
        """
        return self.obstacles

    def turn_reachable(
        self, x: int, y: int, new_x: int, new_y: int, direction: Direction
    ) -> bool:
        """
        Checks if the robot can turn from x, y to new_x, new_y
        Logic:
            Checks 3 things for a turn: pre-turn, turn, post-turn
            1. pre-turn: if the obstacle is within the padding distance from the starting point
            2. post-turn: if the obstacle is within the padding distance from the end point
            3. turn:
                    Finds 3 points near the curve followed by the robot during the turn
                    For each point, checks if the obstacle is within the padding distance
        (For more details regarding the 3 points, refer to the _get_turn_checking_points function)
        """

        points = self._get_turn_checking_points(x, y, new_x, new_y, direction)

        if not self.is_valid_coord(x, y) or not self.is_valid_coord(new_x, new_y):
            return False
        for obstacle in self.obstacles:
            # pre turn
            preturn_horizontal_distance = obstacle.x - x
            preturn_vertical_distance = obstacle.y - y
            preturn_dist = math.sqrt(
                preturn_horizontal_distance**2 + preturn_vertical_distance**2
            )
            if preturn_dist < TURN_PADDING:
                return False

            # post-turn
            turn_horizontal_distance = obstacle.x - new_x
            turn_vertical_distance = obstacle.y - new_y
            turn_dist = math.sqrt(
                turn_horizontal_distance**2 + turn_vertical_distance**2
            )
            if turn_dist < TURN_PADDING:
                return False

            # turn
            for point in points:
                horizontal_distance = obstacle.x - point[0]
                vertical_distance = obstacle.y - point[1]
                if (
                    math.sqrt(horizontal_distance**2 + vertical_distance**2)
                    < MID_TURN_PADDING
                ):
                    return False

        return True

    def reachable(self, x: int, y: int) -> bool:
        """Checks whether the given x,y coordinate is reachable/safe for the robot from a straight movement.
        Args:
            x (int): x coordinate
            y (int): y coordinate
        """
        if not self.is_valid_coord(x, y):
            return False

        for ob in self.obstacles:
            if abs(ob.x - x) + abs(ob.y - y) <= 2:
                return False

            if max(abs(ob.x - x), abs(ob.y - y)) < 2:
                return False

        return True

    def half_turn_reachable(self, x: int, y: int, new_x: int, new_y: int) -> bool:
        """
        Checks if the robot can half turn from x, y to new_x, new_y
        Logic:
            find the longer axis for the movement, and add padding to the shorter axis.
            Check if the obstacle is within the padded area
        """
        if not self.is_valid_coord(x, y) or not self.is_valid_coord(new_x, new_y):
            return False
        padding = 2 * EXPANDED_CELL
        if new_x < x:
            new_x, x = x, new_x
        if new_y < y:
            new_y, y = y, new_y
        for obs in self.obstacles:
            if abs(x - new_x) > abs(y - new_y):
                # x is the longer axis. Use padding only for the y-axis
                if x <= obs.x <= new_x and y - padding <= obs.y <= new_y + padding:
                    return False
            else:
                # y is the longer axis. Use padding only for the x-axis
                if x - padding <= obs.x <= new_x + padding and y <= obs.y <= new_y:
                    return False
        return True

    def is_valid_coord(self, x: int, y: int) -> bool:
        """
        Checks if given position is within bounds
        """
        if x < 1 or x >= self.size_x - 1 or y < 1 or y >= self.size_y - 1:
            return False

        return True

    def is_valid_cell_state(self, state: CellState) -> bool:
        """
        Checks if given state is within bounds
        """
        return self.is_valid_coord(state.x, state.y)

    def get_view_obstacle_positions(self) -> List[List[CellState]]:
        """
        This function return a list of desired states for the robot to achieve based on the obstacle position and direction.
        The state is the position that the robot can see the image of the obstacle and is safe to reach without collision
        :return: [[CellState]]
        """

        optimal_positions = []
        for obstacle in self.obstacles:
            # skip objects that have SKIP as their direction
            if obstacle.direction == Direction.SKIP:
                continue
            else:
                view_states = [
                    view_state
                    for view_state in obstacle.get_view_state()
                    if self.reachable(view_state.x, view_state.y)
                ]
            optimal_positions.append(view_states)
        return optimal_positions

    def find_obstacle_by_id(self, obstacle_id: int) -> Obstacle:
        """
        Find the obstacle by its id
        """
        for obstacle in self.obstacles:
            if obstacle.obstacle_id == obstacle_id:
                return obstacle
        return None

    @staticmethod
    def _get_turn_checking_points(
        x: int, y: int, new_x: int, new_y: int, direction: Direction
    ):
        """
        Finds 3 points near the curve followed by the robot during the turn. Near the curve since it is difficult to
        approximate points on the curve since it is not a part of a circle, but rather an irregular ellipse.

        Some intermediate points are used in the calculation. These are:
            1. mid_x, mid_y: the mid-point between the starting point and end point of the turn
            2. tr_x, tr_y: The point that completes the right-angled triangle with the starting point and end point of the turn.

        The 3 points are calculated as follows:
            1. p1x, p1y: A point between the starting point and (mid_x, mid_y)
            2. p2x, p2y: the mid-point between (tr_x, tr_y) and (mid_x, mid_y)
            3. p3x, p3y: A point between the ending point and (mid_x, mid_y)
        """
        mid_x, mid_y = (x + new_x) / 2, (y + new_y) / 2
        if direction == Direction.NORTH or direction == Direction.SOUTH:
            tr_x, tr_y = x, new_y
            p1x, p1y = (x + mid_x) / 2, mid_y
            p2x, p2y = (tr_x + mid_x) / 2, (tr_y + mid_y) / 2
            p3x, p3y = mid_x, (new_y + mid_y) / 2
            return [(p1x, p1y), (p2x, p2y), (p3x, p3y)]
        elif direction == Direction.EAST or direction == Direction.WEST:
            tr_x, tr_y = new_x, y
            p1x, p1y = mid_x, (y + mid_y) / 2
            p2x, p2y = (tr_x + mid_x) / 2, (tr_y + mid_y) / 2
            p3x, p3y = (new_x + mid_x) / 2, mid_y
            return [(p1x, p1y), (p2x, p2y), (p3x, p3y)]
        raise ValueError("Invalid direction")

    @classmethod
    def is_valid_grid_position(cls, x: int, y: int):
        return 0 <= x < cls.size_x and 0 <= y < cls.size_y
