from enum import Enum


class Direction(int, Enum):
    """
    Enum class representing the directions an entity can face
    """

    NORTH = 0
    SOUTH = 1
    EAST = 2
    WEST = 3
    SKIP = 4

    def __int__(self):
        return self.value

    @staticmethod
    def rotation_cost(d1, d2):
        """
        Calculate the cost of turning from direction d1 to direction d2
        For a regular left or right turn, the cost is 2. if the robot does not turn, the cost is 0.
        """
        if d1 == Direction.NORTH:
            if d2 in [Direction.EAST, Direction.WEST]:
                diff = 1
            elif d2 == Direction.NORTH:
                return 0
            else:
                raise ValueError("Robot cannot turn from north to south")

        elif d1 == Direction.SOUTH:
            if d2 in [Direction.EAST, Direction.WEST]:
                diff = 1
            elif d2 == Direction.SOUTH:
                return 0
            else:
                raise ValueError("Robot cannot turn from south to north")

        elif d1 == Direction.EAST:
            if d2 in [Direction.NORTH, Direction.SOUTH]:
                diff = 1
            elif d2 == Direction.EAST:
                return 0
            else:
                raise ValueError("Robot cannot turn from east to west")

        elif d1 == Direction.WEST:
            if d2 in [Direction.NORTH, Direction.SOUTH]:
                diff = 1
            elif d2 == Direction.WEST:
                return 0
            else:
                raise ValueError("Robot cannot turn from west to east")

        else:
            raise ValueError(f"direction {d1} is not a valid direction.")

        return diff

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class Motion(int, Enum):
    """
    Enum class for the motion of the robot between two cells
    """

    # the robot can move in 10 different ways from one cell to another
    # designed so that 10 - motion = opposite motion
    FORWARD_LEFT_TURN = 0
    FORWARD_OFFSET_LEFT = 1
    FORWARD = 2
    FORWARD_OFFSET_RIGHT = 3
    FORWARD_RIGHT_TURN = 4

    REVERSE_LEFT_TURN = 10
    REVERSE_OFFSET_RIGHT = 9
    REVERSE = 8
    REVERSE_OFFSET_LEFT = 7
    REVERSE_RIGHT_TURN = 6

    # the robot can also capture an image
    CAPTURE = 1000

    def __int__(self):
        return self.value

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def __eq__(self, other: "Motion"):
        return self.value == other.value

    def opposite_motion(self):
        """
        Get the opposite motion of the current motion.
        E.g. if the current motion is FORWARD, the opposite motion is REVERSE.
        """
        if self == Motion.CAPTURE:
            return Motion.CAPTURE

        opp_val = 10 - self.value
        if opp_val == 5 or opp_val < 0 or opp_val > 10:
            raise ValueError(f"Invalid motion {self}. This should never happen.")

        return Motion(opp_val)

    def is_combinable(self):
        """
        Check if the motion is combinable with other motions.

        Note: Updates so that only forward/reverse motions are combinable (due to offsets added to turns while tuning).
        """
        return self.value in [2, 8]

    def reverse_cost(self):
        """
        If the motion is a reverse motion, return the cost of the motion.
        Returns:
            int:
        """
        if self == Motion.CAPTURE:
            raise ValueError("Capture motion does not have a reverse cost")

        if self in [
            Motion.REVERSE_OFFSET_RIGHT,
            Motion.REVERSE_OFFSET_LEFT,
            Motion.REVERSE_LEFT_TURN,
            Motion.REVERSE_RIGHT_TURN,
            Motion.REVERSE,
        ]:
            return 1
        else:
            return 0

    def half_turn_cost(self):
        """
        If the motion is a half turn motion, return the cost of the motion.
        Returns:
            int:
        """
        if self in [
            Motion.FORWARD_OFFSET_LEFT,
            Motion.FORWARD_OFFSET_RIGHT,
            Motion.REVERSE_OFFSET_LEFT,
            Motion.REVERSE_OFFSET_RIGHT,
        ]:
            return 1
        else:
            return 0


