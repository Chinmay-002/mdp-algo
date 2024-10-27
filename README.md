# CZ3004/SC2079 Multidisciplinary Design Project (MDP) Algorithm


## Overview

---
This is a repo containing the algorithm used by Group 30 for the Multidisciplinary Design Project (MDP) in AY24-25 S1. Final Result:
- Task 1 - 1st Place (52s for 7 objects)
- Task 2 - 4th Place 

## Setup 

---
1. Clone the repository
2. Open the terminal and navigate to the repository root
3. Create a virtual environment using the python you have installed.
 _NOTE: this project has been tested only using Python 3.8_
    ```bash
    python3 -m venv mdp-venv
    ```
4. Activate the virtual environment
    ```bash
    source mdp-venv/bin/activate
    ```
5. Install required packages
    ```bash
    pip install -r requirements.txt
    ```

## Running the Simulation

---
1. Navigate to the repository root  
2. source the virtual environment you created earlier
    ```bash
    source mdp-venv/bin/activate
    ```
3. Optionally modify `main.py` to change the simulation parameters according to your simulation requirements. You can 
refer to the Simulation class-it's functionality provided in `simulation.py`.

4. Run the simulation using the following command
    ```bash
    python main.py
    ```
5. After the script is complete, if `sim.plot_optimal_path_animation()` is called in `main.py`, the resulting gif of
the simulation will be saved in the `animations` directory. The gif will be named `optimal_path.gif`.

_NOTE: For 7-8 objects, the optimal path calculation can take upto 40s. This time can be redeced by reducing the number 
of view states searched, and a few other optimisations. We found that the current setting allowing the algorithm to search 
a good amount of view states while not taking too much time._

Example of the simulation output:  

![Simulation Output](https://github.com/Chinmay-002/mdp-algo/blob/main/animations/optimal_path.gif)

## Hyperparameters and Tuning

---

<details>
  <summary>Click to expand</summary>

You can find most of the hyperparameters in the consts.py file. The hyperparameters are as follows:

### Algo hyperparams:

`TURN_FACTOR`: The cost of turning the robot. The higher the value, the less likely the robot is to turn.

`HALF_TURN_FACTOR`: The cost of turning the robot by 180 degrees. The higher the value, the higher the chance the root will turn only when it needs to.

`REVERSE_FACTOR`: The cost of reversing the robot. The higher the value, the less likely the robot is to reverse.

`HALF_TURN_FACTOR`: The cost of turning the robot by 180 degrees. The higher the value, 
the higher the chance the root make offset turns.

`SCREENSHOT_COST`: The cost of taking an image off center. The higher the value, the less likely the robot is to take an image off center.

`TOO_CLOSE_COST` : The cost of being too close to an object while taking an image

`TURN_PADDING`: Padding for the robot to turn. The higher the value, the more space the robot will need to make a turn. Must be tuned with `MID_TURN_PADDING`.

`MID_TURN_PADDING`: Padding for the robot to turn. The higher the value, the more space the robot will need to make a turn. Must be tuned with `TURN_PADDING`.

### Hardware hyperparams:
`TURNS`: The number of grid squares the robot moves for a turn on each axis. This must be tuned based on real robot movement.

`HALF_TURNS`: The number of grid squares the robot moves for a half turn on each axis. This must be tuned based on real robot movement. 

For more on turning the hardware movements to fit software requirements, see the [`tools/movement.py`](https://github.com/Chinmay-002/mdp-algo/blob/main/tools/movement.py) for the `CommandGenerator`

### Deprecated hyperparams: 

`SAFE_COST`: The cost in case the robot is too close to an object

</details>

## Acknowledgements

---
<details>
  <summary>Click to expand</summary>

I used [pyesonekyaw](https://github.com/pyesonekyaw)'s MDP algorithm as a starting point, but reimplemented it and improved it significantly by adding new functionality. Multiple modifications were also made in order to fit the requirements specified by the other teams in my MDP group (AY 24-25 S1 Group 30).

The original code can be found [in this repository](https://github.com/pyesonekyaw/CZ3004-SC2079-MDP-Algorithm).
</details>

## Contributors

---

[Lucas Ng Wei Jie](https://github.com/LucasNgWeiJie)
