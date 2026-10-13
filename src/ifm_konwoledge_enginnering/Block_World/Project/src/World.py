from typing import List

import numpy as np
from .BlockState import BlockState
from .Move import Move



class World:
    """
    Store the placement and state of every block in a world.

    Attributes:
        placement: Support-block ID for each block; 0 represents the table.
        states: BlockState objects corresponding to the blocks in placement.
    """

    @staticmethod
    def _check_if_placement_is_legal(placement:np.ndarray[np.int32]) -> bool:
        """Return True if placement describes a legal block arrangement.

        Raises ValueError for invalid block IDs, shared supports, or cycles.
        """

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
    def _set_BlockState(placement, block_id):
        on = int(placement[block_id - 1])
        return BlockState(
            id=block_id,
            on=on,
            on_table=(on == 0),
            clear=(block_id not in placement),
        )


    def legal_moves(self) -> List[Move]:
        """Return legal moves without changing this world."""
        moves = []
        clear_blocks = [state.id for state in self.states if state.clear]

        for moving in clear_blocks:
            current_destination = int(self.placement[moving - 1])
            for destination in [0, *clear_blocks]:
                if destination == moving or destination == current_destination:
                    continue

                candidate = self.placement.copy()
                candidate[moving - 1] = destination
                try:
                    self._check_if_placement_is_legal(candidate)
                except ValueError:
                    continue

                moves.append(Move(moving=moving, destination=destination))

        return moves

    def update(self, move: Move) -> None:
        """Apply a move and refresh the affected block states."""

        #Check if move is leagl
        #TODO Check if asserst are correct and enough
        assert self.states[move.moving - 1].clear, "Block cannot be moved"
        assert move.destination == 0 or self.states[move.destination - 1].clear, "Destination block is not cleared"
        assert move.destination != move.moving, "Block cannot be moved onto itself"


        # Update Placement
        new_placement = self.placement.copy()
        new_placement[move.moving - 1] = move.destination

        assert self._check_if_placement_is_legal(new_placement), "This Placment is not legal, an Illegal Move was commited!!"
        self.placement= new_placement

        # Update states
        self.states = [
            self._set_BlockState(self.placement, block_id)
            for block_id in range(1, len(self.placement) + 1)
        ]

    def __init__(self, placement):
        placement = np.asarray(placement, dtype=np.int32)
        self._check_if_placement_is_legal(placement)
        self.placement = placement.copy()
        self.states = [
            self._set_BlockState(self.placement, block_id)
            for block_id in range(1, len(placement) + 1)
        ]
