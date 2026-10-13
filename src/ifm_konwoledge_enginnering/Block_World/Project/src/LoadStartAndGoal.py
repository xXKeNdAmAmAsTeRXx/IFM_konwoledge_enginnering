from ipaddress import ip_network
from typing import Self, Any

import numpy as np
from .Move import Move
from .BlockState import BlockState



class LoadStartAndGoal:
    """
    state: is a array defining a blocks array
    """

    @staticmethod
    def _check_if_placement_is_legal(placement:np.ndarray[np.int32]) -> bool:

        n = len(placement)
        if np.array([(block == idx + 1) for idx, block in enumerate(placement)]).any():
            raise ValueError("Block cannot lie on itself")

        if np.array((placement > n) | (placement < 0)).any():
            raise ValueError("Block cannot lie on not existing block")

        on_blocks = placement[placement != 0]
        values, counts = np.unique(on_blocks, return_counts=True)
        if (counts > 1).any():
            raise ValueError(
                f"Blocks cannot lie on the same block: block {values[counts > 1][0]} has more than one block on it"
            )

        for i in range(n):
            visited = set()
            current = i + 1

            while current != 0:
                if current in visited:
                    raise ValueError("Cycle detected.")

                visited.add(current)
                current = int(placement[current - 1])

        return True

    @staticmethod
    def _set_BlockState(placement:np.ndarray[np.int32]) -> BlockState:
        state = BlockState()
        for idx, on in enumerate(placement):
            state.id = idx + 1
            state.on = on
            state.on_table = True if on==0 else False
            state.clear = False if np.isin(on, state.id) else True

        return state

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

        # Check is states are legal
        print("Checking initial State...")
        self._check_if_placement_is_legal(start)
        print("OK\n")

        print("Checking goal State...")
        self._check_if_placement_is_legal(goal)
        print("OK\n")

        start_states = np.ndarray(shape=(len(start),), dtype=BlockState)
        for block in start:
            start_states[block] = self._set_BlockState(block)

        goal_states = np.ndarray(shape=(len(goal),), dtype=BlockState)
        for block in goal:
            goal_states[block] = self._set_BlockState(block)

        #create class members
        self.start=start
        self.start_states = start_states
        self.goal=goal
        self.goal_states = goal_states

    def all_possible_movements(self) -> list[Any]:
        #TODO: all possible movments based on current BlockStates

        pass



    def update_move(self, move:np.ndarray[np.int32]):
        #TODO: Update Block Move
        pass
