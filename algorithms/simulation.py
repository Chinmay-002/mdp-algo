from algorithms.algo import MazeSolver
from entities.entity import CellState, Obstacle
from tools.movement import Direction, Motion

import os
import json
import random
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib
import numpy as np

from typing import List, Tuple, Literal


class MazeSolverSimulation:
    """
    This class is used to run tests on the MazeSolver class.
    """

    debug_file = os.path.join(os.path.dirname(__file__), "../debug", "obstacles.json")
    debug = False
    debug_save = 0

    def __init__(
        self,
        maze_solver: MazeSolver = None,
        grid_size_x: int = None,
        grid_size_y: int = None,
        robot_x: int = None,
        robot_y: int = None,
        robot_direction: int = None,
    ):
        """
        Initialize the MazeSolverSimulation object with the MazeSolver object.
        If the MazeSolver object is not provided, the grid size, robot position, robot direction
        """
        self.maze_solver = (
            maze_solver
            if maze_solver
            else MazeSolver(
                size_x=grid_size_x,
                size_y=grid_size_y,
                robot_x=robot_x,
                robot_y=robot_y,
                robot_direction=robot_direction,
            )
        )

    def add_obstacles(self, obstacles):
        """
        Add a list of obstacles to the grid.

        The obstacles are a list of tuples, where each tuple contains the following:
        (x: int, y: int, direction: Direction, id: int)

        For example:

        sim.add_obstacles([(0, 19, Direction.SOUTH, 1),(19, 19, Direction.WEST, 2)])
        """
        for obstacle in obstacles:
            self.maze_solver.add_obstacle(*obstacle)

        if self.debug:
            print(
                f"Debug mode enabled. Storing obstacles to file {os.path.realpath(self.debug_file)}"
            )
            # store the obstacles in a json file
            self._save_obstacles(obstacles, save_number=self.debug_save)

    def generate_random_obstacles(self, num_obstacles: int):
        """
        Generate random obstacles in the grid. The obstacles are placed randomly in the grid. If debug mode is enabled,
        the obstacles are saved to a file, with the option to save them to one of the three save slots. For more details,
        regarding the save slots, see the MazeSolverSimulation.enable_debug() method.
        """
        grid_x = self.maze_solver.grid.size_x
        grid_y = self.maze_solver.grid.size_y
        padding = 5
        robot_state = self.maze_solver.robot.get_start_state()
        existing_obstacles = self.maze_solver.grid.obstacles
        # get the existing obstacles to get obstacle ids
        obs_nums = [int(obstacle.get_obstacle_id()) for obstacle in existing_obstacles]
        max_obs_num = max(obs_nums) if obs_nums else 0

        banned_gridsq = self._get_forbidden_area(
            [(robot_state.x, robot_state.y)], padding=padding
        )

        obstacles = []
        for i in range(num_obstacles):
            # generate obstacles with random x and y coordinates
            obs_x = random.randint(0 + padding, grid_x - 1 - padding)
            obs_y = random.randint(0 + padding, grid_y - 1 - padding)

            direction = None
            # check if the obstacle is in the forbidden area
            while (obs_x, obs_y) in banned_gridsq or direction is None:
                # while the obstacle is in the forbidden area, generate new coordinates
                obs_x = random.randint(0 + padding, grid_x - 1 - padding)
                obs_y = random.randint(0 + padding, grid_y - 1 - padding)
                if (obs_x, obs_y) in banned_gridsq:
                    continue

                # choose a random direction for the obstacle smartly
                direction = self._smart_direction_choice(
                    obs_x, obs_y, existing_obstacles
                )

            # update the forbidden area with the new obstacle coordinates
            banned_gridsq.update(self._get_forbidden_area([(obs_x, obs_y)]))

            # get the obstacle id
            obs_id = max_obs_num + i + 1

            # add the obstacle to the grid
            obstacles.append((obs_x, obs_y, direction, obs_id))
            self.maze_solver.add_obstacle(obs_x, obs_y, direction, obs_id)

        if self.debug:
            print(
                f"Debug mode enabled. Storing obstacles to file {os.path.realpath(self.debug_file)}"
            )
            # store the obstacles in a json file
            self._save_obstacles(obstacles, save_number=self.debug_save)

        return obstacles

    def load_obstacles(self, load_option=0):
        """
        Load obstacles from a file. The obstacles can be loaded from the last save or from one of the three save slots.
        load_option can be one of the following:
        1: Save slot 1
        2: Save slot 2
        3: Save slot 3
        0: Last save
        """
        if load_option == 0:
            obstacles = self._load_obstacles(option="last")["last"]
        elif load_option in [1, 2, 3]:
            obstacles = self._load_obstacles(option=f"{load_option}")[f"{load_option}"]
        else:
            # logging.error(f"Invalid load option {load_option}. It must be between 0 and 3.")
            return

        for obs in obstacles:
            obs_x, obs_y, direction, obs_id = (
                obs["x"],
                obs["y"],
                obs["direction"],
                obs["id"],
            )
            self.maze_solver.add_obstacle(obs_x, obs_y, direction, obs_id)
            # logging.info(f"Added obstacle at ({obs_x}, {obs_y}) with direction {direction} and id {obs_id}")
        return obstacles

    def reset_obstacles(self):
        """
        Resets the grid by removing all obstacles.
        """
        self.maze_solver.reset_obstacles()

    def get_optimal_path(self):
        """
        Calculates the optimal path for the robot to traverse the grid. Uses the current state of the grid to calculate the path.

        """
        print("Calculating optimal path...")
        return self.maze_solver.get_optimal_path(False)

    def plot_optimal_path_animation(self, verbose=False):
        """
        Calculates the optimal path for the robot to traverse the grid and plots an animation of the path.
        The animation is saved as a gif file in the animations folder to "optimal_path.gif".

        If verbose is set to True, the optimal path is printed to the console.
        """
        num_points = 3
        robot_state = self.maze_solver.robot.get_start_state()
        obstacles = self.maze_solver.grid.obstacles
        print("Calculating optimal path...")
        optimal_path, cost = self.maze_solver.get_optimal_path(False)

        if verbose:
            print(f"Optimal path with cost = {cost} calculated: ")
            for grid_sq in optimal_path:
                if grid_sq == optimal_path[-1]:
                    print(f"({grid_sq.x}, {grid_sq.y}) {grid_sq.direction.name}")
                else:
                    print(
                        f"({grid_sq.x}, {grid_sq.y}) {grid_sq.direction.name}",
                        end=" ->  ",
                    )

        print("Plotting optimal path animation")
        fig, ax = plt.subplots()

        # get data
        obs_x = [[], [], [], []]
        obs_y = [[], [], [], []]
        markers = ["^", ">", "v", "<"]

        for cell in obstacles:
            idx = markers.index(self._get_direction_symbol(cell.direction))

            obs_x[idx].append(cell.x)
            obs_y[idx].append(cell.y)

        path_x = [[], [], [], []]
        path_y = [[], [], [], []]

        screenshot_x, screenshot_y = [], []

        angle_x = [[], [], [], []]
        angle_y = [[], [], [], []]
        markers_angle = [45, 135, 225, 315]
        prev_cell = robot_state
        time = 0
        for cell in optimal_path:
            # creating intermediate points for turns
            if abs(prev_cell.x - cell.x) > 1 or abs(prev_cell.y - cell.y) > 1:
                angle = self._get_delta_angle(prev_cell.direction, cell.direction)
                if angle is None:
                    raise ValueError(
                        f"Invalid turn from {prev_cell.direction} to {cell.direction}. "
                        f"The location of the robot is {prev_cell.x}, {prev_cell.y}"
                        f" and the location of the next cell is {cell.x}, {cell.y}"
                    )
                elif angle == 0:
                    # half turn
                    angle = self._get_half_turn_angles(
                        prev_cell.x, prev_cell.y, cell.x, cell.y, prev_cell.direction
                    )

                angle_idx = markers_angle.index(angle)
                x_diff = cell.x - prev_cell.x
                y_diff = cell.y - prev_cell.y
                for i in range(1, 1 + num_points):
                    angle_x[angle_idx].append(
                        (prev_cell.x + i * x_diff / (1 + num_points), time)
                    )
                    angle_y[angle_idx].append(
                        (prev_cell.y + i * y_diff / (1 + num_points), time)
                    )
                    time += 1

            if cell.screenshot_id:
                screenshot_x.append((cell.x, time))
                screenshot_y.append((cell.y, time))

            idx = markers.index(self._get_direction_symbol(cell.direction))
            path_x[idx].append((cell.x, time))
            path_y[idx].append((cell.y, time))
            prev_cell = cell
            time += 1

        ax.set(xlim=(0, 20), ylim=(0, 20))
        ax.set_xticks(range(0, 21))
        ax.set_yticks(range(0, 21))

        def update(frame_num):
            ax.clear()
            ax.set(xlim=(0, 20), ylim=(0, 20))
            ax.set_xticks(range(0, 21))
            ax.set_yticks(range(0, 21))
            ax.grid()

            # robot
            ax.scatter(
                robot_state.x,
                robot_state.y,
                marker=self._get_direction_symbol(robot_state.direction),
                color="red",
                s=100,
            )

            data_x = [[], [], [], []]
            data_y = [[], [], [], []]
            data_x_turn = [[], [], [], []]
            data_y_turn = [[], [], [], []]

            for index in range(4):
                dir_x = path_x[index]
                dir_y = path_y[index]
                dir_x_turn = angle_x[index]
                dir_y_turn = angle_y[index]
                for num in range(len(dir_x)):
                    pos_x, t = dir_x[num]
                    pos_y, _ = dir_y[num]
                    if frame_num - 2 <= t <= frame_num:
                        data_x[index].append(pos_x)
                        data_y[index].append(pos_y)

                for num in range(len(dir_x_turn)):
                    posangle_x, t = dir_x_turn[num]
                    posangle_y, _ = dir_y_turn[num]
                    if frame_num - 2 <= t <= frame_num:
                        data_x_turn[index].append(posangle_x)
                        data_y_turn[index].append(posangle_y)

            x_image = [x_pos for x_pos, t in screenshot_x if frame_num > t]
            y_image = [y_pos for y_pos, t in screenshot_y if frame_num > t]

            if screenshot_x and screenshot_y:
                ax.scatter(x_image, y_image, color="green", s=100, marker="*")

            for j in range(len(markers)):
                if obs_x[j] and obs_y[j]:
                    ax.scatter(
                        obs_x[j], obs_y[j], marker=markers[j], color="black", s=300
                    )

                if data_x[j] and data_y[j]:
                    ax.scatter(
                        data_x[j], data_y[j], marker=markers[j], color="blue", s=80
                    )

                if data_x_turn[j] and data_y_turn[j]:
                    ax.scatter(
                        data_x_turn[j],
                        data_y_turn[j],
                        marker=(3, 0, markers_angle[j]),
                        color="green",
                        s=120,
                    )

        if verbose:
            print("Animating optimal path...")

        ani = animation.FuncAnimation(fig, update, frames=time + 5, interval=300)
        out_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../animations", "optimal_path.gif")
        )

        print(f"Saving animation to {out_path}")

        ani.save(out_path, writer="pillow")
        return optimal_path, cost

    def plot_animation_from_path(self, optimal_path, verbose=False):
        """
        Plots an animation of the robot traversing the grid based on the optimal path.
        """
        num_points = 3
        robot_state = self.maze_solver.robot.get_start_state()
        obstacles = self.maze_solver.grid.obstacles
        print("Plotting optimal path animation")
        fig, ax = plt.subplots()
        # get data
        obs_x = [[], [], [], []]
        obs_y = [[], [], [], []]
        markers = ["^", ">", "v", "<"]

        for cell in obstacles:
            idx = markers.index(self._get_direction_symbol(cell.direction))

            obs_x[idx].append(cell.x)
            obs_y[idx].append(cell.y)

        path_x = [[], [], [], []]
        path_y = [[], [], [], []]

        screenshot_x, screenshot_y = [], []

        angle_x = [[], [], [], []]
        angle_y = [[], [], [], []]
        markers_angle = [45, 135, 225, 315]
        prev_cell = robot_state
        time = 0
        for cell in optimal_path:
            # creating intermediate points for turns
            if abs(prev_cell.x - cell.x) > 1 or abs(prev_cell.y - cell.y) > 1:
                angle = self._get_delta_angle(prev_cell.direction, cell.direction)
                if angle is None:
                    raise ValueError(
                        f"Invalid turn from {prev_cell.direction} to {cell.direction}. "
                        f"The location of the robot is {prev_cell.x}, {prev_cell.y}"
                        f" and the location of the next cell is {cell.x}, {cell.y}"
                    )
                elif angle == 0:
                    # half turn
                    angle = self._get_half_turn_angles(
                        prev_cell.x, prev_cell.y, cell.x, cell.y, prev_cell.direction
                    )

                angle_idx = markers_angle.index(angle)
                x_diff = cell.x - prev_cell.x
                y_diff = cell.y - prev_cell.y
                for i in range(1, 1 + num_points):
                    angle_x[angle_idx].append(
                        (prev_cell.x + i * x_diff / (1 + num_points), time)
                    )
                    angle_y[angle_idx].append(
                        (prev_cell.y + i * y_diff / (1 + num_points), time)
                    )
                    time += 1

            if cell.screenshot_id:
                screenshot_x.append((cell.x, time))
                screenshot_y.append((cell.y, time))

            idx = markers.index(self._get_direction_symbol(cell.direction))
            path_x[idx].append((cell.x, time))
            path_y[idx].append((cell.y, time))
            prev_cell = cell
            time += 1

        ax.set(xlim=(0, 20), ylim=(0, 20))
        ax.set_xticks(range(0, 21))
        ax.set_yticks(range(0, 21))

        def update(frame_num):
            ax.clear()
            ax.set(xlim=(-1, 20), ylim=(-1, 20))
            ax.set_xticks(range(0, 21))
            ax.set_yticks(range(0, 21))
            ax.grid()

            # robot
            ax.scatter(
                robot_state.x,
                robot_state.y,
                marker=self._get_direction_symbol(robot_state.direction),
                color="red",
                s=100,
            )

            data_x = [[], [], [], []]
            data_y = [[], [], [], []]
            data_x_turn = [[], [], [], []]
            data_y_turn = [[], [], [], []]

            for index in range(4):
                dir_x = path_x[index]
                dir_y = path_y[index]
                dir_x_turn = angle_x[index]
                dir_y_turn = angle_y[index]
                for num in range(len(dir_x)):
                    pos_x, t = dir_x[num]
                    pos_y, _ = dir_y[num]
                    if frame_num - 2 <= t <= frame_num:
                        data_x[index].append(pos_x)
                        data_y[index].append(pos_y)

                for num in range(len(dir_x_turn)):
                    posangle_x, t = dir_x_turn[num]
                    posangle_y, _ = dir_y_turn[num]
                    if frame_num - 2 <= t <= frame_num:
                        data_x_turn[index].append(posangle_x)
                        data_y_turn[index].append(posangle_y)

            x_image = [x_pos for x_pos, t in screenshot_x if frame_num > t]
            y_image = [y_pos for y_pos, t in screenshot_y if frame_num > t]

            if screenshot_x and screenshot_y:
                ax.scatter(x_image, y_image, color="green", s=100, marker="*")

            for j in range(len(markers)):
                if obs_x[j] and obs_y[j]:
                    ax.scatter(
                        obs_x[j], obs_y[j], marker=markers[j], color="black", s=300
                    )

                if data_x[j] and data_y[j]:
                    ax.scatter(
                        data_x[j], data_y[j], marker=markers[j], color="blue", s=80
                    )

                if data_x_turn[j] and data_y_turn[j]:
                    ax.scatter(
                        data_x_turn[j],
                        data_y_turn[j],
                        marker=(3, 0, markers_angle[j]),
                        color="green",
                        s=120,
                    )

        if verbose:
            print("Animating optimal path...")

        ani = animation.FuncAnimation(fig, update, frames=time + 5, interval=300)
        out_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../animations", "optimal_path.gif")
        )

        print(f"Saving animation to {out_path}")

        ani.save(out_path, writer="pillow")

    def enable_debug(self, save_number=0):
        """
        Enable debug mode to save randomly generated obstacles to a file.
        save_number can be one of the following:
        1: Save to slot 1
        2: Save to slot 2
        3: Save to slot 3
        0: Only save to "last" slot (default)
        if save_number is between 1 and 3, the obstacles are saved to the corresponding save slot AND to the "last" slot.
        """
        self.debug_save = save_number
        self.debug = True
        if not os.path.exists(os.path.dirname(self.debug_file)):
            os.makedirs(os.path.dirname(self.debug_file))
        if not os.path.exists(self.debug_file):
            with open(self.debug_file, "w") as f:
                json.dump({"save_1": [], "save_2": [], "save_3": [], "last": []}, f)

    def disable_debug(self):
        """
        Disable debug mode and set the save number to 0.
        """
        self.debug = False
        self.debug_save = 0

    def _save_obstacles(self, obstacles, save_number=0):
        old_obs = self._load_obstacles(option="all")
        serialized_obstacles = []
        for obs in obstacles:
            obs_dict = {"x": obs[0], "y": obs[1], "direction": obs[2], "id": obs[3]}
            serialized_obstacles.append(obs_dict)
        if save_number == 0:
            pass
        elif save_number in [1, 2, 3]:
            old_obs[f"{save_number}"] = serialized_obstacles
        else:
            # logging.error(f"Invalid save number {save_number}. Its value must be between 0 and 3.")
            return

        # save the obstacles to last by default
        old_obs["last"] = serialized_obstacles

        try:
            with open(self.debug_file, "w") as f:
                json.dump(old_obs, f, indent=4)
        except IOError as e:
            # logging.error(f"Unable to save obstacles to file: {e}")
            pass

    def _load_obstacles(self, option="last") -> dict:
        try:
            with open(self.debug_file, "r") as f:
                serialized_obstacles = json.load(f)
        except IOError as e:
            # logging.info(f"Unable to load obstacles from file: {e}")
            return {"save_1": [], "save_2": [], "save_3": [], "last": []}

        if option == "all":
            return serialized_obstacles
        else:
            return {f"{option}": serialized_obstacles[option]}

    @staticmethod
    def _get_forbidden_area(obstacle_positions, padding=2) -> set:
        """
        function to get the grid squares where objects cannot be placed since there are already obstacles there.
        """
        forbidden_area = set()
        for obstacle_pos in obstacle_positions:
            x, y = obstacle_pos
            # add padding around the obstacle
            for i in range(-padding, padding + 1):
                for j in range(-padding, padding + 1):
                    forbidden_area.add((x + i, y + j))
        return forbidden_area

    @staticmethod
    def _get_direction_symbol(direction):
        if direction == Direction.NORTH:
            return "^"
        elif direction == Direction.EAST:
            return ">"
        elif direction == Direction.SOUTH:
            return "v"
        elif direction == Direction.WEST:
            return "<"

    @staticmethod
    def _get_delta_angle(direction1, direction2):
        # angle diff for turns only
        # 0 ^
        # 45 ^ <
        # 90 <
        # 135 v <
        # 180 v
        # 225 v >
        # 270 >
        # 315 ^ >
        # 360 ^
        if direction2 == direction1:
            # for half turns, no delta angle
            return 0

        if direction1 == Direction.NORTH:
            if direction2 == Direction.EAST:
                return 315
            elif direction2 == Direction.WEST:
                return 45

        elif direction1 == Direction.EAST:
            if direction2 == Direction.SOUTH:
                return 225
            elif direction2 == Direction.NORTH:
                return 315

        elif direction1 == Direction.SOUTH:
            if direction2 == Direction.WEST:
                return 135
            elif direction2 == Direction.EAST:
                return 225

        elif direction1 == Direction.WEST:
            if direction2 == Direction.NORTH:
                return 45
            elif direction2 == Direction.SOUTH:
                return 135

        return None

    @staticmethod
    def _is_approach_blocked(
        x: int,
        y: int,
        direction: Direction,
        obstacles: List[Obstacle],
        padding: int = 5,
    ) -> bool:
        """
        Check if the direction is valid based on the location of the obstacles.
        """
        mini_padding = padding // 2
        if direction == Direction.NORTH:
            for obstacle in obstacles:
                if (
                    x - mini_padding < obstacle.x < x + mini_padding
                    and y < obstacle.y < y + padding
                ):
                    return True
        elif direction == Direction.EAST:
            for obstacle in obstacles:
                if (
                    y - mini_padding < obstacle.y < y + mini_padding
                    and x < obstacle.x < x + padding
                ):
                    return True
        elif direction == Direction.SOUTH:
            for obstacle in obstacles:
                if (
                    x - mini_padding < obstacle.x < x + mini_padding
                    and y - padding < obstacle.y < y
                ):
                    return True
        elif direction == Direction.WEST:
            for obstacle in obstacles:
                if (
                    y - mini_padding < obstacle.y < y + mini_padding
                    and x - padding < obstacle.x < x
                ):
                    return True
        else:
            raise ValueError(f"Invalid direction {direction}")
        return False

    def _get_half_turn_angles(
        self, x: int, y: int, new_x: int, new_y: int, direction: Direction
    ) -> int:
        if direction == Direction.NORTH:
            if new_x > x:
                if new_y > y:
                    # FORWARD_OFFSET_RIGHT
                    return self._get_delta_angle(Direction.NORTH, Direction.EAST)
                elif new_y < y:
                    # REVERSE_OFFSET_RIGHT
                    return self._get_delta_angle(Direction.NORTH, Direction.WEST)
            else:
                if new_y > y:
                    # FORWARD_OFFSET_LEFT
                    return self._get_delta_angle(Direction.NORTH, Direction.WEST)
                elif new_y < y:
                    # REVERSE_OFFSET_LEFT
                    return self._get_delta_angle(Direction.NORTH, Direction.EAST)

        elif direction == Direction.EAST:
            if new_y > y:
                if new_x > x:
                    # FORWARD_OFFSET_RIGHT
                    return self._get_delta_angle(Direction.EAST, Direction.SOUTH)
                elif new_x < x:
                    # REVERSE_OFFSET_RIGHT
                    return self._get_delta_angle(Direction.EAST, Direction.NORTH)
            else:
                if new_x > x:
                    # FORWARD_OFFSET_LEFT
                    return self._get_delta_angle(Direction.EAST, Direction.NORTH)
                elif new_x < x:
                    # REVERSE_OFFSET_LEFT
                    return self._get_delta_angle(Direction.EAST, Direction.SOUTH)

        elif direction == Direction.SOUTH:
            if new_x > x:
                if new_y > y:
                    # FORWARD_OFFSET_RIGHT
                    return self._get_delta_angle(Direction.SOUTH, Direction.WEST)
                elif new_y < y:
                    # REVERSE_OFFSET_RIGHT
                    return self._get_delta_angle(Direction.SOUTH, Direction.EAST)
            else:
                if new_y > y:
                    # FORWARD_OFFSET_LEFT
                    return self._get_delta_angle(Direction.SOUTH, Direction.EAST)
                elif new_y < y:
                    # REVERSE_OFFSET_LEFT
                    return self._get_delta_angle(Direction.SOUTH, Direction.WEST)
        else:
            if new_y > y:
                if new_x > x:
                    # FORWARD_OFFSET_RIGHT
                    return self._get_delta_angle(Direction.WEST, Direction.NORTH)
                elif new_x < x:
                    # REVERSE_OFFSET_RIGHT
                    return self._get_delta_angle(Direction.WEST, Direction.SOUTH)
            else:
                if new_x > x:
                    # FORWARD_OFFSET_LEFT
                    return self._get_delta_angle(Direction.WEST, Direction.SOUTH)
                elif new_x < x:
                    # REVERSE_OFFSET_LEFT
                    return self._get_delta_angle(Direction.WEST, Direction.NORTH)
        return None

    def _smart_direction_choice(
        self,
        x: int,
        y: int,
        obstacles: List[Obstacle],
    ) -> Direction:
        """
        Choose the direction of the robot based on the location of the obstacles.
        """
        available_choices = []
        for direction in [
            Direction.NORTH,
            Direction.EAST,
            Direction.SOUTH,
            Direction.WEST,
        ]:

            if self._is_approach_blocked(x, y, direction, obstacles):
                continue

            if self._unreachable_location(x, y, direction):
                continue

            available_choices.append(direction)

        if not available_choices:
            return None
        return random.choice(available_choices)

    def _unreachable_location(
        self, x: int, y: int, direction: Direction, padding: int = 6
    ) -> bool:
        """
        Check if the location is unreachable based on the location of the obstacles.
        """
        if direction == Direction.NORTH:
            if y > self.maze_solver.grid.size_y - padding:
                return True
        elif direction == Direction.EAST:
            if x > self.maze_solver.grid.size_x - padding:
                return True
        elif direction == Direction.SOUTH:
            if y < padding:
                return True
        elif direction == Direction.WEST:
            if x < padding:
                return True
        else:
            raise ValueError(f"Invalid direction {direction}")
        return False
