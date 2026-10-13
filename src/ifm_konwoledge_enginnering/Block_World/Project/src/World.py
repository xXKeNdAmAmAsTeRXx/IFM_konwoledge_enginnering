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

    # TODO: Implement legal_moves() as a separate method. Return all valid moves
    #       without mutating this World: choose only clear source blocks and
    #       destinations that are either the table (0) or a different clear
    #       block. Exclude no-op moves and candidate placements that are illegal.
    def update(self, move: Move) -> None:
        """Apply a move and refresh the affected block states."""

        # TODO: Keep move validation explicit and user-readable: validate IDs
        #       before indexing states, and raise ValueError rather than relying on
        #       assert statements that Python can disable.
        # TODO: Preserve atomic updates: construct and validate the candidate
        #       placement first, then commit it and rebuild every BlockState so
        #       the moving block, its former support, and its new support all have
        #       correct clear/on/on_table values. Destination 0 is the table and
        #       must never be indexed as a block.
        # TODO: Add tests for legal moves to the table and onto another clear
        #       block, blocked sources/destinations, invalid IDs, self-moves, and
        #       confirming rejected moves leave placement and states unchanged.

        #Check if move is leagl
        assert self.states[move.moving - 1].clear, "Block cannot be moved"
        assert move.destination == 0 or self.states[move.destination - 1].clear, "Destination block is not cleared"

        # Update Placement
        new_placement = self.placement.copy()
        new_placement[move.moving - 1] = move.destination
        assert self._check_if_placement_is_legal(new_placement), "This Move is not legal"

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
