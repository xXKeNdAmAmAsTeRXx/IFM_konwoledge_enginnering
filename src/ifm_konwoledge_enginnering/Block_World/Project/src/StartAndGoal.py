from typing import Self

import numpy as np



class StartAndGoal:
    """
    state: is a array defining a blocks array

    """

    @staticmethod
    def _check_if_state_is_legal(state:np.ndarray[np.int32]) -> bool:

        n = len(state)
        if np.array([(block == idx + 1) for idx, block in enumerate(state)]).any():
            raise ValueError("Block cannot lie on itself")

        if np.array((state > n) | (state < 0)).any():
            raise ValueError("Block cannot lie on not existing block")

        on_blocks = state[state != 0]
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
                current = int(state[current - 1])

        return True

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
        state = StartAndGoal(start, goal)

        return state


    def __init__(self,start:np.ndarray[np.int32], goal:np.ndarray[np.int32]):
        assert len(start)==len(goal)

        # Check is states are legal
        print("Checking initial State:")
        self._check_if_state_is_legal(start)

        print("Checking goal State:")
        self._check_if_state_is_legal(goal)

        #create class members
        self.start=start
        self.goal=goal