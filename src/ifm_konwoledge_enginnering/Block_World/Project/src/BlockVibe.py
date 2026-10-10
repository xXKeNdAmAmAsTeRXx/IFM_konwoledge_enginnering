import numpy as np


class BlockVibe:
    """
    state: is a array defining a blocks array

    """

    @staticmethod
    def _check_if_state_is_legal(state:np.ndarray[np.int32]) -> bool:

        n = len(state)
        if np.array([(block == idx + 1) for idx, block in enumerate(state)]).any():
            raise ValueError("Block cannot lie on itself")

        if np.array(state > n or state < 0).any():
            raise ValueError("Block cannot lie on not existing block")

        if  len(state[state!=0]) == np.unique(state[state != 0]):
            raise ValueError("Blocks cannot lie on the same block")

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
        with open(path, "r") as f:
            lines = f.readlines()








    def __init__(self,start:np.ndarray[np.int32], goal:np.ndarray[np.int32]):
        assert len(start)==len(goal)

        # Check is states are legal
        print("Checking initial State:")
        self._check_if_state_is_legal(start)

        print("Checking goal State:")
        self._check_if_state_is_legal(goal)

        #create class members
        self.state=start
        self.goal=goal