class CommandGenerator:
    """
    A class to generate commands for the robot to follow. See STM repo for commands format.
    """

    SEP = "|"
    END = ""
    RCV = "r"
    FIN = "FIN"
    INFO_MARKER = "M"
    INFO_DIST = "D"

    # Flags
    FORWARD_DIST_TARGET = "T"
    FORWARD_DIST_AWAY = "W"
    BACKWARD_DIST_TARGET = "t"
    BACKWARD_DIST_AWAY = "w"

    # IR Sensors based motion
    FORWARD_IR_DIST_L = "L"
    FORWARD_IR_DIST_R = "R"
    BACKWARD_IR_DIST_L = "l"
    BACKWARD_IR_DIST_R = "r"

    # unit distance
    UNIT_DIST = 10

    # TUNABLE VALUES (these are based on values we got from our robot)
    # sharpness of turn angles
    FORWARD_TURN_ANGLE_LEFT = 25
    FORWARD_TURN_ANGLE_RIGHT = 25
    BACKWARD_TURN_ANGLE_LEFT = 25
    BACKWARD_TURN_ANGLE_RIGHT = 25

    # final turn angles
    FORWARD_RIGHT_FINAL_ANGLE = 86
    FORWARD_LEFT_FINAL_ANGLE = 87
    BACKWARD_RIGHT_FINAL_ANGLE = 89
    BACKWARD_LEFT_FINAL_ANGLE = 88

    def __init__(self, straight_speed: int = 50, turn_speed: int = 50):
        """
        A class to generate commands for the robot to follow

        Args:
            straight_speed (int): speed of the robot when moving straight (Max: 100)
            turn_speed (int): speed of the robot when turning (Max: 100)

        Recommendations:
            - straight_speed: 50
            - turn_speed: 50

        """
        self.straight_speed = straight_speed
        self.turn_speed = turn_speed

    def _generate_command(self, motion: Motion, num_motions: int = 1):
        if num_motions > 1:
            dist = num_motions * self.UNIT_DIST
            # angle = num_motions * 90  # useful when combining turns which has been disabled due to tuning
        else:
            dist = self.UNIT_DIST
            # angle = 90  # useful when combining turns which has been disabled due to tuning

        # for each turn you can tune it further by adding an offset in the respective direction (by adding a straight command)
        if motion == Motion.FORWARD:
            return [
                f"{self.FORWARD_DIST_TARGET}{self.straight_speed}{self.SEP}0{self.SEP}{dist}{self.END}"
            ]
        elif motion == Motion.REVERSE:
            return [
                f"{self.BACKWARD_DIST_TARGET}{self.straight_speed}{self.SEP}0{self.SEP}{dist}{self.END}"
            ]
        elif motion == Motion.FORWARD_LEFT_TURN:
            cmd1 = f"{self.FORWARD_DIST_TARGET}{self.turn_speed}{self.SEP}-{self.FORWARD_TURN_ANGLE_LEFT}{self.SEP}{self.FORWARD_LEFT_FINAL_ANGLE}{self.END}"
            # move robot front to make the robot end in the middle of the cell
            cmd2 = f"{self.FORWARD_DIST_TARGET}{self.straight_speed}{self.SEP}0{self.SEP}{6}{self.END}"

        elif motion == Motion.FORWARD_RIGHT_TURN:
            cmd1 = f"{self.FORWARD_DIST_TARGET}{self.straight_speed}{self.SEP}0{self.SEP}{5}{self.END}"
            cmd2 = f"{self.FORWARD_DIST_TARGET}{self.turn_speed}{self.SEP}{self.FORWARD_TURN_ANGLE_RIGHT}{self.SEP}{self.FORWARD_RIGHT_FINAL_ANGLE}{self.END}"  # 88
            # move robot front to make the robot end in the middle of the cell
            cmd3 = f"{self.FORWARD_DIST_TARGET}{self.straight_speed}{self.SEP}0{self.SEP}{12}{self.END}"
            return [cmd1, cmd2, cmd3]

        elif motion == Motion.REVERSE_LEFT_TURN:
            # reverse first before turning to make the robot end in the middle of the cell
            cmd1 = f"{self.BACKWARD_DIST_TARGET}{self.straight_speed}{self.SEP}0{self.SEP}{6}{self.END}"
            cmd2 = f"{self.BACKWARD_DIST_TARGET}{self.turn_speed}{self.SEP}-{self.BACKWARD_TURN_ANGLE_LEFT}{self.SEP}{self.BACKWARD_LEFT_FINAL_ANGLE}{self.END}"
            # cmd3 = f"{self.BACKWARD_DIST_TARGET}{self.straight_speed}{self.SEP}0{self.SEP}{3}{self.END}"
            return [cmd1, cmd2]

        elif motion == Motion.REVERSE_RIGHT_TURN:
            # reverse first before turning to make the robot end in the middle of the cell
            cmd1 = f"{self.BACKWARD_DIST_TARGET}{self.straight_speed}{self.SEP}0{self.SEP}{7}{self.END}"
            cmd2 = f"{self.BACKWARD_DIST_TARGET}{self.turn_speed}{self.SEP}{self.BACKWARD_TURN_ANGLE_RIGHT}{self.SEP}{self.BACKWARD_RIGHT_FINAL_ANGLE}{self.END}"
            cmd3 = f"{self.BACKWARD_DIST_TARGET}{self.straight_speed}{self.SEP}0{self.SEP}{4}{self.END}"
            return [cmd1, cmd2, cmd3]

        # cannot combine with other motions
        elif motion == Motion.FORWARD_OFFSET_LEFT:
            # break it down into 2 steps
            cmd1 = f"{self.FORWARD_DIST_TARGET}{self.turn_speed}{self.SEP}{-14}{self.SEP}{21}{self.END}"
            cmd2 = f"{self.FORWARD_DIST_TARGET}{self.turn_speed}{self.SEP}{17}{self.SEP}{21}{self.END}"
        elif motion == Motion.FORWARD_OFFSET_RIGHT:
            # break it down into 2 steps
            cmd1 = f"{self.FORWARD_DIST_TARGET}{self.turn_speed}{self.SEP}{14}{self.SEP}{21}{self.END}"
            cmd2 = f"{self.FORWARD_DIST_TARGET}{self.straight_speed}{self.SEP}{-17}{self.SEP}{21}{self.END}"
        elif motion == Motion.REVERSE_OFFSET_LEFT:
            # break it down into 2 steps
            cmd1 = f"{self.BACKWARD_DIST_TARGET}{self.turn_speed}{self.SEP}{-15}{self.SEP}{24}{self.END}"
            cmd2 = f"{self.BACKWARD_DIST_TARGET}{self.turn_speed}{self.SEP}{25}{self.SEP}{25}{self.END}"
        elif motion == Motion.REVERSE_OFFSET_RIGHT:
            # break it down into 2 steps
            cmd1 = f"{self.BACKWARD_DIST_TARGET}{self.turn_speed}{self.SEP}{15}{self.SEP}{24}{self.END}"
            cmd2 = f"{self.BACKWARD_DIST_TARGET}{self.turn_speed}{self.SEP}{-25}{self.SEP}{25}{self.END}"
        else:
            raise ValueError(f"Invalid motion {motion}. This should never happen.")
        return [cmd1, cmd2]

    def generate_commands(self, motions, obstacle_ids, testing=False):
        """
        Generate commands based on the list of motions
        """
        snap_count = 0
        if not motions:
            return []
        commands = []
        prev_motion = motions[0]
        # cur_cmd = self._generate_command(prev_motion)
        num_motions = 1
        for motion in motions[1:]:
            # if combinable motions
            if motion == prev_motion and motion.is_combinable():
                # increment the number of combined motions
                num_motions += 1
            # convert prev motion to command
            else:
                if prev_motion == Motion.CAPTURE:
                    commands.append(f"M0|0|0")
                    commands.append(f"SNAP{obstacle_ids[snap_count]}")
                    snap_count += 1
                    prev_motion = motion
                    continue
                if testing:
                    raise ValueError("This function is DEPRECATED!!")
                else:
                    cur_cmd = self._generate_command(prev_motion, num_motions)
                commands.extend(cur_cmd)
                num_motions = 1

            prev_motion = motion

        # add the last command
        if testing:
            raise ValueError("This function is DEPRECATED!!")
        else:
            if prev_motion == Motion.CAPTURE:
                commands.append(f"M0|0|0")
                commands.append(f"SNAP{obstacle_ids[snap_count]}")
            else:
                cur_cmd = self._generate_command(prev_motion, num_motions)
                commands.extend(cur_cmd)

        # add the final command
        commands.append(f"{self.FIN}")
        commands = CommandGenerator._post_process_commands(commands)
        return commands

    @staticmethod
    def _post_process_commands(commands: list):
        """
        Merge commands that can be combined. Currently only merges forward and backward commands
        """
        merged_commands = []
        prev_cmd = None

        for cmd in commands:
            if prev_cmd:
                # check if command is snap, D0|0|0 or FIN
                if cmd == "FIN" or cmd.startswith("SNAP") or cmd == "M0|0|0":
                    merged_commands.append(prev_cmd)
                    prev_cmd = None
                    merged_commands.append(cmd)
                    continue

                # check if commands can be merged
                merged_cmd = CommandGenerator._merge_commands(prev_cmd, cmd)
                if merged_cmd:
                    prev_cmd = merged_cmd
                else:
                    merged_commands.append(prev_cmd)
                    prev_cmd = cmd
            else:
                if cmd == "FIN" or cmd.startswith("SNAP") or cmd == "M0|0|0":
                    merged_commands.append(cmd)
                    continue
                prev_cmd = cmd
        # last command always FIN, so no need to check
        return merged_commands

    @staticmethod
    def _merge_commands(cmd1: str, cmd2: str):
        """
        Merge two commands that can be combined
        NOTE: This function can only merge forward and backward commands
        """
        result1, result2 = cmd1.split("|"), cmd2.split("|")

        # angles have to be 0
        angle1, angle2 = int(result1[1]), int(result2[1])
        if angle1 != angle2 or angle1 != 0:
            return None

        dist1, dist2 = int(result1[2]), int(result2[2])

        # speed of commands is always the same
        motion1, motion2 = result1[0][0], result2[0][0]

        if motion1 != motion2:
            if dist1 > dist2:
                # choose motion1
                used_motion = motion1
                used_dist = dist1 - dist2
            else:
                used_motion = motion2
                used_dist = dist2 - dist1
        else:
            used_motion = motion1
            used_dist = dist1 + dist2

        speed = result1[0][1:]
        return f"{used_motion}{speed}|{0}|{used_dist}"
