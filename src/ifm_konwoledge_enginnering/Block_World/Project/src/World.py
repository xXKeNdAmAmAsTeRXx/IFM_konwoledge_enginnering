import numpy as np
from .BlockState import BlockState
from .Move import Move



class World:
    """
    The World class represents current placement and states of each block
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
    def _set_BlockState(placement: np.ndarray[np.int32]) -> BlockState:
        state = BlockState()
        for idx, on in enumerate(placement):
            state.id = idx + 1
            state.on = on
            state.on_table = True if on == 0 else False
            state.clear = False if np.isin(on, state.id) else True

        return state

    def update(self, move: Move) -> None:

        # Update Placement
        new_placement = self.placement.copy()
        new_placement[move.moving - 1] = move.destination
        assert self._check_if_placement_is_legal(new_placement), "This Move is not legal"

        self.placement= new_placement

        # Update states
        self.states[Move.moving - 1].update(move)
        self.states[Move.destination - 1].update(move)

    def __init__(self, placement:np.ndarray[np.int32]):
        assert self._check_if_placement_is_legal(placement), "This block placement cannot exist"

        states = np.ndarray(shape=(len(placement),), dtype=BlockState)
        for block in placement:
            states[block] = self._set_BlockState(block)

        self.states = states
        self.placement = placement