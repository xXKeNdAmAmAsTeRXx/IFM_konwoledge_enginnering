from ipaddress import ip_network
from typing import Self, Any

import numpy as np
from .World import World



class LoadStartAndGoal:
    """
    state: is a array defining a blocks array
    """

    @staticmethod
    def load_from_txt(path:str):

        # utf-8-sig also copes with a BOM added by some Windows editors
        with open(path, "r", encoding="utf-8-sig") as f:
            lines = [line.strip() for line in f]

        layouts = [line for line in lines if line and not line.startswith("#")]
        if len(layouts) != 2:
            raise ValueError(
                f"{path}: expected 2 layout lines (start and target), "
                f"found {len(layouts)}"
            )

        parsed = []
        for name, line in zip(("start", "target"), layouts):
            try:
                parsed.append([int(token) for token in line.split()])
            except ValueError:
                raise ValueError(
                    f"{path}: {name} layout must contain only integers, got {line!r}"
                ) from None

        start, goal = np.array(parsed)
        print(start)
        state = LoadStartAndGoal(start, goal)

        return state


    def __init__(self, start:np.ndarray[np.int32], goal:np.ndarray[np.int32]):
        assert len(start) == len(goal)
        self.start = World(start)
        self.goal = World(goal)


