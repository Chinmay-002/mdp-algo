from algorithms.algo import MazeSolver
from entities.entity import Obstacle
from tools.movement import Direction, CommandGenerator, Motion
from algorithms.simulation import MazeSolverSimulation

sim = MazeSolverSimulation(
    grid_size_x=20,
    grid_size_y=20,
    robot_x=1,
    robot_y=1,
    robot_direction=Direction.NORTH,
)


sim.enable_debug(0)

# sim.load_obstacles(0)  # load obstacles from file

# sim.generate_random_obstacles(4)  # uncomment to generate random obstacles

obstacles = [
    (0, 17, Direction.EAST, 1),
    (5, 12, Direction.SOUTH, 2),
    (7, 5, Direction.NORTH, 3),
    (15, 2, Direction.WEST, 4),
    (11, 14, Direction.EAST, 5),
    (16, 19, Direction.SOUTH, 6),
    (19, 9, Direction.WEST, 7),
]  # obstacles from race day. Comment out when generating random obstacles

sim.add_obstacles(obstacles)

optimal_path, cost = sim.maze_solver.get_optimal_path()


# motions, obstacle_ids = sim.maze_solver.optimal_path_to_motion_path(optimal_path)  # uncomment to generate commands
# command_generator = CommandGenerator()
# commands = command_generator.generate_commands(motions, obstacle_ids)

sim.plot_animation_from_path(optimal_path)
