import heapq
import math
import numpy as np

from python_tsp.exact import solve_tsp_dynamic_programming

from entities.entity import CellState, Obstacle, Grid
from entities.robot import Robot
from tools.movement import Direction, Motion
from tools.consts import (
    MOVE_DIRECTION,
    TURN_FACTOR,
    HALF_TURN_FACTOR,
    ITERATIONS,
    TURN_RADIUS,
    SAFE_COST,
    TURNS,
    HALF_TURNS,
    REVERSE_FACTOR,
)


class MazeSolver:
    """
    A class that is used to find the shortest path given a grid, robot and obstacles
    """

    def __init__(
        self,
        size_x: int = 20,
        size_y: int = 20,
        robot: Robot = None,
        robot_x: int = 1,
        robot_y: int = 1,
        robot_direction: Direction = Direction.NORTH,
    ):
        """

        :param size_x: size of the grid in x direction. Default is 20
        :param size_y: size of the grid in y direction. Default is 20
        :param robot: A robot object that contains the robot's path. Preferrentially used over robot_x, robot_y, robot_direction
        :param robot_x: If no robot object is provided, the x coordinate of the robot. Default is 1
        :param robot_y: If no robot object is provided, the y coordinate of the robot. Default is 1
        :param robot_direction: If no robot object is provided, the direction the robot is facing. Default is NORTH
        """
        self.grid = Grid(size_x, size_y)

        self.robot = robot if robot else Robot(robot_x, robot_y, robot_direction)

        self.path_table = dict()
        self.cost_table = dict()
        self.motion_table = dict()

    def add_obstacle(
        self, x: int, y: int, direction: Direction, obstacle_id: int
    ) -> None:
        """
        Add an obstacle to the grid

        :param x: x coordinate of the obstacle
        :param y: y coordinate of the obstacle
        :param direction: direction that the image on the obstacle is facing
        :param obstacle_id: id of the obstacle
        """
        self.grid.add_obstacle(Obstacle(x, y, direction, obstacle_id))

    def clear_obstacles(self) -> None:
        """
        Removes all obstacles from the grid
        """
        self.grid.reset_obstacles()

    def get_optimal_path(self):
        """
        Get the optimal path from the using dynamic programming

        :return: An Optimal path, which is a list of all the CellStates involved and cost of the path
        """
        min_dist = 1e9
        optimal_path = []

        # get all grid positions that can view the obstacle images
        views = self.grid.get_view_obstacle_positions()
        num_views = len(views)

        for bin_pos in self._get_visit_options(num_views):
            visit_states = [self.robot.get_start_state()]
            cur_view_positions = []

            for i in range(num_views):
                # if the i-th bit is 1, then the robot will visit the i-th view position
                if bin_pos[i] == "1":
                    # add the view position to the current view positions
                    cur_view_positions.append(views[i])
                    # add the view position to the visit states
                    visit_states.extend(views[i])

            # for each visit state, generate paths and cost of the paths using A* search
            self._generate_paths(visit_states)

            # generate all possible combinations of the view positions
            combinations = MazeSolver._generate_combinations(
                cur_view_positions, 0, [], [], ITERATIONS
            )

            # iterate over all the combinations and find the optimal path
            for combination in combinations:
                visited = [0]

                current_idx, cost = 1, 0

                # iterate over the views and calculate the cost of the path
                for idx, view_pos in enumerate(cur_view_positions):
                    visited.append(current_idx + combination[idx])
                    cost += view_pos[combination[idx]].penalty
                    current_idx += len(view_pos)

                # initialize the cost matrix
                cost_matrix = np.zeros((len(visited), len(visited)))

                for start_idx in range(len(visited) - 1):
                    for end_idx in range(start_idx + 1, len(visited)):
                        start_state = visit_states[visited[start_idx]]
                        end_state = visit_states[visited[end_idx]]

                        # check if the cost has already been calculated
                        if (start_state, end_state) in self.cost_table:
                            cost_matrix[start_idx, end_idx] = self.cost_table[
                                (start_state, end_state)
                            ]
                        else:
                            # initialize the cost matrix with a large value since the cost has not been calculated
                            cost_matrix[start_idx, end_idx] = 1e9

                        # add the cost for the reverse path
                        cost_matrix[end_idx, start_idx] = cost_matrix[
                            start_idx, end_idx
                        ]

                # set the cost of travelling from each state to itself to 0
                cost_matrix[:, 0] = 0

                # solve the TSP problem using dynamic programming
                permutation, distance = solve_tsp_dynamic_programming(cost_matrix)

                # if the distancd is more than the minimum distance, the path is irrelevant.
                if distance + cost >= min_dist:
                    continue

                # update the minimum distance and the optimal path
                min_dist = distance + cost

                optimal_path = [visit_states[0]]
                # generate the optimal path
                for idx in range(len(permutation) - 1):
                    from_state = visit_states[visited[permutation[idx]]]
                    to_state = visit_states[visited[permutation[idx + 1]]]

                    current_path = self.path_table[(from_state, to_state)]

                    # add each state from the current path to the optimal path
                    for idx2 in range(1, len(current_path)):
                        optimal_path.append(
                            CellState(
                                current_path[idx2][0],
                                current_path[idx2][1],
                                current_path[idx2][2],
                            )
                        )
                    # check position of to_state wrt to obstacle. If it is directly in front of the obstacle, add idC
                    # if it is to the left or right, add idL or idR
                    corresponding_obs = self.grid.find_obstacle_by_id(
                        to_state.screenshot_id
                    )
                    if corresponding_obs:
                        pos = MazeSolver._get_capture_relative_position(
                            optimal_path[-1], corresponding_obs
                        )
                        formatted = f"{to_state.screenshot_id}_{pos}"

                        optimal_path[-1].add_screenshot(formatted)
                    else:
                        raise ValueError(
                            f"Obstacle with id {to_state.screenshot_id} not found"
                        )

            # if the optimal path has been found, break the view positions loop
            if optimal_path:
                break

        return optimal_path, min_dist

    def _generate_paths(self, states) -> int:
        """
        Generate and store the path between all states in a list of states using astar search
        """
        for i in range(len(states) - 1):
            for j in range(i + 1, len(states)):
                self._astar_search(states[i], states[j])

    def _astar_search(self, start: CellState, end: CellState) -> None:
        """
        A* search algorithm to find the shortest path between two states
        Each state is defined by x, y, and direction.

        Heuristic: distance f = g + h
        g: Actual distance from the start state to the current state
        h: Estimated distance from the current state to the end state
        """
        # check if the path has already been calculated

        if (start, end) in self.path_table:
            return

        # initialize the actual distance dict with the start state
        g_dist = {(start.x, start.y, start.direction): 0}

        # initialize min heap with the start state
        # the heap is a list of tuples (h, x, y, direction) where h is the estimated distance from the current state to the end state
        heap = [
            (self._estimate_distance(start, end), start.x, start.y, start.direction)
        ]

        visited = set()
        parent_dict = dict()

        while heap:
            # get the node with the minimum estimated distance
            _, x, y, direction = heapq.heappop(heap)

            # check if the node has already been visited
            if (x, y, direction) in visited:
                continue

            # if the terminal state is reached record the path and return
            if end.is_eq(x, y, direction):
                self._record_path(start, end, parent_dict, g_dist[(x, y, direction)])
                return

            # mark the node as visited
            visited.add((x, y, direction))
            dist = g_dist[(x, y, direction)]

            # traverse the neighboring states
            for (
                new_x,
                new_y,
                new_direction,
                safe_cost,
                motion,
            ) in self._get_neighboring_states(x, y, direction):

                # check if the new state has already been visited
                if (new_x, new_y, new_direction) in visited:
                    continue

                if (
                    x,
                    y,
                    direction,
                    new_x,
                    new_y,
                    new_direction,
                ) not in self.motion_table and (
                    new_x,
                    new_y,
                    new_direction,
                    x,
                    y,
                    direction,
                ) not in self.motion_table:
                    # only need to store one of the two directions as the other will be the opposite
                    self.motion_table[
                        (x, y, direction, new_x, new_y, new_direction)
                    ] = motion

                # calculate the cost of robot rotation
                rotation_cost = TURN_FACTOR * Direction.rotation_cost(
                    direction, new_direction
                )
                if rotation_cost == 0:
                    rotation_cost = 1

                # calculate the cost of robot reversing
                reverse_cost = REVERSE_FACTOR * motion.reverse_cost()
                if reverse_cost == 0:
                    reverse_cost = 1

                # calculate the cost of robot half-turning
                half_turn_cost = HALF_TURN_FACTOR * motion.half_turn_cost()
                if half_turn_cost == 0:
                    half_turn_cost = 1

                motion_cost = reverse_cost * half_turn_cost * rotation_cost

                # calculate the cost of robot rotation
                movement_cost = motion_cost + safe_cost

                # check if there is a screenshot penalty
                if end.is_eq(new_x, new_y, new_direction):
                    screenshot_cost = end.penalty
                else:
                    screenshot_cost = 0

                # total cost f = g + h = safe_cost + rot_cost + screenshot_cost + dist + h (estimated distance)
                total_cost = (
                    dist
                    + movement_cost
                    + screenshot_cost
                    + self._estimate_distance(
                        CellState(new_x, new_y, new_direction), end
                    )
                )

                # update the g distance if the new state has not been visited or the new cost is less than the previous cost
                if (new_x, new_y, new_direction) not in g_dist or g_dist[
                    (new_x, new_y, new_direction)
                ] > dist + movement_cost:
                    g_dist[(new_x, new_y, new_direction)] = (
                        dist + movement_cost + screenshot_cost
                    )

                    # add the new state to the heap
                    heapq.heappush(heap, (total_cost, new_x, new_y, new_direction))

                    # update the parent dict
                    parent_dict[(new_x, new_y, new_direction)] = (x, y, direction)

    def _get_neighboring_states(
        self, x, y, direction
    ):  # TODO: see the behavior of the robot and adjust...
        """
        Return a list of tuples with format:
        newX, newY, new_direction

        # Neighbors have the following format: {newX, newY, movement direction, safe cost, motion}
        # Neighbors are coordinates that fulfill the following criteria:
        # If moving in the same direction:
        #   - Valid position within bounds
        #   - Must be at least 4 units away in total (x+y)
        #   - Furthest distance must be at least 3 units away (x or y)
        # If it is exactly 2 units away in both x and y directions, safe cost = SAFECOST. Else, safe cost = 0
        """
        neighbors = []

        # Assume that after following this direction, the car direction is EXACTLY md
        for dx, dy, md in MOVE_DIRECTION:
            if md == direction:  # if the new direction == md
                # FORWARD
                if self.grid.reachable(x + dx, y + dy):  # go forward;
                    # Get safe cost of destination
                    safe_cost = self._calculate_safe_cost(x + dx, y + dy)
                    motion = Motion.FORWARD

                    neighbors.append((x + dx, y + dy, md, safe_cost, motion))

                # REVERSE
                if self.grid.reachable(x - dx, y - dy):  # go back;
                    # Get safe cost of destination
                    safe_cost = self._calculate_safe_cost(x - dx, y - dy)
                    motion = Motion.REVERSE
                    neighbors.append((x - dx, y - dy, md, safe_cost, motion))

                # half turns
                delta_x, delta_y = self._get_half_turn_displacement(direction)
                if direction == Direction.NORTH or direction == Direction.SOUTH:
                    # FORWARD_OFFSET_RIGHT
                    if self.grid.half_turn_reachable(x, y, x + delta_x, y + delta_y):
                        safe_cost = self._calculate_safe_cost(x + delta_x, y + delta_y)
                        motion = Motion.FORWARD_OFFSET_RIGHT
                        neighbors.append(
                            (x + delta_x, y + delta_y, md, safe_cost, motion)
                        )

                    # FORWARD_OFFSET_LEFT
                    if self.grid.half_turn_reachable(x, y, x - delta_x, y + delta_y):

                        safe_cost = self._calculate_safe_cost(x - delta_x, y + delta_y)
                        motion = Motion.FORWARD_OFFSET_LEFT
                        neighbors.append(
                            (x - delta_x, y + delta_y, md, safe_cost, motion)
                        )
                    # REVERSE_OFFSET_RIGHT
                    if self.grid.half_turn_reachable(x, y, x + delta_x, y - delta_y):

                        safe_cost = self._calculate_safe_cost(x + delta_x, y - delta_y)
                        motion = Motion.REVERSE_OFFSET_RIGHT
                        neighbors.append(
                            (x + delta_x, y - delta_y, md, safe_cost, motion)
                        )
                    # REVERSE_OFFSET_LEFT
                    if self.grid.half_turn_reachable(x, y, x - delta_x, y - delta_y):

                        safe_cost = self._calculate_safe_cost(x - delta_x, y - delta_y)
                        motion = Motion.REVERSE_OFFSET_LEFT
                        neighbors.append(
                            (x - delta_x, y - delta_y, md, safe_cost, motion)
                        )
                else:
                    # EAST or WEST
                    # FORWARD_OFFSET_RIGHT
                    if self.grid.half_turn_reachable(x, y, x + delta_x, y - delta_y):

                        safe_cost = self._calculate_safe_cost(x + delta_x, y - delta_y)
                        motion = Motion.FORWARD_OFFSET_RIGHT
                        neighbors.append(
                            (x + delta_x, y - delta_y, md, safe_cost, motion)
                        )

                    # FORWARD_OFFSET_LEFT
                    if self.grid.half_turn_reachable(x, y, x + delta_x, y + delta_y):

                        safe_cost = self._calculate_safe_cost(x + delta_x, y + delta_y)
                        motion = Motion.FORWARD_OFFSET_LEFT
                        neighbors.append(
                            (x + delta_x, y + delta_y, md, safe_cost, motion)
                        )

                    # REVERSE_OFFSET_RIGHT
                    if self.grid.half_turn_reachable(x, y, x - delta_x, y - delta_y):

                        safe_cost = self._calculate_safe_cost(x - delta_x, y - delta_y)
                        motion = Motion.REVERSE_OFFSET_RIGHT
                        neighbors.append(
                            (x - delta_x, y - delta_y, md, safe_cost, motion)
                        )

                    # REVERSE_OFFSET_LEFT
                    if self.grid.half_turn_reachable(x, y, x - delta_x, y + delta_y):

                        safe_cost = self._calculate_safe_cost(x - delta_x, y + delta_y)
                        motion = Motion.REVERSE_OFFSET_LEFT
                        neighbors.append(
                            (x - delta_x, y + delta_y, md, safe_cost, motion)
                        )

            else:  # consider 8 cases

                # Turning displacement is either 4-2 or 3-1
                delta_big = TURNS[0]
                delta_small = TURNS[1]

                # north -> east
                if direction == Direction.NORTH and md == Direction.EAST:
                    # FORWARD_RIGHT_TURN
                    if self.grid.turn_reachable(
                        x, y, x + delta_big, y + delta_small, direction
                    ):
                        safe_cost = self._calculate_safe_cost(
                            x + delta_big, y + delta_small
                        )
                        motion = Motion.FORWARD_RIGHT_TURN
                        neighbors.append(
                            (x + delta_big, y + delta_small, md, safe_cost + 10, motion)
                        )

                    # REVERSE_LEFT_TURN
                    if self.grid.turn_reachable(
                        x, y, x - delta_small, y - delta_big, direction
                    ):
                        safe_cost = self._calculate_safe_cost(
                            x - delta_small, y - delta_big
                        )
                        motion = Motion.REVERSE_LEFT_TURN
                        neighbors.append(
                            (x - delta_small, y - delta_big, md, safe_cost + 10, motion)
                        )

                # east -> north
                if direction == Direction.EAST and md == Direction.NORTH:
                    # FORWARD_LEFT_TURN
                    if self.grid.turn_reachable(
                        x, y, x + delta_small, y + delta_big, direction
                    ):
                        safe_cost = self._calculate_safe_cost(
                            x + delta_small, y + delta_big
                        )
                        motion = Motion.FORWARD_LEFT_TURN
                        neighbors.append(
                            (x + delta_small, y + delta_big, md, safe_cost + 10, motion)
                        )

                    # REVERSE_RIGHT_TURN
                    if self.grid.turn_reachable(
                        x, y, x - delta_big, y - delta_small, direction
                    ):
                        safe_cost = self._calculate_safe_cost(
                            x - delta_big, y - delta_small
                        )
                        motion = Motion.REVERSE_RIGHT_TURN
                        neighbors.append(
                            (x - delta_big, y - delta_small, md, safe_cost + 10, motion)
                        )

                # east -> south
                if direction == Direction.EAST and md == Direction.SOUTH:
                    # FORWARD_RIGHT_TURN
                    if self.grid.turn_reachable(
                        x, y, x + delta_small, y - delta_big, direction
                    ):
                        safe_cost = self._calculate_safe_cost(
                            x + delta_small, y - delta_big
                        )
                        motion = Motion.FORWARD_RIGHT_TURN
                        neighbors.append(
                            (x + delta_small, y - delta_big, md, safe_cost + 10, motion)
                        )

                    # REVERSE_LEFT_TURN
                    if self.grid.turn_reachable(
                        x, y, x - delta_big, y + delta_small, direction
                    ):
                        safe_cost = self._calculate_safe_cost(
                            x - delta_big, y + delta_small
                        )
                        motion = Motion.REVERSE_LEFT_TURN
                        neighbors.append(
                            (x - delta_big, y + delta_small, md, safe_cost + 10, motion)
                        )

                # south -> east
                if direction == Direction.SOUTH and md == Direction.EAST:
                    # FORWARD_LEFT_TURN
                    if self.grid.turn_reachable(
                        x, y, x + delta_big, y - delta_small, direction
                    ):
                        safe_cost = self._calculate_safe_cost(
                            x + delta_big, y - delta_small
                        )
                        motion = Motion.FORWARD_LEFT_TURN
                        neighbors.append(
                            (x + delta_big, y - delta_small, md, safe_cost + 10, motion)
                        )

                    # REVERSE_RIGHT_TURN
                    if self.grid.turn_reachable(
                        x, y, x - delta_small, y + delta_big, direction
                    ):
                        safe_cost = self._calculate_safe_cost(
                            x - delta_small, y + delta_big
                        )
                        motion = Motion.REVERSE_RIGHT_TURN
                        neighbors.append(
                            (x - delta_small, y + delta_big, md, safe_cost + 10, motion)
                        )

                # south -> west
                if direction == Direction.SOUTH and md == Direction.WEST:
                    # FORWARD_RIGHT_TURN
                    if self.grid.turn_reachable(
                        x, y, x - delta_big, y - delta_small, direction
                    ):
                        safe_cost = self._calculate_safe_cost(
                            x - delta_big, y - delta_small
                        )
                        motion = Motion.FORWARD_RIGHT_TURN
                        neighbors.append(
                            (x - delta_big, y - delta_small, md, safe_cost + 10, motion)
                        )

                    # REVERSE_LEFT_TURN
                    if self.grid.turn_reachable(
                        x, y, x + delta_small, y + delta_big, direction
                    ):
                        safe_cost = self._calculate_safe_cost(
                            x + delta_small, y + delta_big
                        )
                        motion = Motion.REVERSE_LEFT_TURN
                        neighbors.append(
                            (x + delta_small, y + delta_big, md, safe_cost + 10, motion)
                        )

                # west -> south
                if direction == Direction.WEST and md == Direction.SOUTH:
                    # FORWARD_LEFT_TURN
                    if self.grid.turn_reachable(
                        x, y, x - delta_small, y - delta_big, direction
                    ):
                        safe_cost = self._calculate_safe_cost(
                            x - delta_small, y - delta_big
                        )
                        motion = Motion.FORWARD_LEFT_TURN
                        neighbors.append(
                            (x - delta_small, y - delta_big, md, safe_cost + 10, motion)
                        )

                    # REVERSE_RIGHT_TURN
                    if self.grid.turn_reachable(
                        x, y, x + delta_big, y + delta_small, direction
                    ):
                        safe_cost = self._calculate_safe_cost(
                            x + delta_big, y + delta_small
                        )
                        motion = Motion.REVERSE_RIGHT_TURN
                        neighbors.append(
                            (x + delta_big, y + delta_small, md, safe_cost + 10, motion)
                        )

                # west -> north
                if direction == Direction.WEST and md == Direction.NORTH:
                    # FORWARD_RIGHT_TURN
                    if self.grid.turn_reachable(
                        x, y, x - delta_small, y + delta_big, direction
                    ):
                        safe_cost = self._calculate_safe_cost(
                            x - delta_small, y + delta_big
                        )
                        motion = Motion.FORWARD_RIGHT_TURN
                        neighbors.append(
                            (x - delta_small, y + delta_big, md, safe_cost + 10, motion)
                        )

                    # REVERSE_LEFT_TURN
                    if self.grid.turn_reachable(
                        x, y, x + delta_big, y - delta_small, direction
                    ):
                        safe_cost = self._calculate_safe_cost(
                            x + delta_big, y - delta_small
                        )
                        motion = Motion.REVERSE_LEFT_TURN
                        neighbors.append(
                            (x + delta_big, y - delta_small, md, safe_cost + 10, motion)
                        )

                # north <-> west
                if direction == Direction.NORTH and md == Direction.WEST:
                    # FORWARD_LEFT_TURN
                    if self.grid.turn_reachable(
                        x, y, x - delta_big, y + delta_small, direction
                    ):
                        safe_cost = self._calculate_safe_cost(
                            x - delta_big, y + delta_small
                        )
                        motion = Motion.FORWARD_LEFT_TURN
                        neighbors.append(
                            (x - delta_big, y + delta_small, md, safe_cost + 10, motion)
                        )

                    # REVERSE_RIGHT_TURN
                    if self.grid.turn_reachable(
                        x, y, x + delta_small, y - delta_big, direction
                    ):
                        safe_cost = self._calculate_safe_cost(
                            x + delta_small, y - delta_big
                        )
                        motion = Motion.REVERSE_RIGHT_TURN
                        neighbors.append(
                            (x + delta_small, y - delta_big, md, safe_cost + 10, motion)
                        )

        return neighbors

    def _calculate_safe_cost(self, new_x: int, new_y: int) -> int:
        """
        calculates the safe cost of moving to a new position, considering obstacles that the robot might touch.
        Currently, the function checks 2 units in each direction.
        """
        padding = 2
        for obj in self.grid.obstacles:
            if abs(obj.x - new_x) <= padding and abs(obj.y - new_y) <= padding:
                return SAFE_COST
            if abs(obj.y - new_y) <= padding and abs(obj.x - new_x) <= padding:
                return SAFE_COST
        return 0

    def _record_path(self, start: CellState, end: CellState, parent: dict, cost: int):
        """
        Record the path between two states. Should be called only during the A* search.
        """
        # update the cost table for edges (start, end) and (end, start)
        self.cost_table[(start, end)] = cost
        self.cost_table[(end, start)] = cost

        # record the path
        path = []
        parent_pointer = (end.x, end.y, end.direction)
        while parent_pointer in parent:
            path.append(parent_pointer)
            parent_pointer = parent[parent_pointer]
        path.append(parent_pointer)

        # reverse the path and store it in the path table
        self.path_table[(start, end)] = path[::-1]
        self.path_table[(end, start)] = path

    @staticmethod
    def _estimate_distance(
        start: CellState,
        end: CellState,
        level=0,
    ) -> int:
        """
        Estimate the distance between two states.
        level 0: Manhattan distance
        level 1: Euclidean distance
        """
        horizontal_distance = start.x - end.x
        vertical_distance = start.y - end.y

        # Euclidean distance
        if level == 1:
            return math.sqrt(horizontal_distance**2 + vertical_distance**2)

        # Manhattan distance
        return abs(horizontal_distance) + abs(vertical_distance)

    @staticmethod
    def _get_visit_options(n):
        """
        Generate all possible visit options for n-digit binary numbers
        """
        max_len = bin(2**n - 1).count("1")
        strings = [bin(i)[2:].zfill(max_len) for i in range(2**n)]
        strings.sort(key=lambda x: x.count("1"), reverse=True)
        return strings

    @staticmethod
    def _generate_combinations(
        view_positions,
        index: int,
        current,
        result,
        num_iters: int,
    ):
        """
        Generate all possible combinations of the view positions
        """
        # if all the view positions have been visited, add the current combination to the result
        if index == len(view_positions):
            result.append(current.copy())
            return result

        # if the number of iterations is 0, return the result
        if num_iters == 0:
            return result

        # update the number of iterations
        num_iters -= 1

        # iterate over the view positions and generate the combinations for the next view position
        for i in range(len(view_positions[index])):
            current.append(i)
            result = MazeSolver._generate_combinations(
                view_positions, index + 1, current, result, num_iters
            )
            current.pop()

        return result

    @staticmethod
    def _get_half_turn_displacement(direction: Direction):
        # calculate delta small and delta big based on the direction
        if direction == Direction.NORTH:
            dx = HALF_TURNS[1]
            dy = HALF_TURNS[0]

        elif direction == Direction.SOUTH:
            dx = -HALF_TURNS[1]
            dy = -HALF_TURNS[0]

        elif direction == Direction.EAST:
            dx = HALF_TURNS[0]
            dy = HALF_TURNS[1]
        elif direction == Direction.WEST:
            dx = -HALF_TURNS[0]
            dy = -HALF_TURNS[1]
        else:
            raise ValueError(
                f"Invalid direction {direction}. This should never happen."
            )
        return dx, dy

    @staticmethod
    def _get_capture_relative_position(
        cell_state: CellState, obstacle: Obstacle
    ) -> str:
        """
        Get the relative position of the obstacle image wrt the robot and return L R or C
        """
        x, y, direction = cell_state.x, cell_state.y, cell_state.direction
        x_obs, y_obs = obstacle.x, obstacle.y

        # check if the obstacle is in front of the robot
        if direction == Direction.NORTH:
            if x_obs == x and y_obs > y:
                return "C"
            elif x_obs < x:
                return "L"
            else:
                return "R"
        elif direction == Direction.SOUTH:
            if x_obs == x and y_obs < y:
                return "C"
            elif x_obs < x:
                return "R"
            else:
                return "L"
        elif direction == Direction.EAST:
            if y_obs == y and x_obs > x:
                return "C"
            elif y_obs < y:
                return "R"
            else:
                return "L"
        elif direction == Direction.WEST:
            if y_obs == y and x_obs < x:
                return "C"
            elif y_obs < y:
                return "L"
            else:
                return "R"
        else:
            raise ValueError(
                f"Invalid direction {direction}. This should never happen."
            )

    def optimal_path_to_motion_path(self, optimal_path):
        """
        Convert the optimal path to a list of motions that the robot needs to take
        """
        # requires the path table to be filled and the optimal path to be calculated
        motion_path = []
        obstacle_id_list = []
        for i in range(len(optimal_path) - 1):
            from_state = optimal_path[i]
            to_state = optimal_path[i + 1]
            x, y, d = from_state.x, from_state.y, from_state.direction
            x_new, y_new, d_new = to_state.x, to_state.y, to_state.direction

            if (x_new, y_new, d_new, x, y, d) in self.motion_table:
                # if the motion is not found, check the reverse motion and get its opposite
                motion = self.motion_table[
                    (x_new, y_new, d_new, x, y, d)
                ].opposite_motion()
            elif (x, y, d, x_new, y_new, d_new) in self.motion_table:
                motion = self.motion_table[(x, y, d, x_new, y_new, d_new)]
            else:
                # if the motion is still not found, then the path is invalid
                raise ValueError(
                    f"Invalid path from {from_state} to {to_state}. This should never happen."
                )

            motion_path.append(motion)

            # check if the robot is taking a screenshot
            if to_state.screenshot_id:
                for idx in range(len(to_state.screenshot_id)):
                    motion_path.append(Motion.CAPTURE)
                    obstacle_id_list.append(to_state.screenshot_id[idx])

        return motion_path, obstacle_id_list
